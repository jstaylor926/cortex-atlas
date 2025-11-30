"""
Conversations API endpoints
"""
from fastapi import APIRouter, HTTPException, WebSocket
from typing import Optional
from datetime import datetime
import uuid
import json
from ..models.conversation import (
    Conversation,
    ConversationCreate,
    ChatMessage,
    MessageCreate
)
from ..database import get_db_connection

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(limit: int = 20, offset: int = 0):
    """List all conversations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()

    conn.close()

    conversations = [dict(row) for row in rows]
    for conv in conversations:
        conv['pinned'] = bool(conv.get('pinned', 0))

    return {
        "conversations": conversations,
        "total": len(conversations),
        "limit": limit,
        "offset": offset
    }


@router.post("")
async def create_conversation(conv: ConversationCreate):
    """Create a new conversation"""
    conn = get_db_connection()
    cursor = conn.cursor()

    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO conversations
        (id, title, created_at, updated_at, last_message_preview, pinned)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (conv_id, conv.title, now, now, None, 0)
    )

    conn.commit()
    conn.close()

    return {
        "id": conv_id,
        "title": conv.title,
        "created_at": now,
        "updated_at": now,
        "last_message_preview": None,
        "pinned": False
    }


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv_dict = dict(row)
    conv_dict['pinned'] = bool(conv_dict.get('pinned', 0))
    return conv_dict


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get messages for a conversation"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify conversation exists
    conv = cursor.execute(
        "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()

    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Fetch messages
    rows = cursor.execute(
        """
        SELECT * FROM chat_messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
        """,
        (conversation_id, limit, offset)
    ).fetchall()

    conn.close()

    messages = []
    for row in rows:
        msg_dict = dict(row)
        if msg_dict.get('references_json'):
            msg_dict['references'] = json.loads(msg_dict['references_json'])
        else:
            msg_dict['references'] = None
        del msg_dict['references_json']
        messages.append(msg_dict)

    return {
        "messages": messages,
        "total": len(messages),
        "limit": limit,
        "offset": offset
    }


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, msg: MessageCreate):
    """Send a message in a conversation (simplified - no AI response yet)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify conversation exists
    conv = cursor.execute(
        "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()

    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create user message
    msg_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    references_json = None
    if msg.references:
        references_json = json.dumps(msg.references)

    cursor.execute(
        """
        INSERT INTO chat_messages
        (id, conversation_id, role, content, model, timestamp, references_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (msg_id, conversation_id, msg.role, msg.content, msg.model, now, references_json)
    )

    # Update conversation
    preview = msg.content[:100] if len(msg.content) > 100 else msg.content
    cursor.execute(
        """
        UPDATE conversations
        SET updated_at = ?, last_message_preview = ?
        WHERE id = ?
        """,
        (now, preview, conversation_id)
    )

    conn.commit()
    conn.close()

    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": msg.role,
        "content": msg.content,
        "model": msg.model,
        "timestamp": now,
        "references": msg.references
    }


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted", "id": conversation_id}
