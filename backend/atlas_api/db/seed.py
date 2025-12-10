import sqlite3
import uuid
from datetime import datetime, timedelta
import json
import random
from typing import List, Dict

from atlas_api.database import get_db_connection
from atlas_api.utils.wiki_links import parse_wiki_links

def clear_all_data(conn: sqlite3.Connection):
    """Clears all data from relevant tables."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    cursor.execute("DELETE FROM conversations")
    cursor.execute("DELETE FROM event_notes")
    cursor.execute("DELETE FROM event_tasks")
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM notes")
    cursor.execute("DELETE FROM note_links")
    cursor.execute("DELETE FROM project_notes")
    cursor.execute("DELETE FROM projects")
    cursor.execute("DELETE FROM sync_state")
    cursor.execute("DELETE FROM tasks")
    # For FTS, a rebuild is usually needed after mass delete if not handled by triggers
    cursor.execute("INSERT INTO notes_fts(notes_fts) VALUES('rebuild')")
    conn.commit()
    print("All data cleared.")

def create_sample_notes(conn: sqlite3.Connection) -> List[Dict]:
    """Creates and inserts sample notes, including those with wiki-links and tasks."""
    cursor = conn.cursor()
    now = datetime.now()
    notes_data = []

    # Note 1: Basic note
    note1_id = str(uuid.uuid4())
    note1_content = "This is my first note. It's about [[Project Alpha]]."
    notes_data.append({
        "id": note1_id,
        "title": "First Steps",
        "content": note1_content,
        "tags": json.dumps(["getting-started", "idea"]),
        "created_at": (now - timedelta(days=5)).isoformat(),
        "updated_at": (now - timedelta(days=5)).isoformat()
    })

    # Note 2: Note with tasks and a wiki-link
    note2_id = str(uuid.uuid4())
    note2_content = """
# Project Alpha Meeting Notes
- [x] Review Q4 report
- [ ] Prepare presentation slides for [[Next Week's Meeting]]
- [ ] Schedule follow-up with [[Client X]]
This note is crucial for [[Project Alpha]].
"""
    notes_data.append({
        "id": note2_id,
        "title": "Project Alpha Update",
        "content": note2_content,
        "tags": json.dumps(["project", "meeting"]),
        "created_at": (now - timedelta(days=3)).isoformat(),
        "updated_at": (now - timedelta(days=1)).isoformat()
    })

    # Note 3: Note linking back to note 2
    note3_id = str(uuid.uuid4())
    note3_content = "This note references the [[Project Alpha Update]] and discusses progress."
    notes_data.append({
        "id": note3_id,
        "title": "Project Alpha Progress",
        "content": note3_content,
        "tags": json.dumps(["project", "status"]),
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": (now - timedelta(days=2)).isoformat()
    })
    
    # Note 4: Note for "Next Week's Meeting"
    note4_id = str(uuid.uuid4())
    note4_content = "Agenda items for the next weekly meeting. This was linked from [[Project Alpha Update]]."
    notes_data.append({
        "id": note4_id,
        "title": "Next Week's Meeting",
        "content": note4_content,
        "tags": json.dumps(["meeting", "planning"]),
        "created_at": (now - timedelta(hours=10)).isoformat(),
        "updated_at": (now - timedelta(hours=10)).isoformat()
    })


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
    conn.commit()
    print(f"Inserted {len(notes_data)} sample notes.")
    return notes_data

def create_sample_tasks(conn: sqlite3.Connection):
    """Creates and inserts sample tasks."""
    cursor = conn.cursor()
    now = datetime.now()
    tasks_data = []

    # Standalone tasks
    tasks_data.append({
        "id": str(uuid.uuid4()),
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "status": "todo",
        "priority": "high",
        "due_date": (now + timedelta(days=1)).isoformat(),
        "tags": json.dumps(["personal", "urgent"]),
        "source_note_id": None,
        "source_line": None,
        "project_id": None,
        "created_at": now.isoformat(),
        "completed_at": None
    })

    tasks_data.append({
        "id": str(uuid.uuid4()),
        "title": "Walk the dog",
        "description": "",
        "status": "done",
        "priority": "medium",
        "due_date": (now - timedelta(hours=2)).isoformat(),
        "tags": json.dumps(["personal"]),
        "source_note_id": None,
        "source_line": None,
        "project_id": None,
        "created_at": (now - timedelta(days=1)).isoformat(),
        "completed_at": (now - timedelta(hours=1)).isoformat()
    })
    
    tasks_data.append({
        "id": str(uuid.uuid4()),
        "title": "Write report",
        "description": "Draft Q4 financial report",
        "status": "in_progress",
        "priority": "high",
        "due_date": (now + timedelta(days=3)).isoformat(),
        "tags": json.dumps(["work", "report"]),
        "source_note_id": None,
        "source_line": None,
        "project_id": None,
        "created_at": now.isoformat(),
        "completed_at": None
    })

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
    conn.commit()
    print(f"Inserted {len(tasks_data)} sample tasks.")


def create_sample_events(conn: sqlite3.Connection):
    """Creates and inserts sample events."""
    cursor = conn.cursor()
    now = datetime.now()
    events_data = []

    events_data.append({
        "id": str(uuid.uuid4()),
        "title": "Team Sync",
        "description": "Weekly team synchronization meeting",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
        "location": "Zoom",
        "source": "local",
        "external_id": None,
        "calendar_id": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    })

    events_data.append({
        "id": str(uuid.uuid4()),
        "title": "Doctor's Appointment",
        "description": "Annual check-up",
        "start_time": (now + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
        "end_time": (now + timedelta(days=7)).replace(hour=11, minute=0, second=0, microsecond=0).isoformat(),
        "location": "Clinic",
        "source": "local",
        "external_id": None,
        "calendar_id": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    })

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
    print(f"Inserted {len(events_data)} sample events.")


def seed_database():
    """Seeds the database with sample data."""
    with get_db_connection() as conn:
        print("Seeding database...")
        clear_all_data(conn)
        create_sample_notes(conn)
        create_sample_tasks(conn)
        create_sample_events(conn)
        print("Database seeding complete.")

if __name__ == '__main__':
    seed_database()
