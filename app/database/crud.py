from datetime import datetime, timedelta, timezone
from typing import List, Optional
import json
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Router, UserSession, ActionApproval, AuditLog
from app.utils.security import encrypt_secret, decrypt_secret
from config.settings import settings


# ---------------- Router Operations ----------------

async def get_all_routers(db: AsyncSession, active_only: bool = True) -> List[Router]:
    stmt = select(Router)
    if active_only:
        stmt = stmt.where(Router.is_active == True)
    result = await db.execute(stmt.order_by(Router.id))
    return list(result.scalars().all())


async def get_router_by_id(db: AsyncSession, router_id: int) -> Optional[Router]:
    stmt = select(Router).where(Router.id == router_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_router_by_name(db: AsyncSession, name: str) -> Optional[Router]:
    stmt = select(Router).where(Router.name == name.strip())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_router(
    db: AsyncSession,
    name: str,
    host: str,
    username: str,
    password: str,
    port: int = 8728,
    use_ssl: bool = False,
    description: Optional[str] = None,
) -> Router:
    password_encrypted = encrypt_secret(password)
    router = Router(
        name=name.strip(),
        host=host.strip(),
        port=port,
        username=username.strip(),
        password_encrypted=password_encrypted,
        use_ssl=use_ssl,
        description=description,
        is_active=True,
    )
    db.add(router)
    await db.commit()
    await db.refresh(router)
    return router


async def delete_router(db: AsyncSession, router_id: int) -> bool:
    router = await get_router_by_id(db, router_id)
    if not router:
        return False
    await db.delete(router)
    await db.commit()
    return True


# ---------------- User Session Operations ----------------

async def get_or_create_user_session(db: AsyncSession, user_id: int) -> UserSession:
    stmt = select(UserSession).where(UserSession.user_id == user_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        session = UserSession(user_id=user_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def set_user_active_router(db: AsyncSession, user_id: int, router_id: Optional[int]) -> UserSession:
    session = await get_or_create_user_session(db, user_id)
    session.active_router_id = router_id
    session.last_active = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def get_active_router_for_user(db: AsyncSession, user_id: int) -> Optional[Router]:
    session = await get_or_create_user_session(db, user_id)
    if session.active_router_id:
        return await get_router_by_id(db, session.active_router_id)

    # Fallback to the first active router if only one is configured
    routers = await get_all_routers(db, active_only=True)
    if len(routers) == 1:
        session.active_router_id = routers[0].id
        await db.commit()
        return routers[0]

    return None


# ---------------- Approval Operations ----------------

async def create_action_approval(
    db: AsyncSession,
    user_id: int,
    router_id: int,
    command_type: str,
    description: str,
    payload: dict,
    timeout_minutes: int = settings.APPROVAL_TIMEOUT_MINUTES,
) -> ActionApproval:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
    approval = ActionApproval(
        user_id=user_id,
        router_id=router_id,
        command_type=command_type,
        description=description,
        payload=json.dumps(payload),
        status="PENDING",
        expires_at=expires_at,
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


async def get_action_approval(db: AsyncSession, approval_id: str) -> Optional[ActionApproval]:
    stmt = select(ActionApproval).where(ActionApproval.id == approval_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_action_approval_status(
    db: AsyncSession,
    approval_id: str,
    status: str,
    output: Optional[str] = None,
) -> Optional[ActionApproval]:
    approval = await get_action_approval(db, approval_id)
    if not approval:
        return None

    approval.status = status
    if output is not None:
        approval.execution_output = output
    if status in ["APPROVED", "REJECTED", "FAILED"]:
        approval.executed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(approval)
    return approval


# ---------------- Audit Log Operations ----------------

async def add_audit_log(
    db: AsyncSession,
    user_id: int,
    action_type: str,
    summary: str,
    details: Optional[str] = None,
    router_id: Optional[int] = None,
) -> AuditLog:
    log_entry = AuditLog(
        user_id=user_id,
        router_id=router_id,
        action_type=action_type,
        summary=summary,
        details=details,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    await db.commit()
    return log_entry


async def get_recent_audit_logs(
    db: AsyncSession,
    limit: int = 15,
    user_id: Optional[int] = None,
    router_id: Optional[int] = None,
) -> List[AuditLog]:
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if router_id:
        stmt = stmt.where(AuditLog.router_id == router_id)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def prune_old_read_logs(db: AsyncSession, retention_days: int = settings.METRICS_RETENTION_DAYS):
    """Delete QUERY logs older than retention days while preserving all CONFIG_EXECUTE & APPROVAL logs."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    stmt = delete(AuditLog).where(
        AuditLog.action_type == "QUERY",
        AuditLog.created_at < cutoff_date,
    )
    await db.execute(stmt)
    await db.commit()
