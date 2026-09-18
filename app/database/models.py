from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class Router(Base):
    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=8728, nullable=False)
    username = Column(String(64), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    use_ssl = Column(Boolean, default=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    approvals = relationship("ActionApproval", back_populates="router")
    audit_logs = relationship("AuditLog", back_populates="router")


class UserSession(Base):
    __tablename__ = "user_sessions"

    user_id = Column(BigInteger, primary_key=True, index=True)
    active_router_id = Column(Integer, ForeignKey("routers.id", ondelete="SET NULL"), nullable=True)
    last_active = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    active_router = relationship("Router", foreign_keys=[active_router_id])


class ActionApproval(Base):
    __tablename__ = "action_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(BigInteger, nullable=False, index=True)
    router_id = Column(Integer, ForeignKey("routers.id", ondelete="CASCADE"), nullable=False)
    command_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    payload = Column(Text, nullable=False)  # JSON representation of command details
    status = Column(String(20), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, EXPIRED, FAILED
    execution_output = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    router = relationship("Router", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    router_id = Column(Integer, ForeignKey("routers.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(32), nullable=False, index=True)  # QUERY, APPROVAL_REQUEST, CONFIG_EXECUTE, REJECT, ERROR
    summary = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    router = relationship("Router", back_populates="audit_logs")
