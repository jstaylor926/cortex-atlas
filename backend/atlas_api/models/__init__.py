"""
Pydantic models for API request/response
"""
from .note import Note, NoteCreate, NoteUpdate, Backlink, NoteTaskCount
from .task import Task, TaskCreate, TaskUpdate
from .event import Event, EventCreate, EventUpdate
from .project import Project, ProjectCreate, ProjectUpdate
from .conversation import (
    Conversation,
    ConversationCreate,
    ChatMessage,
    MessageCreate,
    ConversationWithMessages
)

__all__ = [
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "Backlink",
    "NoteTaskCount",
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "Event",
    "EventCreate",
    "EventUpdate",
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "Conversation",
    "ConversationCreate",
    "ChatMessage",
    "MessageCreate",
    "ConversationWithMessages",
]
