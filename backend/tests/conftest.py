import pytest
import sqlite3
from pathlib import Path
from typing import Generator
from datetime import datetime, timedelta
import json
import uuid

# Import necessary modules from the application
from atlas_api.database import get_db_connection
from atlas_api.config import settings
from atlas_api.utils.wiki_links import parse_wiki_links

@pytest.fixture(scope="function")
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Provides an in-memory SQLite database connection with the schema applied.
    The database is fresh for each test function.
    """
    # Temporarily override the database path to use an in-memory database
    original_db_path = settings.database_path
    settings.database_path = ":memory:"

    conn = None
    try:
        # Get an in-memory connection
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row

        # Apply the schema from schema.sql
        schema_path = Path(__file__).parent.parent.parent / "backend" / "atlas_api" / "db" / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()

        yield conn
    finally:
        if conn:
            conn.close()
        # Restore the original database path
        settings.database_path = original_db_path


@pytest.fixture(scope="function")
def seeded_db(in_memory_db: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """
    Provides an in-memory SQLite database pre-filled with sample data.
    """
    conn = in_memory_db
    
    now = datetime.now()
    
    # --- Seed Notes ---
    note1_id = str(uuid.uuid4())
    note1_content = "This is my first note. It's about [[Project Alpha]]."
    
    note2_id = str(uuid.uuid4())
    note2_content = """
# Project Alpha Meeting Notes
- [x] Review Q4 report
- [ ] Prepare presentation slides for [[Next Week's Meeting]]
- [ ] Schedule follow-up with [[Client X]]
This note is crucial for [[Project Alpha]].
"""
    
    note3_id = str(uuid.uuid4())
    note3_content = "This note references the [[Project Alpha Update]] and discusses progress. Also has a task - [ ] Buy milk."
    
    notes_data = [
        {
            "id": note1_id,
            "title": "First Steps",
            "content": note1_content,
            "tags": json.dumps(["getting-started", "idea"]),
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=5)).isoformat()
        },
        {
            "id": note2_id,
            "title": "Project Alpha Update",
            "content": note2_content,
            "tags": json.dumps(["project", "meeting"]),
            "created_at": (now - timedelta(days=3)).isoformat(),
            "updated_at": (now - timedelta(days=1)).isoformat()
        },
        {
            "id": note3_id,
            "title": "Project Alpha Progress",
            "content": note3_content,
            "tags": json.dumps(["project", "status"]),
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": (now - timedelta(days=2)).isoformat()
        }
    ]

    cursor = conn.cursor()
    for note in notes_data:
        cursor.execute(
            """
            INSERT INTO notes (id, title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                note['id'],
                note['title'],
                note['content'],
                note['tags'],
                note['created_at'],
                note['updated_at']
            )
        )
        # Process wiki-links for each note
        extracted_links = parse_wiki_links(note['content'])
        for link_target in extracted_links:
            cursor.execute(
                """
                INSERT OR IGNORE INTO note_links (source_note_id, target_note_title)
                VALUES (?, ?)
                """,
                (note['id'], link_target)
            )
    
    # --- Seed Tasks ---
    task1_id = str(uuid.uuid4())
    task2_id = str(uuid.uuid4())
    tasks_data = [
        {
            "id": task1_id,
            "title": "Standalone Task",
            "description": "This is a task not linked to any note.",
            "status": "todo",
            "priority": "medium",
            "due_date": (now + timedelta(days=1)).isoformat(),
            "tags": json.dumps(["personal"]),
            "source_note_id": None,
            "source_line": None,
            "project_id": None,
            "created_at": now.isoformat(),
            "completed_at": None
        },
        {
            "id": task2_id,
            "title": "Completed Note Task",
            "description": "This task is from a note.",
            "status": "done",
            "priority": "low",
            "due_date": None,
            "tags": json.dumps(["note-task"]),
            "source_note_id": note2_id,
            "source_line": 3,
            "project_id": None,
            "created_at": (now - timedelta(hours=1)).isoformat(),
            "completed_at": now.isoformat()
        }
    ]
    for task in tasks_data:
        cursor.execute(
            """
            INSERT INTO tasks (id, title, description, status, priority, due_date, tags, 
                               source_note_id, source_line, project_id, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task['id'], task['title'], task['description'], task['status'],
                task['priority'], task['due_date'], task['tags'],
                task['source_note_id'], task['source_line'], task['project_id'],
                task['created_at'], task['completed_at']
            )
        )

    # --- Seed Events ---
    event1_id = str(uuid.uuid4())
    events_data = [
        {
            "id": event1_id,
            "title": "Team Standup",
            "description": "Daily sync meeting",
            "start_time": (now + timedelta(minutes=30)).isoformat(),
            "end_time": (now + timedelta(hours=1)).isoformat(),
            "location": "Zoom",
            "source": "local",
            "external_id": None,
            "calendar_id": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    ]
    for event in events_data:
        cursor.execute(
            """
            INSERT INTO events (id, title, description, start_time, end_time, location, 
                                source, external_id, calendar_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event['id'], event['title'], event['description'], event['start_time'],
                event['end_time'], event['location'], event['source'], event['external_id'],
                event['calendar_id'], event['created_at'], event['updated_at']
            )
        )
        
    conn.commit()
    yield conn
