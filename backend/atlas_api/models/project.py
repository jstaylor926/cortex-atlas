"""
Project models
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    """Base project model"""
    name: str
    root_path: str
    type: str = "code"  # code | general


class ProjectCreate(ProjectBase):
    """Create project request"""
    pass


class ProjectUpdate(BaseModel):
    """Update project request"""
    name: Optional[str] = None
    root_path: Optional[str] = None
    type: Optional[str] = None


class Project(ProjectBase):
    """Full project model"""
    id: str
    created_at: datetime
    updated_at: datetime
    linked_notes: List[str] = []  # Note IDs

    class Config:
        from_attributes = True
