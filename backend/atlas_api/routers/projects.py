"""
Projects API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
import uuid
from ..models.project import Project, ProjectCreate, ProjectUpdate
from ..database import get_db_connection

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(limit: int = 50, offset: int = 0):
    """List all projects"""
    conn = get_db_connection()
    cursor = conn.cursor()

    rows = cursor.execute(
        "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    ).fetchall()

    conn.close()

    projects = [dict(row) for row in rows]
    for project in projects:
        project['linked_notes'] = []

    return {"projects": projects, "total": len(projects), "limit": limit, "offset": offset}


@router.post("")
async def create_project(project: ProjectCreate):
    """Create a new project"""
    conn = get_db_connection()
    cursor = conn.cursor()

    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO projects (id, name, root_path, type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, project.name, project.root_path, project.type, now, now)
    )

    conn.commit()
    conn.close()

    return {
        "id": project_id,
        "name": project.name,
        "root_path": project.root_path,
        "type": project.type,
        "created_at": now,
        "updated_at": now,
        "linked_notes": []
    }


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a single project"""
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    project_dict = dict(row)
    project_dict['linked_notes'] = []
    return project_dict


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted", "id": project_id}
