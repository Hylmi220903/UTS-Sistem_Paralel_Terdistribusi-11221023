"""
Unit Tests untuk Pub-Sub Log Aggregator
Mencakup: deduplication, persistence, schema validation, endpoints, stress test
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
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def dedup_store(temp_db):
    """Fixture untuk DedupStore"""
    return DedupStore(temp_db)


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
    """Test suite untuk DedupStore"""
    
    def test_store_initialization(self, dedup_store):
        """Test: Database dan tabel dibuat dengan benar"""
        assert os.path.exists(dedup_store.db_path)
        stats = dedup_store.get_stats()
        assert stats['total_processed'] == 0
    
    def test_store_event(self, dedup_store, sample_event):
        """Test: Event dapat disimpan dengan benar"""
        stored = dedup_store.store_event(sample_event)
        assert stored is True
        
        # Verify event tersimpan
        events = dedup_store.get_events()
        assert len(events) == 1
        assert events[0]['event_id'] == sample_event['event_id']
    
    def test_duplicate_detection(self, dedup_store, sample_event):
        """Test: Duplikasi terdeteksi dengan benar"""
        # Store pertama kali
        stored1 = dedup_store.store_event(sample_event)
        assert stored1 is True
        
        # Store kedua kali (duplikat)
        stored2 = dedup_store.store_event(sample_event)
        assert stored2 is False
        
        # Verify hanya ada satu event
        events = dedup_store.get_events()
        assert len(events) == 1
    
    def test_is_duplicate_check(self, dedup_store, sample_event):
        """Test: is_duplicate method berfungsi dengan benar"""
        # Sebelum store
        assert dedup_store.is_duplicate(sample_event['topic'], sample_event['event_id']) is False
        
        # Setelah store
        dedup_store.store_event(sample_event)
        assert dedup_store.is_duplicate(sample_event['topic'], sample_event['event_id']) is True
    
    def test_multiple_events_different_ids(self, dedup_store):
        """Test: Multiple event dengan ID berbeda dapat disimpan"""
        events = [
            {'topic': 'test', 'event_id': f'evt-{i}', 'timestamp': datetime.utcnow().isoformat() + 'Z',
             'source': 'test', 'payload': {'index': i}}
            for i in range(5)
        ]
        
        for event in events:
            stored = dedup_store.store_event(event)
            assert stored is True
        
        # Verify semua event tersimpan
        stored_events = dedup_store.get_events(limit=10)
        assert len(stored_events) == 5
    
    def test_get_events_by_topic(self, dedup_store):
        """Test: Filter events berdasarkan topic"""
        # Store events dengan topic berbeda
        topics = ['topic.a', 'topic.b', 'topic.a', 'topic.c']
        for i, topic in enumerate(topics):
            event = {
                'topic': topic,
                'event_id': f'evt-{i}',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'test',
                'payload': {}
            }
            dedup_store.store_event(event)
        
        # Test filter by topic
        topic_a_events = dedup_store.get_events(topic='topic.a')
        assert len(topic_a_events) == 2
        
        topic_b_events = dedup_store.get_events(topic='topic.b')
        assert len(topic_b_events) == 1
    
    def test_get_topics(self, dedup_store):
        """Test: Mendapatkan list topics yang unik"""
        topics = ['user.login', 'user.logout', 'user.login', 'payment.success']
        for i, topic in enumerate(topics):
            event = {
                'topic': topic,
                'event_id': f'evt-{i}',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'test',
                'payload': {}
            }
            dedup_store.store_event(event)
        
        unique_topics = dedup_store.get_topics()
        assert len(unique_topics) == 3  # user.login, user.logout, payment.success
        assert 'user.login' in unique_topics
        assert 'user.logout' in unique_topics
        assert 'payment.success' in unique_topics
    
    def test_persistence_after_restart(self, temp_db, sample_event):
        """Test: Data persisten setelah restart (simulasi)"""
        # Store dengan instance pertama
        store1 = DedupStore(temp_db)
        store1.store_event(sample_event)
        
        # Buat instance baru (simulasi restart)
        store2 = DedupStore(temp_db)
        
        # Verify data masih ada
        assert store2.is_duplicate(sample_event['topic'], sample_event['event_id']) is True
        events = store2.get_events()
        assert len(events) == 1


class TestEventConsumer:
    """Test suite untuk EventConsumer"""
    
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
        # Start consumer
        consumer_task = asyncio.create_task(consumer.start())
        
        # Enqueue event
        await consumer.enqueue(sample_event)
        
        # Tunggu processing
        await asyncio.sleep(0.5)
        
        # Stop consumer
        consumer.stop()
        await consumer_task
        
        # Verify stats
        assert consumer.stats['unique_processed'] == 1
        assert consumer.stats['duplicate_dropped'] == 0
    
    @pytest.mark.asyncio
    async def test_process_duplicate_event(self, consumer, sample_event):
        """Test: Event duplikat dibuang dengan benar"""
        # Start consumer
        consumer_task = asyncio.create_task(consumer.start())
        
        # Enqueue same event twice
        await consumer.enqueue(sample_event)
        await consumer.enqueue(sample_event)
        
        # Tunggu processing
        await asyncio.sleep(0.5)
        
        # Stop consumer
        consumer.stop()
        await consumer_task
        
        # Verify stats: hanya 1 yang diproses, 1 dropped
        assert consumer.stats['unique_processed'] == 1
        assert consumer.stats['duplicate_dropped'] == 1
        assert consumer.stats['received'] == 2
    
    @pytest.mark.asyncio
    async def test_get_stats(self, consumer, sample_event):
        """Test: Statistik dikembalikan dengan benar"""
        # Start consumer
        consumer_task = asyncio.create_task(consumer.start())
        
        # Process some events
        await consumer.enqueue(sample_event)
        await asyncio.sleep(0.5)
        
        consumer.stop()
        await consumer_task
        
        # Get stats
        stats = consumer.get_stats()
        
        assert 'received' in stats
        assert 'unique_processed' in stats
        assert 'duplicate_dropped' in stats
        assert 'topics' in stats
        assert 'uptime' in stats
        assert stats['uptime'] > 0


class TestEventModel:
    """Test suite untuk Event model validation"""
    
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
                # event_id missing
                timestamp="2025-10-22T10:30:00Z",
                source="test-service"
            )


class TestStressLoad:
    """Test suite untuk stress testing"""
    
    @pytest.mark.asyncio
    async def test_high_volume_events(self, consumer):
        """Test: Sistem dapat menangani volume tinggi (>5000 events dengan 20% duplikasi)"""
        # Start consumer
        consumer_task = asyncio.create_task(consumer.start())
        
        total_events = 5000
        duplicate_rate = 0.2  # 20% duplikasi
        
        # Generate events
        events = []
        for i in range(total_events):
            # Buat duplikat untuk 20% event
            if i > 0 and i % 5 == 0:  # Setiap event ke-5 adalah duplikat
                event_id = f'evt-{i-1}'  # Gunakan ID sebelumnya
            else:
                event_id = f'evt-{i}'
            
            event = {
                'topic': f'topic-{i % 10}',  # 10 topics berbeda
                'event_id': event_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'stress-test',
                'payload': {'index': i}
            }
            events.append(event)
        
        # Enqueue all events
        for event in events:
            await consumer.enqueue(event)
        
        # Tunggu processing (dengan timeout)
        timeout = 30  # 30 detik untuk 5000 events
        wait_time = 0
        while consumer.queue.qsize() > 0 and wait_time < timeout:
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        # Stop consumer
        consumer.stop()
        await consumer_task
        
        # Verify stats
        assert consumer.stats['received'] == total_events
        assert consumer.stats['unique_processed'] > 0
        assert consumer.stats['duplicate_dropped'] > 0
        
        # Verify sistem masih responsif
        stats = consumer.get_stats()
        assert stats is not None


# Run tests jika dijalankan langsung
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
