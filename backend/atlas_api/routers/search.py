"""
Search API endpoints
"""
from fastapi import APIRouter
from typing import Optional, List
from ..database import get_db_connection
import json

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str,
    type: str = "all",  # "all", "notes", "tasks"
    limit: int = 20,
    offset: int = 0
):
    """Full-text search across notes and tasks"""
    conn = get_db_connection()
    cursor = conn.cursor()

    results = {
        "query": q,
        "notes": [],
        "tasks": [],
        "total": 0
    }

    # Search notes
    if type in ["all", "notes"]:
        note_rows = cursor.execute(
            """
            SELECT id, title, tags, created_at, updated_at
            FROM notes
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (f"%{q}%", f"%{q}%", limit)
        ).fetchall()

        results["notes"] = [
            {
                **dict(row),
                "tags": json.loads(dict(row).get('tags') or '[]'),
                "type": "note"
            }
            for row in note_rows
        ]

    # Search tasks
    if type in ["all", "tasks"]:
        task_rows = cursor.execute(
            """
            SELECT id, title, description, status, priority, due_date, tags
            FROM tasks
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (f"%{q}%", f"%{q}%", limit)
        ).fetchall()

        results["tasks"] = [
            {
                **dict(row),
                "tags": json.loads(dict(row).get('tags') or '[]'),
                "type": "task"
            }
            for row in task_rows
        ]

    results["total"] = len(results["notes"]) + len(results["tasks"])

    conn.close()
    return results
