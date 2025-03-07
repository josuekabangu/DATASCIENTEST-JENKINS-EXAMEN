import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.models import MovieIn, MovieOut
from unittest.mock import patch, AsyncMock, Mock
import sys
import importlib

# Fixture pour mocker is_cast_present et recharger movies.py
@pytest.fixture(scope="function")
def mock_is_cast_present():
    """Mocke is_cast_present et recharge movies.py pour refléter le mock."""
    # Importer dynamiquement le module service
    service_module = sys.modules["app.api.service"]
    original_is_cast_present = service_module.is_cast_present
    # Remplacer par un mock
    service_module.is_cast_present = Mock(side_effect=lambda cast_id: cast_id in [1, 2])
    # Recharger movies.py pour qu'il utilise le mock
    movies_module = importlib.reload(sys.modules["app.api.movies"])
    yield service_module.is_cast_present
    # Restaurer la fonction originale après le test
    service_module.is_cast_present = original_is_cast_present
    # Recharger movies.py à nouveau pour restaurer l'état original
    importlib.reload(movies_module)

# Fixture pour le client de test
@pytest.fixture
def client(mock_is_cast_present):
    """Retourne un TestClient avec le mock déjà en place."""
    return TestClient(app, base_url="http://movie_service:8001")

# Fixture pour mocker la connexion à la base de données
@pytest.fixture(autouse=True)
async def mock_database():
    """Mocke les événements de connexion/déconnexion à la DB."""
    with patch("app.api.db.database.connect", new_callable=AsyncMock):
        with patch("app.api.db.database.disconnect", new_callable=AsyncMock):
            yield

# Marquer tous les tests comme asynchrones
pytestmark = pytest.mark.asyncio

# Test pour POST /api/v1/movies/
async def test_create_movie_success(client, mock_is_cast_present):
    payload = {
        "name": "Inception",
        "plot": "A thief enters dreams.",
        "genres": ["Sci-Fi", "Thriller"],
        "casts_id": [1, 2]
    }
    
    with patch("app.api.db_manager.add_movie", new_callable=AsyncMock, return_value=1) as mock_add_movie:
        response = client.post("/api/v1/movies/", json=payload)
        print("Mock is_cast_present called:", mock_is_cast_present.called)
        print("Mock is_cast_present call count:", mock_is_cast_present.call_count)
        print("Mock is_cast_present calls:", mock_is_cast_present.mock_calls)
        print("Mock add_movie called:", mock_add_movie.called)
        print("Response Status:", response.status_code)
        print("Response JSON:", response.json())
        assert response.status_code == 201

async def test_create_movie_missing_field(client, mock_is_cast_present):
    """Teste la création avec un champ manquant."""
    payload = {"plot": "A thief enters dreams.", "genres": ["Sci-Fi"], "casts_id": [1]}
    response = client.post("/api/v1/movies/", json=payload)
    assert response.status_code == 422
    assert "name" in response.json()["detail"][0]["loc"]

async def test_create_movie_cast_not_found(client):
    """Teste la création avec un cast inexistant."""
    payload = {
        "name": "Inception",
        "plot": "A thief enters dreams.",
        "genres": ["Sci-Fi", "Thriller"],
        "casts_id": [999]  # Cast ID qui n'existe pas
    }
    with patch("app.api.service.is_cast_present", return_value=False):
        response = client.post("/api/v1/movies/", json=payload)
        assert response.status_code == 404
        assert response.json() == {"detail": "Cast with given id:999 not found"}

# Test pour GET /api/v1/movies/
async def test_get_all_movies_success(client):
    """Teste la récupération de tous les films."""
    movies_data = [
        {"id": 1, "name": "Inception", "plot": "A thief enters dreams.", "genres": ["Sci-Fi"], "casts_id": [1]},
        {"id": 2, "name": "Matrix", "plot": "A hacker discovers reality.", "genres": ["Sci-Fi"], "casts_id": [2]}
    ]
    with patch("app.api.db_manager.get_all_movies", new_callable=AsyncMock, return_value=movies_data):
        response = client.get("/api/v1/movies/")
        assert response.status_code == 200
        assert response.json() == movies_data

# Test pour GET /api/v1/movies/{id}/
async def test_get_movie_success(client):
    """Teste la récupération réussie d'un film existant."""
    movie_data = {"id": 1, "name": "Inception", "plot": "A thief enters dreams.", "genres": ["Sci-Fi"], "casts_id": [1]}
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value=movie_data):
        response = client.get("/api/v1/movies/1/")
        assert response.status_code == 200
        assert response.json() == movie_data

async def test_get_movie_not_found(client):
    """Teste la récupération d'un film inexistant."""
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value=None):
        response = client.get("/api/v1/movies/999/")
        assert response.status_code == 404
        assert response.json() == {"detail": "Movie not found"}

async def test_get_movie_invalid_id(client):
    """Teste la récupération avec un ID invalide."""
    response = client.get("/api/v1/movies/invalid/")
    assert response.status_code == 422
    assert "Input should be a valid integer" in response.json()["detail"][0]["msg"]

# Test pour PUT /api/v1/movies/{id}/
async def test_update_movie_success(client, mock_is_cast_present):
    """Teste la mise à jour réussie d'un film."""
    existing_movie = {"id": 1, "name": "Inception", "plot": "Old plot", "genres": ["Sci-Fi"], "casts_id": [1]}
    update_payload = {"name": "Inception Updated", "plot": "New plot"}
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value=existing_movie):
        with patch("app.api.db_manager.update_movie", new_callable=AsyncMock, return_value=1):
            with patch("fastapi.routing.serialize_response", return_value=1):
                response = client.put("/api/v1/movies/1/", json=update_payload)
                assert response.status_code == 200
                assert response.json() == 1

async def test_update_movie_not_found(client, mock_is_cast_present):
    """Teste la mise à jour d'un film inexistant."""
    payload = {"name": "Inception Updated"}
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value=None):
        response = client.put("/api/v1/movies/999/", json=payload)  # Correction : utiliser 'payload' au lieu de 'update_payload'
        assert response.status_code == 404
        assert response.json() == {"detail": "Movie not found"}

# Test pour DELETE /api/v1/movies/{id}/
async def test_delete_movie_success(client):
    """Teste la suppression réussie d'un film."""
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value={"id": 1}):
        with patch("app.api.db_manager.delete_movie", new_callable=AsyncMock, return_value=1):
            response = client.delete("/api/v1/movies/1/")
            assert response.status_code == 200
            assert response.json() == 1

async def test_delete_movie_not_found(client):
    """Teste la suppression d'un film inexistant."""
    with patch("app.api.db_manager.get_movie", new_callable=AsyncMock, return_value=None):
        response = client.delete("/api/v1/movies/999/")
        assert response.status_code == 404
        assert response.json() == {"detail": "Movie not found"}