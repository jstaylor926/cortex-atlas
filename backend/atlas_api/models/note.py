"""
Note models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NoteBase(BaseModel):
    """Base note model"""
    title: str
    content: str
    tags: List[str] = []


class NoteCreate(NoteBase):
    """Create note request"""
    pass


class NoteUpdate(BaseModel):
    """Update note request"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteTaskCount(BaseModel):
    """Task count for a note"""
    total: int
    open: int
    done: int


class Backlink(BaseModel):
    """Note backlink"""
    note_id: str
    title: str


class Note(NoteBase):
    """Full note model with computed fields"""
    id: str
    created_at: datetime
    updated_at: datetime
    links: List[str] = []  # Wiki-link titles extracted from content
    backlinks: List[Backlink] = []
    task_count: Optional[NoteTaskCount] = None

    class Config:
        from_attributes = True
