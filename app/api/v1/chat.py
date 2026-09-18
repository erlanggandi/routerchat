import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.database import crud
from app.mikrotik.manager import router_manager
from app.ai.agent import ai_agent
from app.schemas.api_schemas import ChatRequestSchema, ChatResponseSchema
from app.utils.telegram_notifier import telegram_notifier

router = APIRouter(prefix="/chat", tags=["AI Chat / Agent"])


@router.post("", response_model=ChatResponseSchema)
async def chat_with_agent(
    payload: ChatRequestSchema,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Direct AI interaction endpoint for external bots (e.g. Hermes).
    Processes user queries, executes read tools on MikroTik, and creates approval proposals if mutating commands are needed.
    """
    target_router = None
    if payload.router_id:
        target_router = await crud.get_router_by_id(db, payload.router_id)
    else:
        target_router = await crud.get_active_router_for_user(db, payload.user_id)

    if not target_router:
        all_routers = await crud.get_all_routers(db, active_only=True)
        if all_routers:
            target_router = all_routers[0]
        else:
            raise HTTPException(
                status_code=400,
                detail="Belum ada router MikroTik yang terdaftar. Daftarkan router melalui POST /api/v1/routers.",
            )

    service = router_manager.get_service_for_router(target_router)

    reply_text, pending_proposals = await ai_agent.run(
        user_message=payload.message,
        service=service,
        db=db,
        user_id=payload.user_id,
        router=target_router,
    )

    # Optionally push to Telegram group if requested
    if payload.send_to_telegram:
        await telegram_notifier.send_message(
            text=f"🤖 **[Hermes -> MikroTik AI]**\n\n{reply_text}"
        )
        for prop in pending_proposals:
            proposal_msg = (
                f"🛡️ **Persetujuan Diperlukan (Approval Engine)**\n\n"
                f"• **ID:** `{prop['approval_id']}`\n"
                f"• **Router:** `{prop['router_name']}`\n"
                f"• **Tindakan:** `{prop['command_type']}` pada `/{'/'.join(prop['path_parts'])}`\n"
                f"• **Keterangan:** {prop['description']}\n\n"
                f"Gunakan API `POST /api/v1/approvals/{prop['approval_id']}/approve` untuk mengeksekusi."
            )
            await telegram_notifier.send_message(text=proposal_msg)

    return ChatResponseSchema(
        reply=reply_text,
        router_name=target_router.name,
        pending_approvals=pending_proposals,
    )
