"""
Integration Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestIndexingEndpoints:
    """Test indexing API endpoints."""
    
    def test_start_indexing(self, client):
        """Test POST /index/start."""
        payload = {
            "repo_path": "/fake/path",
            "force_reindex": False
        }
        
        response = client.post("/index/start", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"
    
    def test_get_stats(self, client):
        """Test GET /index/stats."""
        response = client.get("/index/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_files" in data


class TestSearchEndpoints:
    """Test search API endpoints."""
    
    def test_semantic_search(self, client):
        """Test POST /search/semantic."""
        payload = {
            "query": "authentication functions",
            "top_k": 10
        }
        
        response = client.post("/search/semantic", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data


class TestChatEndpoints:
    """Test chat API endpoints."""
    
    def test_chat_completion(self, client):
        """Test POST /chat/completion."""
        payload = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "stream": False
        }
        
        response = client.post("/chat/completion", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestDebugEndpoints:
    """Test debug API endpoints."""
    
    def test_debug_error(self, client):
        """Test POST /debug/error."""
        payload = {
            "error": {
                "error_type": "TypeError",
                "error_message": "Cannot read property",
                "file_path": "test.py",
                "line_number": 42
            },
            "auto_fix": False
        }
        
        response = client.post("/debug/error", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
    
    def test_get_hotspots(self, client):
        """Test GET /debug/hotspots."""
        response = client.get("/debug/hotspots")
        
        assert response.status_code == 200
        data = response.json()
        assert "hotspots" in data


class TestGraphEndpoints:
    """Test graph API endpoints."""
    
    def test_graph_overview(self, client):
        """Test GET /graph/overview."""
        response = client.get("/graph/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "relationships" in data
