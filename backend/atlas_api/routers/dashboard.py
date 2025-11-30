"""
Dashboard API endpoints
"""
from fastapi import APIRouter
from typing import Optional
from datetime import datetime, date, timedelta
from ..database import get_db_connection
import json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today")
async def get_today_overview(target_date: Optional[str] = None):
    """Get today's overview including tasks, events, and recent notes"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Use provided date or today
    if target_date:
        today = datetime.fromisoformat(target_date).date()
    else:
        today = date.today()

    today_start = datetime.combine(today, datetime.min.time()).isoformat()
    today_end = datetime.combine(today, datetime.max.time()).isoformat()

    # Get overdue tasks
    overdue_tasks = cursor.execute(
        """
        SELECT id, title, status, priority, due_date, tags
        FROM tasks
        WHERE status IN ('todo', 'in_progress')
          AND due_date < ?
        ORDER BY due_date ASC
        LIMIT 10
        """,
        (today_start,)
    ).fetchall()

    # Get tasks due today
    due_today_tasks = cursor.execute(
        """
        SELECT id, title, status, priority, due_date, tags
        FROM tasks
        WHERE status IN ('todo', 'in_progress')
          AND due_date >= ? AND due_date <= ?
        ORDER BY priority DESC, due_date ASC
        LIMIT 10
        """,
        (today_start, today_end)
    ).fetchall()

    # Get today's events
    events_today = cursor.execute(
        """
        SELECT id, title, start_time, end_time, location, source
        FROM events
        WHERE (date(start_time) = ? OR date(end_time) = ?)
        ORDER BY start_time ASC
        """,
        (today.isoformat(), today.isoformat())
    ).fetchall()

    # Get recent notes (last 3 days)
    three_days_ago = (today - timedelta(days=3)).isoformat()
    recent_notes = cursor.execute(
        """
        SELECT id, title, tags, created_at, updated_at
        FROM notes
        WHERE date(updated_at) >= ?
        ORDER BY updated_at DESC
        LIMIT 10
        """,
        (three_days_ago,)
    ).fetchall()

    conn.close()

    # Format results
    def format_task(task):
        task_dict = dict(task)
        task_dict['tags'] = json.loads(task_dict.get('tags') or '[]')
        return task_dict

    def format_note(note):
        note_dict = dict(note)
        note_dict['tags'] = json.loads(note_dict.get('tags') or '[]')
        return note_dict

    return {
        "date": today.isoformat(),
        "tasks": {
            "overdue": [format_task(t) for t in overdue_tasks],
            "due_today": [format_task(t) for t in due_today_tasks]
        },
        "events": [dict(e) for e in events_today],
        "recent_notes": [format_note(n) for n in recent_notes]
    }
