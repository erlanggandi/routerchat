import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_fastapi_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        data = root_resp.json()
        assert data["status"] == "running"
        assert data["app"] == "AI MikroTik Service API"
        assert data["docs"] == "/docs"
