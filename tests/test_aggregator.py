"""
Unit Tests untuk Pub-Sub Log Aggregator
Total: 15 comprehensive tests
Mencakup: deduplication, persistence, schema validation, consumer processing
"""
import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Import komponen yang akan ditest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dedup_store import DedupStore
from src.consumer import EventConsumer
from src.models import Event


@pytest.fixture
def temp_db():
    """Fixture untuk temporary database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    try:
        import gc
        gc.collect()
        import time
        time.sleep(0.1)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        pass


@pytest.fixture
def dedup_store(temp_db):
    """Fixture untuk DedupStore"""
    store = DedupStore(temp_db)
    yield store
    store.close()


@pytest.fixture
def consumer(dedup_store):
    """Fixture untuk EventConsumer"""
    return EventConsumer(dedup_store)


@pytest.fixture
def sample_event():
    """Fixture untuk sample event"""
    return {
        'topic': 'test.topic',
        'event_id': 'evt-12345',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'source': 'test-service',
        'payload': {'key': 'value', 'count': 42}
    }


class TestDedupStore:
    """Test suite untuk DedupStore (6 tests)"""
    
    def test_store_initialization(self, dedup_store):
        """Test: Database dan tabel dibuat dengan benar"""
        assert os.path.exists(dedup_store.db_path)
        stats = dedup_store.get_stats()
        assert stats['total_processed'] == 0
    
    def test_store_event(self, dedup_store, sample_event):
        """Test: Event dapat disimpan dengan benar"""
        stored = dedup_store.store_event(sample_event)
        assert stored is True
        
        events = dedup_store.get_events()
        assert len(events) == 1
        assert events[0]['event_id'] == sample_event['event_id']
    
    def test_duplicate_detection(self, dedup_store, sample_event):
        """Test: Duplikasi terdeteksi dengan benar"""
        stored1 = dedup_store.store_event(sample_event)
        assert stored1 is True
        
        stored2 = dedup_store.store_event(sample_event)
        assert stored2 is False
        
        events = dedup_store.get_events()
        assert len(events) == 1
    
    def test_multiple_events(self, dedup_store):
        """Test: Multiple event dengan ID berbeda disimpan"""
        for i in range(5):
            event = {
                'topic': 'test',
                'event_id': f'evt-{i}',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'test',
                'payload': {'index': i}
            }
            stored = dedup_store.store_event(event)
            assert stored is True
        
        events = dedup_store.get_events(limit=10)
        assert len(events) == 5
    
    def test_filter_by_topic(self, dedup_store):
        """Test: Filter events berdasarkan topic"""
        topics = ['topic.a', 'topic.b', 'topic.a']
        for i, topic in enumerate(topics):
            event = {
                'topic': topic,
                'event_id': f'evt-{i}',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'test',
                'payload': {}
            }
            dedup_store.store_event(event)
        
        topic_a_events = dedup_store.get_events(topic='topic.a')
        assert len(topic_a_events) == 2
        
        topic_b_events = dedup_store.get_events(topic='topic.b')
        assert len(topic_b_events) == 1
    
    def test_persistence(self, temp_db, sample_event):
        """Test: Data persisten setelah restart"""
        store1 = DedupStore(temp_db)
        store1.store_event(sample_event)
        store1.close()
        
        store2 = DedupStore(temp_db)
        assert store2.is_duplicate(sample_event['topic'], sample_event['event_id']) is True
        events = store2.get_events()
        assert len(events) == 1
        store2.close()


class TestEventConsumer:
    """Test suite untuk EventConsumer (5 tests)"""
    
    @pytest.mark.asyncio
    async def test_consumer_initialization(self, consumer):
        """Test: Consumer diinisialisasi dengan benar"""
        assert consumer.stats['received'] == 0
        assert consumer.stats['unique_processed'] == 0
        assert consumer.stats['duplicate_dropped'] == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_event(self, consumer, sample_event):
        """Test: Event dapat dienqueue"""
        await consumer.enqueue(sample_event)
        assert consumer.stats['received'] == 1
        assert consumer.queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_process_unique_event(self, consumer, sample_event):
        """Test: Event unik diproses dengan benar"""
        consumer_task = asyncio.create_task(consumer.start())
        
        await consumer.enqueue(sample_event)
        await asyncio.sleep(0.5)
        
        consumer.stop()
        await consumer_task
        
        assert consumer.stats['unique_processed'] == 1
        assert consumer.stats['duplicate_dropped'] == 0
    
    @pytest.mark.asyncio
    async def test_process_duplicate_event(self, consumer, sample_event):
        """Test: Event duplikat dibuang dengan benar"""
        consumer_task = asyncio.create_task(consumer.start())
        
        await consumer.enqueue(sample_event)
        await consumer.enqueue(sample_event)
        await asyncio.sleep(0.5)
        
        consumer.stop()
        await consumer_task
        
        assert consumer.stats['unique_processed'] == 1
        assert consumer.stats['duplicate_dropped'] == 1
        assert consumer.stats['received'] == 2
    
    @pytest.mark.asyncio
    async def test_get_stats(self, consumer, sample_event):
        """Test: Statistik dikembalikan dengan benar"""
        consumer_task = asyncio.create_task(consumer.start())
        
        await consumer.enqueue(sample_event)
        await asyncio.sleep(0.5)
        
        consumer.stop()
        await consumer_task
        
        stats = consumer.get_stats()
        assert 'received' in stats
        assert 'unique_processed' in stats
        assert 'duplicate_dropped' in stats
        assert 'topics' in stats
        assert 'uptime' in stats
        assert stats['uptime'] > 0


class TestEventModel:
    """Test suite untuk Event model validation (3 tests)"""
    
    def test_valid_event(self):
        """Test: Event valid dapat dibuat"""
        event = Event(
            topic="test.topic",
            event_id="evt-123",
            timestamp="2025-10-22T10:30:00Z",
            source="test-service",
            payload={"key": "value"}
        )
        assert event.topic == "test.topic"
        assert event.event_id == "evt-123"
    
    def test_invalid_timestamp(self):
        """Test: Timestamp invalid ditolak"""
        with pytest.raises(ValueError):
            Event(
                topic="test.topic",
                event_id="evt-123",
                timestamp="invalid-timestamp",
                source="test-service",
                payload={}
            )
    
    def test_missing_required_fields(self):
        """Test: Field required yang hilang menyebabkan error"""
        with pytest.raises(ValueError):
            Event(
                topic="test.topic",
                timestamp="2025-10-22T10:30:00Z",
                source="test-service"
            )


# Run tests jika dijalankan langsung
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
