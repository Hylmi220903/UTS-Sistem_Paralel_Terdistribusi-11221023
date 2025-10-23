"""
Integration Tests untuk FastAPI endpoints
Menggunakan TestClient synchronous untuk menghindari masalah lifespan
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Import app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app


@pytest.fixture
def client():
    """Fixture untuk synchronous test client"""
    with TestClient(app) as client:
        yield client


class TestHealthCheck:
    """Test suite untuk health check endpoint"""
    
    def test_root_endpoint(self, client):
        """Test: Root endpoint mengembalikan informasi service"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['service'] == "Pub-Sub Log Aggregator"
        assert 'version' in data
        assert 'status' in data


# Run tests jika dijalankan langsung
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
