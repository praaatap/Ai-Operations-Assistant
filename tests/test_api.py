from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_read_main():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "AI Operations Assistant"

def test_health_check_structure():
    """Test health check endpoint returns correct structure"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "agents" in data
    assert "planner" in data["agents"]

def test_openapi_docs_accessible():
    """Test that OpenAPI docs are generated and accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Operations Assistant"
