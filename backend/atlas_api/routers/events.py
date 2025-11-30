"""
Events API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
import uuid
from ..models.event import Event, EventCreate, EventUpdate
from ..database import get_db_connection

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List events with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if start_date:
        query += " AND start_time >= ?"
        params.append(start_date)

    if end_date:
        query += " AND end_time <= ?"
        params.append(end_date)

    if source:
        query += " AND source = ?"
        params.append(source)

    query += " ORDER BY start_time ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    events = [dict(row) for row in rows]
    for event in events:
        event['linked_notes'] = []
        event['linked_tasks'] = []

    return {"events": events, "total": len(events), "limit": limit, "offset": offset}


@router.post("")
async def create_event(event: EventCreate):
    """Create a new event"""
    conn = get_db_connection()
    cursor = conn.cursor()

    event_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO events
        (id, title, description, start_time, end_time, location,
         source, external_id, calendar_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event.title,
            event.description,
            event.start_time.isoformat(),
            event.end_time.isoformat(),
            event.location,
            event.source,
            event.external_id,
            event.calendar_id,
            now,
            now
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": event_id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "location": event.location,
        "source": event.source,
        "external_id": event.external_id,
        "calendar_id": event.calendar_id,
        "created_at": now,
        "updated_at": now,
        "linked_notes": [],
        "linked_tasks": []
    }


@router.get("/{event_id}")
async def get_event(event_id: str):
    """Get a single event"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Event not found")

    event_dict = dict(row)
    event_dict['linked_notes'] = []
    event_dict['linked_tasks'] = []
    return event_dict


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """Delete an event"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"message": "Event deleted", "id": event_id}
