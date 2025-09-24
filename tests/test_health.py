"""Health endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    """Test health endpoint returns 200."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_readiness_endpoint():
    """Test readiness endpoint returns 200."""
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
