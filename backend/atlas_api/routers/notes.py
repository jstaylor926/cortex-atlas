"""
Notes API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
import uuid
import json
import re
from ..models.note import Note, NoteCreate, NoteUpdate, Backlink, NoteTaskCount
from ..database import get_db_connection
import sqlite3

router = APIRouter(prefix="/notes", tags=["notes"])


def extract_wiki_links(content: str) -> List[str]:
    """Extract [[Note Title]] style links"""
    pattern = r'\[\[([^\]]+)\]\]'
    return re.findall(pattern, content)


def get_backlinks(note_id: str, conn: sqlite3.Connection) -> List[Backlink]:
    """Find all notes that link to this note"""
    cursor = conn.cursor()

    # Get the title of the target note
    target = cursor.execute(
        "SELECT title FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    if not target:
        return []

    target_title = target['title']

    # Get all other notes
    all_notes = cursor.execute(
        "SELECT id, title, content FROM notes WHERE id != ?", (note_id,)
    ).fetchall()

    backlinks = []
    for note in all_notes:
        links = extract_wiki_links(note['content'])
        if target_title in links:
            backlinks.append(Backlink(
                note_id=note['id'],
                title=note['title']
            ))

    return backlinks


@router.get("")
async def list_notes(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort: str = "updated_desc"
):
    """List notes with optional filters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM notes WHERE 1=1"
    params = []

    if q:
        query += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])

    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')

    # Sorting
    if sort == "updated_desc":
        query += " ORDER BY updated_at DESC"
    elif sort == "updated_asc":
        query += " ORDER BY updated_at ASC"
    elif sort == "created_desc":
        query += " ORDER BY created_at DESC"
    elif sort == "title_asc":
        query += " ORDER BY title ASC"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    notes = []
    for row in rows:
        note_dict = dict(row)
        note_dict['tags'] = json.loads(note_dict.get('tags') or '[]')
        note_dict['links'] = extract_wiki_links(note_dict['content'])
        note_dict['backlinks'] = []
        note_dict['task_count'] = None
        notes.append(note_dict)

    return {"notes": notes, "total": len(notes), "limit": limit, "offset": offset}


@router.post("")
async def create_note(note: NoteCreate):
    """Create a new note"""
    conn = get_db_connection()
    cursor = conn.cursor()

    note_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO notes (id, title, content, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            note_id,
            note.title,
            note.content,
            json.dumps(note.tags),
            now,
            now
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": note_id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "created_at": now,
        "updated_at": now,
        "links": extract_wiki_links(note.content),
        "backlinks": [],
        "task_count": None
    }


@router.get("/{note_id}")
async def get_note(note_id: str):
    """Get a single note with backlinks"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    note_dict = dict(row)
    note_dict['tags'] = json.loads(note_dict.get('tags') or '[]')
    note_dict['links'] = extract_wiki_links(note_dict['content'])
    note_dict['backlinks'] = [bl.dict() for bl in get_backlinks(note_id, conn)]
    note_dict['task_count'] = None

    conn.close()
    return note_dict


@router.patch("/{note_id}")
async def update_note(note_id: str, update: NoteUpdate):
    """Partial update of a note"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if note exists
    existing = cursor.execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    # Build update query
    updates = []
    params = []

    if update.title is not None:
        updates.append("title = ?")
        params.append(update.title)

    if update.content is not None:
        updates.append("content = ?")
        params.append(update.content)

    if update.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(update.tags))

    if not updates:
        conn.close()
        return dict(existing)

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(note_id)

    query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()

    # Fetch updated note
    updated = cursor.execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    note_dict = dict(updated)
    note_dict['tags'] = json.loads(note_dict.get('tags') or '[]')
    note_dict['links'] = extract_wiki_links(note_dict['content'])
    note_dict['backlinks'] = [bl.dict() for bl in get_backlinks(note_id, conn)]
    note_dict['task_count'] = None

    conn.close()
    return note_dict


@router.delete("/{note_id}")
async def delete_note(note_id: str):
    """Delete a note"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"message": "Note deleted", "id": note_id}
