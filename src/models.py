"""
Data models untuk event dan response
"""
from pydantic import BaseModel, Field, validator
from typing import Any, Optional
from datetime import datetime


class Event(BaseModel):
    """
    Model untuk event yang diterima dari publisher
    Format minimal: topic, event_id, timestamp, source, payload
    """
    topic: str = Field(..., min_length=1, description="Topic/kategori event")
    event_id: str = Field(..., min_length=1, description="Unique identifier untuk event")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    source: str = Field(..., min_length=1, description="Sumber event")
    payload: dict = Field(default_factory=dict, description="Data payload event")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validasi format timestamp ISO8601"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Timestamp harus dalam format ISO8601")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "topic": "user.login",
                "event_id": "evt-12345",
                "timestamp": "2025-10-22T10:30:00Z",
                "source": "auth-service",
                "payload": {"user_id": 123, "ip": "192.168.1.1"}
            }
        }


class PublishResponse(BaseModel):
    """Response dari endpoint publish"""
    status: str
    message: str
    event_id: str
    received_at: str


class StatsResponse(BaseModel):
    """Response dari endpoint stats"""
    received: int = Field(..., description="Total event yang diterima")
    unique_processed: int = Field(..., description="Event unik yang diproses")
    duplicate_dropped: int = Field(..., description="Event duplikat yang dibuang")
    topics: list[str] = Field(..., description="Daftar topic yang ada")
    uptime: float = Field(..., description="Uptime sistem dalam detik")
    
    class Config:
        schema_extra = {
            "example": {
                "received": 1000,
                "unique_processed": 850,
                "duplicate_dropped": 150,
                "topics": ["user.login", "user.logout", "payment.success"],
                "uptime": 3600.5
            }
        }


class EventListResponse(BaseModel):
    """Response dari endpoint GET /events"""
    topic: Optional[str]
    count: int
    events: list[dict]
