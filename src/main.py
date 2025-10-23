"""
Main Application - Pub-Sub Log Aggregator
FastAPI application dengan endpoint publish dan stats
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime
from typing import Optional, List

from .models import Event, PublishResponse, StatsResponse, EventListResponse
from .dedup_store import DedupStore
from .consumer import EventConsumer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
dedup_store: Optional[DedupStore] = None
consumer: Optional[EventConsumer] = None
consumer_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager untuk startup dan shutdown
    """
    global dedup_store, consumer, consumer_task
    
    # Startup
    logger.info("Starting Pub-Sub Log Aggregator...")
    
    # Inisialisasi dedup store
    dedup_store = DedupStore("data/dedup_store.db")
    
    # Inisialisasi consumer
    consumer = EventConsumer(dedup_store)
    
    # Start consumer dalam background task
    consumer_task = asyncio.create_task(consumer.start())
    logger.info("Consumer started in background")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    consumer.stop()
    
    # Tunggu consumer task selesai
    if consumer_task:
        try:
            await asyncio.wait_for(consumer_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Consumer task did not finish in time")
    
    logger.info("Application shut down")


# Inisialisasi FastAPI app
app = FastAPI(
    title="Pub-Sub Log Aggregator",
    description="Log aggregator dengan idempotent consumer dan deduplication",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Pub-Sub Log Aggregator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "publish": "POST /publish",
            "events": "GET /events?topic={topic}",
            "stats": "GET /stats"
        }
    }


@app.post("/publish", response_model=PublishResponse)
async def publish_event(event: Event):
    """
    Endpoint untuk menerima event dari publisher
    
    Event akan divalidasi, kemudian dikirim ke consumer untuk diproses
    
    Args:
        event: Event object dengan schema yang telah ditentukan
        
    Returns:
        PublishResponse dengan status dan informasi event
    """
    try:
        # Convert event ke dictionary
        event_dict = event.dict()
        
        # Enqueue event untuk diproses oleh consumer
        await consumer.enqueue(event_dict)
        
        logger.info(f"Event published: {event.topic}:{event.event_id}")
        
        return PublishResponse(
            status="accepted",
            message="Event diterima dan akan diproses",
            event_id=event.event_id,
            received_at=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error publishing event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events", response_model=EventListResponse)
async def get_events(
    topic: Optional[str] = Query(None, description="Filter berdasarkan topic"),
    limit: int = Query(100, ge=1, le=1000, description="Maksimal jumlah event")
):
    """
    Endpoint untuk mengambil daftar event yang telah diproses
    
    Args:
        topic: Filter berdasarkan topic (optional)
        limit: Maksimal jumlah event yang dikembalikan (default: 100)
        
    Returns:
        EventListResponse dengan daftar event
    """
    try:
        events = consumer.get_events(topic=topic, limit=limit)
        
        return EventListResponse(
            topic=topic,
            count=len(events),
            events=events
        )
    
    except Exception as e:
        logger.error(f"Error getting events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Endpoint untuk mendapatkan statistik sistem
    
    Returns:
        StatsResponse dengan statistik lengkap:
        - received: total event yang diterima
        - unique_processed: event unik yang diproses
        - duplicate_dropped: event duplikat yang dibuang
        - topics: daftar topic
        - uptime: waktu sistem berjalan (detik)
    """
    try:
        stats = consumer.get_stats()
        
        return StatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
