"""
Consumer/Aggregator Service
Memproses event dari queue dengan idempotency dan deduplication
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from .dedup_store import DedupStore

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumer yang memproses event dari queue
    Fitur:
    - Idempotent: event yang sama (topic, event_id) hanya diproses sekali
    - Deduplication: mendeteksi dan membuang event duplikat
    - Persistent storage: menggunakan DedupStore untuk tahan restart
    """
    
    def __init__(self, dedup_store: DedupStore):
        """
        Inisialisasi consumer
        
        Args:
            dedup_store: Instance DedupStore untuk persistensi
        """
        self.dedup_store = dedup_store
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
        # Statistik
        self.stats = {
            'received': 0,
            'unique_processed': 0,
            'duplicate_dropped': 0,
            'start_time': datetime.utcnow()
        }
        
        logger.info("EventConsumer initialized")
    
    async def enqueue(self, event: dict):
        """
        Tambahkan event ke queue untuk diproses
        
        Args:
            event: Event dictionary
        """
        await self.queue.put(event)
        self.stats['received'] += 1
        logger.debug(f"Event enqueued: {event['topic']}:{event['event_id']}")
    
    async def start(self):
        """
        Mulai consumer loop
        Consumer akan memproses event dari queue secara asynchronous
        """
        self.is_running = True
        logger.info("EventConsumer started")
        
        while self.is_running:
            try:
                # Ambil event dari queue dengan timeout
                event = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                # Tidak ada event, lanjut loop
                continue
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
    
    async def _process_event(self, event: dict):
        """
        Proses single event dengan idempotency check
        
        Args:
            event: Event dictionary
        """
        topic = event['topic']
        event_id = event['event_id']
        
        # Cek apakah event sudah pernah diproses (idempotency check)
        if self.dedup_store.is_duplicate(topic, event_id):
            self.stats['duplicate_dropped'] += 1
            logger.info(f"Duplicate event dropped: {topic}:{event_id}")
            return
        
        # Simpan event ke dedup store
        stored = self.dedup_store.store_event(event)
        
        if stored:
            self.stats['unique_processed'] += 1
            logger.info(f"Event processed: {topic}:{event_id}")
            
            # Simulasi pemrosesan event
            # Di sini bisa ditambahkan logic pemrosesan sebenarnya
            await self._simulate_processing(event)
        else:
            # Race condition: event sudah disimpan oleh proses lain
            self.stats['duplicate_dropped'] += 1
            logger.warning(f"Event already processed (race condition): {topic}:{event_id}")
    
    async def _simulate_processing(self, event: dict):
        """
        Simulasi pemrosesan event
        Bisa diganti dengan logic pemrosesan sebenarnya
        
        Args:
            event: Event dictionary
        """
        # Log event yang diproses
        logger.debug(f"Processing event: {event}")
        
        # Simulasi I/O operation
        await asyncio.sleep(0.01)
    
    def stop(self):
        """Stop consumer loop"""
        self.is_running = False
        logger.info("EventConsumer stopped")
    
    def get_stats(self) -> Dict:
        """
        Dapatkan statistik consumer
        
        Returns:
            Dictionary berisi statistik
        """
        uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        return {
            'received': self.stats['received'],
            'unique_processed': self.stats['unique_processed'],
            'duplicate_dropped': self.stats['duplicate_dropped'],
            'topics': self.dedup_store.get_topics(),
            'uptime': uptime
        }
    
    def get_events(self, topic: str = None, limit: int = 100) -> List[Dict]:
        """
        Dapatkan daftar event yang telah diproses
        
        Args:
            topic: Filter berdasarkan topic (optional)
            limit: Maksimal jumlah event
            
        Returns:
            List of event dictionaries
        """
        return self.dedup_store.get_events(topic, limit)
