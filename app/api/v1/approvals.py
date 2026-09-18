import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import get_db_session
from app.database import crud
from app.database.models import ActionApproval
from app.mikrotik.manager import router_manager
from app.schemas.api_schemas import ApprovalActionSchema
from app.utils.telegram_notifier import telegram_notifier

router = APIRouter(prefix="/approvals", tags=["Approval Engine"])


@router.get("")
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db_session),
):
    """List all pending configuration approval requests."""
    stmt = select(ActionApproval).where(ActionApproval.status == "PENDING").order_by(ActionApproval.created_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "router_id": a.router_id,
            "command_type": a.command_type,
            "description": a.description,
            "payload": json.loads(a.payload),
            "status": a.status,
            "created_at": a.created_at,
            "expires_at": a.expires_at,
        }
        for a in items
    ]


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    payload: ApprovalActionSchema,
    db: AsyncSession = Depends(get_db_session),
):
    """Approve and execute proposed RouterOS configuration."""
    approval = await crud.get_action_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Approval request already has status: {approval.status}",
        )

    now_utc = datetime.now(timezone.utc)
    expires_at = approval.expires_at if approval.expires_at.tzinfo else approval.expires_at.replace(tzinfo=timezone.utc)
    if now_utc > expires_at:
        await crud.update_action_approval_status(db, approval_id, "EXPIRED")
        raise HTTPException(status_code=400, detail="Approval request has expired.")

    router_item = await crud.get_router_by_id(db, approval.router_id)
    if not router_item:
        raise HTTPException(status_code=404, detail="Target router not found.")

    try:
        data = json.loads(approval.payload)
        path_parts = data.get("path_parts", [])
        command_type = data.get("command_type", "")
        params = data.get("parameters", {})

        service = router_manager.get_service_for_router(router_item)
        exec_result = await service.execute_raw_command(path_parts, command_type, **params)
        result_str = str(exec_result) if exec_result is not None else "Success"

        await crud.update_action_approval_status(db, approval_id, "APPROVED", output=result_str)
        await crud.add_audit_log(
            db,
            user_id=payload.user_id,
            action_type="CONFIG_EXECUTE",
            summary=f"Disetujui via API oleh user {payload.user_id} pada router '{router_item.name}'",
            details=f"Command: {command_type} {'/'.join(path_parts)}\nParams: {json.dumps(params)}\nResult: {result_str}",
            router_id=router_item.id,
        )

        # Notify Telegram group
        await telegram_notifier.send_message(
            text=f"✅ **[API Approved]** Perintah pada router `{router_item.name}` berhasil dieksekusi!\n"
                 f"Deskripsi: {approval.description}\n"
                 f"Output: `{result_str}`"
        )

        return {
            "status": "APPROVED",
            "approval_id": approval_id,
            "router_name": router_item.name,
            "result": result_str,
        }
    except Exception as exc:
        err_msg = str(exc)
        await crud.update_action_approval_status(db, approval_id, "FAILED", output=err_msg)
        await crud.add_audit_log(
            db,
            user_id=payload.user_id,
            action_type="ERROR",
            summary=f"Gagal eksekusi konfigurasi pada '{router_item.name}'",
            details=err_msg,
            router_id=router_item.id,
        )
        raise HTTPException(status_code=500, detail=f"Execution error on router: {err_msg}")


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    payload: ApprovalActionSchema,
    db: AsyncSession = Depends(get_db_session),
):
    """Reject proposed RouterOS configuration."""
    approval = await crud.get_action_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Approval request already has status: {approval.status}",
        )

    await crud.update_action_approval_status(db, approval_id, "REJECTED")
    await crud.add_audit_log(
        db,
        user_id=payload.user_id,
        action_type="REJECT",
        summary=f"Ditolak via API oleh user {payload.user_id}",
        details=f"Alasan: {payload.reason or 'Tidak ada'}",
        router_id=approval.router_id,
    )

    # Notify Telegram group
    await telegram_notifier.send_message(
        text=f"❌ **[API Rejected]** Perubahan konfigurasi dibatalkan.\nDeskripsi: {approval.description}"
    )

    return {
        "status": "REJECTED",
        "approval_id": approval_id,
    }
