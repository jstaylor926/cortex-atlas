import pytest
import httpx
from fastapi.testclient import TestClient
import sqlite3
from typing import Generator
from datetime import datetime, timedelta
import json

# Import the main FastAPI app and the dependency for the database
from atlas_api.main import app
from atlas_api.database import get_db_connection

# This fixture is defined in conftest.py and provides an in-memory db with schema
# We need to explicitly import it if we want to use it in this file, though pytest
# will discover it automatically if it's in conftest.py in the same or parent dir.
from tests.conftest import in_memory_db, seeded_db

# Override the get_db_connection dependency to use the test database
def override_get_db_connection(db_conn: sqlite3.Connection):
    """Overrides the FastAPI dependency to use the provided test connection."""
    try:
        yield db_conn
    finally:
        pass # The fixture handles closing the connection


@pytest.fixture(scope="function")
def client(in_memory_db: sqlite3.Connection) -> Generator[TestClient, None, None]:
    """
    Provides a FastAPI test client configured to use the in-memory test database.
    """
    app.dependency_overrides[get_db_connection] = lambda: override_get_db_connection(in_memory_db)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear() # Clear overrides after test

@pytest.fixture(scope="function")
def seeded_client(seeded_db: sqlite3.Connection) -> Generator[TestClient, None, None]:
    """
    Provides a FastAPI test client configured to use the seeded in-memory test database.
    """
    app.dependency_overrides[get_db_connection] = lambda: override_get_db_connection(seeded_db)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_note_data():
    """Provides sample data for creating a new note."""
    return {
        "title": "New Test Note",
        "content": "This is a new test note with a [[Link to another note]].",
        "tags": ["test", "new"]
    }

class TestNotesAPI:

    async def test_list_notes_empty(self, client: TestClient):
        response = client.get("/notes")
        assert response.status_code == 200
        assert response.json() == {"notes": [], "total": 0, "limit": 20, "offset": 0}

    async def test_create_note(self, client: TestClient, sample_note_data: dict):
        response = client.post("/notes", json=sample_note_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_note_data["title"]
        assert data["content"] == sample_note_data["content"]
        assert data["tags"] == sample_note_data["tags"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["links"] == ["Link to another note"]
        assert data["backlinks"] == []
        assert data["task_count"] == {"total": 0, "open": 0, "done": 0}

        # Verify it's in the DB
        get_response = client.get(f"/notes/{data['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == sample_note_data["title"]

        # Verify note_links entry
        with client.app.dependency_overrides[get_db_connection]() as conn:
            cursor = conn.cursor()
            link_entry = cursor.execute(
                "SELECT * FROM note_links WHERE source_note_id = ?",
                (data['id'],)
            ).fetchone()
            assert link_entry is not None
            assert link_entry['target_note_title'] == "Link to another note"


    async def test_get_note_not_found(self, client: TestClient):
        response = client.get(f"/notes/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Note not found"}

    async def test_list_notes_seeded(self, seeded_client: TestClient):
        response = seeded_client.get("/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        # Check that links and task_count are populated for seeded notes
        for note in data["notes"]:
            if note["title"] == "Project Alpha Update":
                assert "Project Alpha" in note["links"]
                assert "Next Week's Meeting" in note["links"]
                assert "Client X" in note["links"]
                assert note["task_count"]["total"] == 3
                assert note["task_count"]["done"] == 1
                assert note["task_count"]["open"] == 2
            elif note["title"] == "First Steps":
                assert "Project Alpha" in note["links"]
                assert note["task_count"] == {"total": 0, "open": 0, "done": 0}
            elif note["title"] == "Project Alpha Progress":
                assert "Project Alpha Update" in note["links"]
                assert note["task_count"]["total"] == 1
                assert note["task_count"]["open"] == 1

    async def test_get_note_seeded(self, seeded_client: TestClient):
        # Find a note ID from the seeded data
        list_response = seeded_client.get("/notes")
        note_id = None
        for note in list_response.json()["notes"]:
            if note["title"] == "Project Alpha Update":
                note_id = note["id"]
                break
        assert note_id is not None

        response = seeded_client.get(f"/notes/{note_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Project Alpha Update"
        assert "Project Alpha" in data["links"]
        assert "Next Week's Meeting" in data["links"]
        assert "Client X" in data["links"]
        assert data["task_count"]["total"] == 3
        assert data["task_count"]["done"] == 1
        assert data["task_count"]["open"] == 2

    async def test_update_note(self, seeded_client: TestClient):
        # Find a note ID from the seeded data
        list_response = seeded_client.get("/notes")
        note_id = None
        for note in list_response.json()["notes"]:
            if note["title"] == "First Steps":
                note_id = note["id"]
                break
        assert note_id is not None

        update_data = {
            "title": "Updated First Steps",
            "content": "This note has [[Updated Link]] and a new - [x] task."
        }
        response = seeded_client.patch(f"/notes/{note_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]
        assert "Updated Link" in data["links"]
        assert data["task_count"]["total"] == 1
        assert data["task_count"]["done"] == 1

        # Verify note_links updated
        with seeded_client.app.dependency_overrides[get_db_connection]() as conn:
            cursor = conn.cursor()
            links = cursor.execute(
                "SELECT target_note_title FROM note_links WHERE source_note_id = ?",
                (note_id,)
            ).fetchall()
            assert len(links) == 1
            assert links[0]['target_note_title'] == "Updated Link"

    async def test_delete_note(self, seeded_client: TestClient):
        # Find a note ID from the seeded data
        list_response = seeded_client.get("/notes")
        note_id = None
        for note in list_response.json()["notes"]:
            if note["title"] == "First Steps":
                note_id = note["id"]
                break
        assert note_id is not None

        response = seeded_client.delete(f"/notes/{note_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Note deleted", "id": note_id}

        # Verify it's gone
        get_response = seeded_client.get(f"/notes/{note_id}")
        assert get_response.status_code == 404

        # Verify associated note_links are also deleted (due to CASCADE)
        with seeded_client.app.dependency_overrides[get_db_connection]() as conn:
            cursor = conn.cursor()
            links = cursor.execute(
                "SELECT * FROM note_links WHERE source_note_id = ?",
                (note_id,)
            ).fetchall()
            assert len(links) == 0

    async def test_search_notes_by_query(self, seeded_client: TestClient):
        response = seeded_client.get("/notes?q=alpha")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2 # "First Steps" and "Project Alpha Update"

    async def test_search_notes_by_tag(self, seeded_client: TestClient):
        response = seeded_client.get("/notes?tag=meeting")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["notes"][0]["title"] == "Project Alpha Update"

    async def test_get_note_backlinks_seeded(self, seeded_client: TestClient):
        # "Project Alpha Update" is linked by "Project Alpha Progress"
        list_response = seeded_client.get("/notes")
        project_alpha_update_id = None
        project_alpha_progress_id = None
        for note in list_response.json()["notes"]:
            if note["title"] == "Project Alpha Update":
                project_alpha_update_id = note["id"]
            if note["title"] == "Project Alpha Progress":
                project_alpha_progress_id = note["id"]
        assert project_alpha_update_id is not None
        assert project_alpha_progress_id is not None

        response = seeded_client.get(f"/notes/{project_alpha_update_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["backlinks"]) == 1
        assert data["backlinks"][0]["note_id"] == project_alpha_progress_id
        assert data["backlinks"][0]["title"] == "Project Alpha Progress"

        # Check a note with no backlinks
        response_no_bl = seeded_client.get(f"/notes/{project_alpha_progress_id}")
        assert response_no_bl.status_code == 200
        data_no_bl = response_no_bl.json()
        assert len(data_no_bl["backlinks"]) == 0
