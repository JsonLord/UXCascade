import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_api_routing_and_404():
    # Verify API 404 returns JSON detail error and not HTML
    response = client.get("/api/nonexistent_endpoint_for_test")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_spa_fallback_route():
    # When FRONTEND_DIST is present, SPA deep routes fallback to HTML or return 404 if no dist
    response = client.get("/projects/123")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "text/html" in response.headers["content-type"]
