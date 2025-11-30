"""
Task models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskBase(BaseModel):
    """Base task model"""
    title: str
    description: Optional[str] = None
    status: str = "todo"  # todo | in_progress | done
    priority: str = "medium"  # low | medium | high
    due_date: Optional[datetime] = None
    tags: List[str] = []
    project_id: Optional[str] = None


class TaskCreate(TaskBase):
    """Create task request"""
    source_note_id: Optional[str] = None
    source_line: Optional[int] = None


class TaskUpdate(BaseModel):
    """Update task request"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None


class Task(TaskBase):
    """Full task model"""
    id: str
    source_note_id: Optional[str] = None
    source_line: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
