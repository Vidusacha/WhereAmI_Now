import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_empty_axes(client: AsyncClient):
    response = await client.get("/api/axes/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_axis_manual(client: AsyncClient):
    payload = {
        "id": "economy",
        "name_en": "Economy",
        "name_ru": "?????????",
        "name_he": "?????",
        "description": "Economic policy"
    }
    response = await client.post("/api/axes/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "economy"

    # Fetch to verify
    response2 = await client.get("/api/axes/")
    assert len(response2.json()) == 1

@pytest.mark.asyncio
async def test_auto_translate_axis(client: AsyncClient, mocker):
    # Mock the ai_service to return a fixed translation
    mock_translate = mocker.patch("api.routes.axes.translate_axis_name", return_value={
        "name_en": "Security",
        "name_ru": "????????????",
        "name_he": "??????"
    })

    response = await client.post("/api/axes/auto_translate?name=Security")
    assert response.status_code == 200
    data = response.json()
    assert data["name_en"] == "Security"
    assert data["status"] == "pending_ai_proposal"
    mock_translate.assert_called_once_with("Security")

