"""
Tasks API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
import uuid
import json
from ..models.task import Task, TaskCreate, TaskUpdate
from ..database import get_db_connection

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    overdue: bool = False,
    due_today: bool = False,
    project_id: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List tasks with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)

    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')

    if overdue:
        query += " AND due_date < ? AND status != 'done'"
        params.append(datetime.now().isoformat())

    if due_today:
        today = datetime.now().date().isoformat()
        query += " AND date(due_date) = ?"
        params.append(today)

    query += " ORDER BY due_date ASC, priority DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    tasks = []
    for row in rows:
        task_dict = dict(row)
        task_dict['tags'] = json.loads(task_dict.get('tags') or '[]')
        tasks.append(task_dict)

    return {"tasks": tasks, "total": len(tasks), "limit": limit, "offset": offset}


@router.post("")
async def create_task(task: TaskCreate):
    """Create a new task"""
    conn = get_db_connection()
    cursor = conn.cursor()

    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO tasks
        (id, title, description, status, priority, due_date, tags,
         source_note_id, source_line, project_id, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            task.title,
            task.description,
            task.status,
            task.priority,
            task.due_date.isoformat() if task.due_date else None,
            json.dumps(task.tags),
            task.source_note_id,
            task.source_line,
            task.project_id,
            now,
            None
        )
    )

    conn.commit()
    conn.close()

    return {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "tags": task.tags,
        "source_note_id": task.source_note_id,
        "source_line": task.source_line,
        "project_id": task.project_id,
        "created_at": now,
        "completed_at": None
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a single task"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = dict(row)
    task_dict['tags'] = json.loads(task_dict.get('tags') or '[]')
    return task_dict


@router.patch("/{task_id}")
async def update_task(task_id: str, update: TaskUpdate):
    """Update a task"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if task exists
    existing = cursor.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    # Build update query
    updates = []
    params = []

    if update.title is not None:
        updates.append("title = ?")
        params.append(update.title)

    if update.description is not None:
        updates.append("description = ?")
        params.append(update.description)

    if update.status is not None:
        updates.append("status = ?")
        params.append(update.status)
        # Auto-set completed_at when marking as done
        if update.status == "done":
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())

    if update.priority is not None:
        updates.append("priority = ?")
        params.append(update.priority)

    if update.due_date is not None:
        updates.append("due_date = ?")
        params.append(update.due_date.isoformat())

    if update.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(update.tags))

    if update.project_id is not None:
        updates.append("project_id = ?")
        params.append(update.project_id)

    if not updates:
        conn.close()
        task_dict = dict(existing)
        task_dict['tags'] = json.loads(task_dict.get('tags') or '[]')
        return task_dict

    params.append(task_id)
    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()

    # Fetch updated task
    updated = cursor.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    conn.close()

    task_dict = dict(updated)
    task_dict['tags'] = json.loads(task_dict.get('tags') or '[]')
    return task_dict


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted", "id": task_id}
