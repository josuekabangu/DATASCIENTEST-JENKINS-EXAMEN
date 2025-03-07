import pytest
from fastapi.testclient import TestClient
from app.main import app, database
from app.api.models import CastIn
from unittest.mock import patch, AsyncMock

# Fixture pour le client de test
@pytest.fixture
def client():
    """Retourne un TestClient pour interagir avec l'application FastAPI."""
    return TestClient(app)

# Fixture pour mocker la connexion à la base de données
@pytest.fixture(autouse=True)
async def mock_database():
    """Mocke les événements de connexion/déconnexion à la DB."""
    with patch("app.api.db.database.connect", new_callable=AsyncMock):
        with patch("app.api.db.database.disconnect", new_callable=AsyncMock):
            yield

# Marquer tous les tests comme asynchrones
pytestmark = pytest.mark.asyncio

# Tests pour POST /api/v1/casts/
async def test_create_cast_success(client):
    """Teste la création réussie d'un cast."""
    payload = {"name": "John Doe", "nationality": "USA"}
    with patch("app.api.db_manager.add_cast", new_callable=AsyncMock, return_value=1):
        response = client.post("/api/v1/casts/", json=payload)
        assert response.status_code == 201
        assert response.json() == {"id": 1, "name": "John Doe", "nationality": "USA"}

async def test_create_cast_missing_name(client):
    """Teste la création avec un champ 'name' manquant."""
    payload = {"nationality": "USA"}
    response = client.post("/api/v1/casts/", json=payload)
    assert response.status_code == 422
    assert "name" in response.json()["detail"][0]["loc"]

async def test_create_cast_name_too_long(client):
    """Teste la création avec un nom trop long."""
    payload = {"name": "A" * 51, "nationality": "USA"}
    with patch("app.api.db_manager.add_cast", new_callable=AsyncMock, return_value=1):
        response = client.post("/api/v1/casts/", json=payload)
        assert response.status_code == 201

# Tests pour GET /api/v1/casts/{id}/
async def test_get_cast_success(client):
    """Teste la récupération réussie d'un cast existant."""
    cast_data = {"id": 1, "name": "John Doe", "nationality": "USA"}
    with patch("app.api.db_manager.get_cast", new_callable=AsyncMock, return_value=cast_data):
        response = client.get("/api/v1/casts/1/")
        assert response.status_code == 200
        assert response.json() == cast_data

async def test_get_cast_not_found(client):
    """Teste la récupération d'un cast inexistant."""
    with patch("app.api.db_manager.get_cast", new_callable=AsyncMock, return_value=None):
        response = client.get("/api/v1/casts/999/")
        assert response.status_code == 404
        assert response.json() == {"detail": "Cast not found"}

async def test_get_cast_invalid_id(client):
    """Teste la récupération avec un ID invalide (non numérique)."""
    response = client.get("/api/v1/casts/invalid/")
    assert response.status_code == 422
    assert "Input should be a valid integer" in response.json()["detail"][0]["msg"]  # Message corrigé