import pytest
import uuid
from datetime import datetime, timezone
import io
from app.utils.security import encrypt_secret, decrypt_secret
from app.database import crud
from app.database.models import Base
from app.database.connection import engine, AsyncSessionLocal, init_db
from app.utils.grapher import generate_resource_chart, generate_traffic_chart
from app.ai.factory import get_llm


@pytest.fixture(autouse=True)
async def clean_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_security_encryption():
    raw_pass = "MySuperSecretPassword123!"
    encrypted = encrypt_secret(raw_pass)
    assert encrypted != raw_pass
    decrypted = decrypt_secret(encrypted)
    assert decrypted == raw_pass


@pytest.mark.asyncio
async def test_database_router_and_session_crud():
    async with AsyncSessionLocal() as db:
        # Create router
        router = await crud.create_router(
            db=db,
            name="test-router-hq",
            host="192.168.1.1",
            username="admin",
            password="secretpassword",
            port=8728,
            use_ssl=False,
            description="HQ Core Router",
        )
        assert router.id is not None
        assert router.name == "test-router-hq"
        assert decrypt_secret(router.password_encrypted) == "secretpassword"

        # User session test
        user_id = 999111888
        session = await crud.set_user_active_router(db, user_id=user_id, router_id=router.id)
        assert session.active_router_id == router.id

        # Verify active router resolution
        active_router = await crud.get_active_router_for_user(db, user_id)
        assert active_router is not None
        assert active_router.id == router.id
        assert active_router.name == "test-router-hq"


@pytest.mark.asyncio
async def test_approval_and_audit_workflow():
    async with AsyncSessionLocal() as db:
        # Create a router for approval
        router = await crud.create_router(
            db=db,
            name="branch-router-1",
            host="192.168.2.1",
            username="admin",
            password="pass",
        )

        user_id = 123456
        # Create approval
        payload = {
            "path_parts": ["ip", "firewall", "filter"],
            "command_type": "add",
            "parameters": {"chain": "forward", "src_address": "10.0.0.99", "action": "drop"},
        }
        approval = await crud.create_action_approval(
            db=db,
            user_id=user_id,
            router_id=router.id,
            command_type="add",
            description="Drop IP 10.0.0.99",
            payload=payload,
            timeout_minutes=5,
        )

        assert approval.status == "PENDING"
        now_utc = datetime.now(timezone.utc)
        expires_at = approval.expires_at if approval.expires_at.tzinfo else approval.expires_at.replace(tzinfo=timezone.utc)
        assert expires_at > now_utc

        # Update approval status to APPROVED
        updated = await crud.update_action_approval_status(
            db=db,
            approval_id=approval.id,
            status="APPROVED",
            output="Rule added with id *1A",
        )
        assert updated.status == "APPROVED"
        assert updated.execution_output == "Rule added with id *1A"
        assert updated.executed_at is not None

        # Add Audit log
        log_entry = await crud.add_audit_log(
            db=db,
            user_id=user_id,
            action_type="CONFIG_EXECUTE",
            summary="Approved firewall rule addition",
            router_id=router.id,
        )
        assert log_entry.id is not None

        recent_logs = await crud.get_recent_audit_logs(db, limit=5)
        assert len(recent_logs) > 0


def test_visual_charts_generation():
    # Test Resource Chart
    buf_res = generate_resource_chart(
        router_name="Router-Test",
        cpu_load=45,
        mem_usage_pct=60.5,
        used_mem_mb=128.0,
        free_mem_mb=83.5,
    )
    assert isinstance(buf_res, io.BytesIO)
    assert buf_res.getbuffer().nbytes > 1000

    # Test Traffic Chart
    buf_traffic = generate_traffic_chart(
        interface_name="ether1",
        rx_mbps=12.5,
        tx_mbps=4.2,
        rx_pps=1200,
        tx_pps=650,
    )
    assert isinstance(buf_traffic, io.BytesIO)
    assert buf_traffic.getbuffer().nbytes > 1000


def test_universal_llm_factory():
    llm = get_llm(
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-test-mock-key",
        temperature=0.1,
    )
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.1
    # Check that OpenAI-compatible client has the expected base_url
    assert "api.openai.com/v1" in str(llm.openai_api_base or "")
