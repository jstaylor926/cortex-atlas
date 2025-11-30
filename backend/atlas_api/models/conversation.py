"""
Conversation and chat message models
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationBase(BaseModel):
    """Base conversation model"""
    title: str


class ConversationCreate(ConversationBase):
    """Create conversation request"""
    pass


class Conversation(ConversationBase):
    """Full conversation model"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = None
    pinned: bool = False

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Create message request"""
    role: str  # user | assistant | system
    content: str
    model: Optional[str] = None
    references: Optional[Dict[str, List[str]]] = None


class ChatMessage(BaseModel):
    """Full chat message model"""
    id: str
    conversation_id: str
    role: str
    content: str
    model: Optional[str] = None
    timestamp: datetime
    references: Optional[Dict[str, List[str]]] = None

    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    """Conversation with messages"""
    messages: List[ChatMessage] = []
