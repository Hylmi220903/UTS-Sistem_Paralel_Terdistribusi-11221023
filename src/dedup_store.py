"""
Deduplication Store menggunakan SQLite
Menyimpan event yang sudah diproses untuk deteksi duplikasi
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class DedupStore:
    """
    Store untuk menyimpan event yang telah diproses
    Menggunakan SQLite untuk persistensi yang tahan restart
    Idempotency: event dengan (topic, event_id) yang sama hanya diproses sekali
    """
    
    def __init__(self, db_path: str = "data/dedup_store.db"):
        """
        Inisialisasi dedup store
        
        Args:
            db_path: Path ke database SQLite
        """
        self.db_path = db_path
        self._conn = None
        
        # Pastikan direktori exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        logger.info(f"DedupStore initialized with database: {db_path}")
    
    def _get_connection(self):
        """Get or create database connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
    
    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _init_db(self):
        """Inisialisasi database dan tabel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    UNIQUE(topic, event_id)
                )
            """)
            
            # Index untuk performa lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic_event_id 
                ON processed_events(topic, event_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic 
                ON processed_events(topic)
            """)
            
            conn.commit()
    
    def is_duplicate(self, topic: str, event_id: str) -> bool:
        """
        Cek apakah event sudah pernah diproses
        
        Args:
            topic: Topic event
            event_id: ID event
            
        Returns:
            True jika event sudah pernah diproses (duplikat)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM processed_events WHERE topic = ? AND event_id = ?",
                (topic, event_id)
            )
            count = cursor.fetchone()[0]
            return count > 0
    
    def store_event(self, event: dict) -> bool:
        """
        Simpan event yang telah diproses
        
        Args:
            event: Dictionary event yang akan disimpan
            
        Returns:
            True jika berhasil disimpan, False jika duplikat
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO processed_events 
                    (topic, event_id, timestamp, source, payload, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event['topic'],
                    event['event_id'],
                    event['timestamp'],
                    event['source'],
                    json.dumps(event['payload']),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                logger.debug(f"Event stored: {event['topic']}:{event['event_id']}")
                return True
        except sqlite3.IntegrityError:
            # Duplikat terdeteksi (UNIQUE constraint violated)
            logger.debug(f"Duplicate detected: {event['topic']}:{event['event_id']}")
            return False
    
    def get_events(self, topic: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Ambil daftar event yang telah diproses
        
        Args:
            topic: Filter berdasarkan topic (optional)
            limit: Maksimal jumlah event yang dikembalikan
            
        Returns:
            List of event dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if topic:
                cursor = conn.execute("""
                    SELECT topic, event_id, timestamp, source, payload, processed_at
                    FROM processed_events
                    WHERE topic = ?
                    ORDER BY processed_at DESC
                    LIMIT ?
                """, (topic, limit))
            else:
                cursor = conn.execute("""
                    SELECT topic, event_id, timestamp, source, payload, processed_at
                    FROM processed_events
                    ORDER BY processed_at DESC
                    LIMIT ?
                """, (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'topic': row['topic'],
                    'event_id': row['event_id'],
                    'timestamp': row['timestamp'],
                    'source': row['source'],
                    'payload': json.loads(row['payload']),
                    'processed_at': row['processed_at']
                })
            
            return events
    
    def get_topics(self) -> List[str]:
        """
        Ambil daftar semua topic yang ada
        
        Returns:
            List of unique topics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT topic FROM processed_events")
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """
        Ambil statistik dari store
        
        Returns:
            Dictionary berisi statistik
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM processed_events")
            total_processed = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT topic) FROM processed_events")
            topic_count = cursor.fetchone()[0]
            
            return {
                'total_processed': total_processed,
                'topic_count': topic_count
            }
    
    def clear(self):
        """Hapus semua data (untuk testing)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM processed_events")
            conn.commit()
        logger.warning("DedupStore cleared")
