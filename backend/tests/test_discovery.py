import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_discover_discourse_not_found(client: AsyncClient):
    response = await client.post("/api/discovery/discourse/nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_discover_discourse_success(client: AsyncClient, mocker):
    # First create an entity and an axis
    await client.post("/api/entities/", json={"id": "test_entity", "name_en": "Test Entity", "name_ru": "", "name_he": "", "entity_type_id": "party"})
    await client.post("/api/axes/", json={"id": "test_axis", "name_en": "Test Axis", "name_ru": "", "name_he": "", "description": ""})
    await client.put("/api/axes/test_axis/approve")

    # Mock the discovery dependencies
    mocker.patch("api.routes.discovery.generate_search_queries", return_value=["Query 1"])
    mocker.patch("api.routes.discovery.search_duckduckgo", return_value=["http://example.com"])
    
    mock_file = "/app/tests/test_mock_file.md"
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write("Some scraped text")

    mocker.patch("api.routes.discovery.scrape_url", return_value=mock_file)
    mocker.patch("api.routes.discovery.score_entity_on_axis", return_value={"score": 5, "confidence": 0.9, "justification_en": "Because", "justification_ru": "", "justification_he": ""})

    response = await client.post("/api/discovery/discourse/test_entity")
    assert response.status_code == 200
    data = response.json()
    assert data["entity_id"] == "test_entity"
    assert data["status"] == "Success"
    assert len(data["scores"]) == 1
    assert data["scores"][0]["axis_id"] == "test_axis"
    assert data["scores"][0]["score"] == 5

    # Verify log was saved
    log_response = await client.get("/api/entities/test_entity/discovery_log")
    assert log_response.status_code == 200
    assert "Discovery process completed" in log_response.json()["log"]

@pytest.mark.asyncio
async def test_discover_new_axes(client: AsyncClient, mocker):
    mocker.patch("api.routes.discovery.search_duckduckgo", return_value=["http://example.com/news"])
    
    mock_file = "/app/tests/test_mock_news.md"
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write("Some news text about economy")

    mocker.patch("api.routes.discovery.scrape_url", return_value=mock_file)
    mocker.patch("api.routes.discovery.discover_axes_from_texts", return_value=[
        {"name_en": "New Economic Axis", "name_ru": "", "name_he": "", "description": "About taxes"}
    ])

    response = await client.post("/api/discovery/axes")
    data = response.json()
    assert response.status_code == 200, f"Error: {data}"
    assert data["status"] == "Success", f"Error: {data}"
    assert len(data["discovered_axes"]) == 1
    assert data["discovered_axes"][0]["name_en"] == "New Economic Axis"


