import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_deduplicate_entities(client: AsyncClient, mocker):
    mocker.patch("api.routes.maintenance.find_duplicate_entities", return_value=[{"primary_id": "party1", "duplicate_id": "party2"}])
    # Add two entities with same name
    await client.post("/api/entities/", json={"id": "party1", "name_en": "Duplicate Party", "name_ru": "a", "name_he": "a", "entity_type_id": "party"})
    await client.post("/api/entities/", json={"id": "party2", "name_en": "The Duplicate Party", "name_ru": "b", "name_he": "b", "entity_type_id": "party"})
    
    response = await client.post("/api/maintenance/deduplicate/entities")
    assert response.status_code == 200
    
    # Verify only 1 remains
    response2 = await client.get("/api/entities/")
    assert len([e for e in response2.json() if e["name_en"] == "Duplicate Party"]) == 1

