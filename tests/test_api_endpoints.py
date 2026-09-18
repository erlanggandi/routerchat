import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.models import Base
from app.database.connection import engine, init_db


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_routers_api_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Router
        payload = {
            "name": "mikrotik-cabang-1",
            "host": "192.168.10.1",
            "port": 8728,
            "username": "admin",
            "password": "Password123!",
            "use_ssl": False,
            "description": "Router Cabang 1",
        }
        res = await client.post("/api/v1/routers", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "mikrotik-cabang-1"
        router_id = data["id"]

        # 2. List Routers
        res_list = await client.get("/api/v1/routers")
        assert res_list.status_code == 200
        routers = res_list.json()
        assert len(routers) == 1
        assert routers[0]["id"] == router_id

        # 3. Get Detail
        res_detail = await client.get(f"/api/v1/routers/{router_id}")
        assert res_detail.status_code == 200
        assert res_detail.json()["host"] == "192.168.10.1"

        # 4. Delete Router
        res_del = await client.delete(f"/api/v1/routers/{router_id}")
        assert res_del.status_code == 204

        # 5. Verify Deleted
        res_check = await client.get(f"/api/v1/routers/{router_id}")
        assert res_check.status_code == 404


@pytest.mark.asyncio
async def test_approvals_api_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a router first
        router_res = await client.post("/api/v1/routers", json={
            "name": "core-router",
            "host": "10.0.0.1",
            "port": 8728,
            "username": "admin",
            "password": "secret",
        })
        router_id = router_res.json()["id"]

        # Directly test empty approvals list
        appr_list = await client.get("/api/v1/approvals")
        assert appr_list.status_code == 200
        assert isinstance(appr_list.json(), list)
