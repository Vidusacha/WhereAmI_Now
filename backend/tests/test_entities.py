import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_entities_works(client: AsyncClient):
    response = await client.get("/api/entities/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_and_get_entity(client: AsyncClient):
    payload = {
        "id": "likud_test",
        "name_en": "Likud Test",
        "name_ru": "?????",
        "name_he": "?????",
        "entity_type_id": "party"
    }
    response = await client.post("/api/entities/", json=payload)
    assert response.status_code == 200

    response2 = await client.get("/api/entities/")
    assert len([e for e in response2.json() if e["id"] == "likud_test"]) == 1

@pytest.mark.asyncio
async def test_get_discovery_log_not_found(client: AsyncClient):
    response = await client.get("/api/entities/likud_test/discovery_log")
    assert response.status_code == 200
    assert "No discovery log found" in response.json()["log"]

