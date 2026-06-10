import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(client: AsyncClient) -> None:
    root = await client.get("/health")
    assert root.status_code == 200
    assert root.json()["ok"] is True

    legacy = await client.get("/api/v1/legacy/health")
    assert legacy.status_code == 200
    assert legacy.json()["ok"] is True
    assert legacy.json()["legacy"] is True

    v2 = await client.get("/api/v2/health")
    assert v2.status_code == 200
    assert v2.json()["ok"] is True

