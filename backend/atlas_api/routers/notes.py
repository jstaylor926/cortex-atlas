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


from ..utils.wiki_links import parse_wiki_links
from ..utils.task_extraction import extract_tasks_from_markdown


def get_backlinks(note_id: str, conn: sqlite3.Connection) -> List[Backlink]:
    """Find all notes that link to this note via the note_links table"""
    cursor = conn.cursor()

    # Get the title of the target note
    target = cursor.execute(
        "SELECT title FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    if not target:
        return []

    target_title = target['title']

    # Query the note_links table to find notes that link to target_title
    # Then join with the notes table to get the source note details
    query = """
        SELECT
            n.id AS note_id,
            n.title AS title
        FROM note_links nl
        JOIN notes n ON nl.source_note_id = n.id
        WHERE nl.target_note_title = ?
          AND nl.source_note_id != ?  -- Exclude the note itself
    """
    rows = cursor.execute(query, (target_title, note_id,)).fetchall()

    backlinks = []
    for row in rows:
        backlinks.append(Backlink(
            note_id=row['note_id'],
            title=row['title']
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

    query = "SELECT n.* FROM notes n"
    params = []
    where_clauses = ["1=1"]

    if q:
        query = "SELECT n.* FROM notes n JOIN notes_fts nft ON n.rowid = nft.rowid WHERE nft MATCH ?"
        params.append(q)
    
    if tag:
        where_clauses.append("n.tags LIKE ?")
        params.append(f'%"{tag}"%')

    if len(where_clauses) > 1: # If there are additional filters beyond FTS or if FTS isn't used
        if q: # if q is used, add additional filters to WHERE clause
            query += " AND " + " AND ".join(where_clauses[1:]) 
        else: # if q is not used, define the WHERE clause
            query += " WHERE " + " AND ".join(where_clauses)

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
        note_dict['links'] = parse_wiki_links(note_dict['content'])
        note_dict['backlinks'] = []
        extracted_tasks = extract_tasks_from_markdown(note_dict['content'])
        total_tasks = len(extracted_tasks)
        open_tasks = sum(1 for task in extracted_tasks if task['status'] == 'todo')
        done_tasks = total_tasks - open_tasks
        note_dict['task_count'] = NoteTaskCount(total=total_tasks, open=open_tasks, done=done_tasks)
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
        ) # Missing parenthesis added here
    )

    # Extract wiki-links and insert into note_links table
    extracted_links = parse_wiki_links(note.content)
    for link_target in extracted_links:
        cursor.execute(
            """
            INSERT INTO note_links (source_note_id, target_note_title)
            VALUES (?, ?)
            """,
            (note_id, link_target)
        )
    conn.commit()
    conn.close()

    extracted_tasks = extract_tasks_from_markdown(note.content)
    total_tasks = len(extracted_tasks)
    open_tasks = sum(1 for task in extracted_tasks if task['status'] == 'todo')
    done_tasks = total_tasks - open_tasks
    task_count = NoteTaskCount(total=total_tasks, open=open_tasks, done=done_tasks)

    return {
        "id": note_id,
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "created_at": now,
        "updated_at": now,
        "links": parse_wiki_links(note.content),
        "backlinks": [],
        "task_count": task_count
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
    note_dict['links'] = parse_wiki_links(note_dict['content'])
    note_dict['backlinks'] = [bl.dict() for bl in get_backlinks(note_id, conn)]
    
    extracted_tasks = extract_tasks_from_markdown(note_dict['content'])
    total_tasks = len(extracted_tasks)
    open_tasks = sum(1 for task in extracted_tasks if task['status'] == 'todo')
    done_tasks = total_tasks - open_tasks
    note_dict['task_count'] = NoteTaskCount(total=total_tasks, open=open_tasks, done=done_tasks)

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
        
    # If content is updated, clear existing links from note_links table
    if update.content is not None:
        cursor.execute("DELETE FROM note_links WHERE source_note_id = ?", (note_id,))

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(note_id)

    query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()

    # Fetch updated note to get its content (potentially new content)
    updated = cursor.execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    
    # If content was updated, re-extract links and insert into note_links table
    if update.content is not None: # Re-evaluate links if content changed
        new_links = parse_wiki_links(updated['content'])
        for link_target in new_links:
            cursor.execute(
                """
                INSERT OR IGNORE INTO note_links (source_note_id, target_note_title)
                VALUES (?, ?)
                """,
                (note_id, link_target)
            )
        conn.commit()

    # Fetch updated note
    updated = cursor.execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    note_dict = dict(updated)
    note_dict['tags'] = json.loads(note_dict.get('tags') or '[]')
    note_dict['links'] = parse_wiki_links(note_dict['content'])
    note_dict['backlinks'] = [bl.dict() for bl in get_backlinks(note_id, conn)]
    extracted_tasks = extract_tasks_from_markdown(note_dict['content'])
    total_tasks = len(extracted_tasks)
    open_tasks = sum(1 for task in extracted_tasks if task['status'] == 'todo')
    done_tasks = total_tasks - open_tasks
    note_dict['task_count'] = NoteTaskCount(total=total_tasks, open=open_tasks, done=done_tasks)

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
