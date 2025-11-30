"""
Event models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EventBase(BaseModel):
    """Base event model"""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None


class EventCreate(EventBase):
    """Create event request"""
    source: str = "local"  # local | google
    external_id: Optional[str] = None
    calendar_id: Optional[str] = None


class EventUpdate(BaseModel):
    """Update event request"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None


class Event(EventBase):
    """Full event model"""
    id: str
    source: str
    external_id: Optional[str] = None
    calendar_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    linked_notes: List[str] = []  # Note IDs
    linked_tasks: List[str] = []  # Task IDs

    class Config:
        from_attributes = True
