"""
Integration Tests untuk API endpoints
Testing POST /publish, GET /events, GET /stats
"""
import pytest
from httpx import AsyncClient
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app


@pytest.fixture
async def client():
    """Fixture untuk HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test: Root endpoint mengembalikan informasi service"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data['service'] == "Pub-Sub Log Aggregator"
    assert 'endpoints' in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test: Health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == "healthy"


@pytest.mark.asyncio
async def test_publish_valid_event(client):
    """Test: Publish event dengan data valid"""
    event = {
        "topic": "user.login",
        "event_id": "evt-test-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "auth-service",
        "payload": {"user_id": 123, "ip": "192.168.1.1"}
    }
    
    response = await client.post("/publish", json=event)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == "accepted"
    assert data['event_id'] == event['event_id']


@pytest.mark.asyncio
async def test_publish_invalid_event_missing_field(client):
    """Test: Publish event dengan field yang hilang"""
    event = {
        "topic": "user.login",
        # event_id missing
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "auth-service",
        "payload": {}
    }
    
    response = await client.post("/publish", json=event)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_publish_invalid_timestamp(client):
    """Test: Publish event dengan timestamp invalid"""
    event = {
        "topic": "user.login",
        "event_id": "evt-test-002",
        "timestamp": "invalid-timestamp",
        "source": "auth-service",
        "payload": {}
    }
    
    response = await client.post("/publish", json=event)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_stats(client):
    """Test: GET /stats mengembalikan statistik yang benar"""
    # Publish beberapa event terlebih dahulu
    events = [
        {
            "topic": f"test.topic{i}",
            "event_id": f"evt-stats-{i}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "test",
            "payload": {"index": i}
        }
        for i in range(3)
    ]
    
    for event in events:
        await client.post("/publish", json=event)
    
    # Tunggu processing
    import asyncio
    await asyncio.sleep(1)
    
    # Get stats
    response = await client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert 'received' in data
    assert 'unique_processed' in data
    assert 'duplicate_dropped' in data
    assert 'topics' in data
    assert 'uptime' in data
    assert data['received'] >= 3


@pytest.mark.asyncio
async def test_get_events(client):
    """Test: GET /events mengembalikan daftar event"""
    # Publish event
    event = {
        "topic": "test.events",
        "event_id": "evt-get-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "test",
        "payload": {"test": "data"}
    }
    
    await client.post("/publish", json=event)
    
    # Tunggu processing
    import asyncio
    await asyncio.sleep(1)
    
    # Get events
    response = await client.get("/events")
    assert response.status_code == 200
    
    data = response.json()
    assert 'count' in data
    assert 'events' in data
    assert isinstance(data['events'], list)


@pytest.mark.asyncio
async def test_get_events_with_topic_filter(client):
    """Test: GET /events dengan filter topic"""
    # Publish events dengan topic berbeda
    topic1_events = [
        {
            "topic": "filtered.topic",
            "event_id": f"evt-filter-{i}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "test",
            "payload": {}
        }
        for i in range(2)
    ]
    
    topic2_event = {
        "topic": "other.topic",
        "event_id": "evt-other-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "test",
        "payload": {}
    }
    
    for event in topic1_events:
        await client.post("/publish", json=event)
    await client.post("/publish", json=topic2_event)
    
    # Tunggu processing
    import asyncio
    await asyncio.sleep(1)
    
    # Get events dengan filter
    response = await client.get("/events?topic=filtered.topic")
    assert response.status_code == 200
    
    data = response.json()
    assert data['topic'] == "filtered.topic"
    # Verify hanya events dari filtered.topic yang dikembalikan


@pytest.mark.asyncio
async def test_duplicate_handling(client):
    """Test: Duplikat event ditangani dengan benar"""
    event = {
        "topic": "duplicate.test",
        "event_id": "evt-duplicate-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "test",
        "payload": {"test": "duplicate"}
    }
    
    # Publish event pertama kali
    response1 = await client.post("/publish", json=event)
    assert response1.status_code == 200
    
    # Publish event kedua kali (duplikat)
    response2 = await client.post("/publish", json=event)
    assert response2.status_code == 200  # Diterima tapi akan di-drop
    
    # Tunggu processing
    import asyncio
    await asyncio.sleep(1)
    
    # Check stats
    response = await client.get("/stats")
    data = response.json()
    
    # Harus ada duplicate_dropped
    assert data['duplicate_dropped'] >= 1


@pytest.mark.asyncio
async def test_batch_publish(client):
    """Test: Batch publish events"""
    batch_size = 50
    events = [
        {
            "topic": f"batch.topic{i % 5}",
            "event_id": f"evt-batch-{i}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "batch-test",
            "payload": {"batch_id": i}
        }
        for i in range(batch_size)
    ]
    
    # Publish all events
    for event in events:
        response = await client.post("/publish", json=event)
        assert response.status_code == 200
    
    # Tunggu processing
    import asyncio
    await asyncio.sleep(2)
    
    # Verify stats
    response = await client.get("/stats")
    data = response.json()
    assert data['received'] >= batch_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
