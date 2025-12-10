"""Initial schema setup

Revision ID: 6966bd4e4575
Revises: 
Create Date: 2025-12-04 19:46:50.548328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6966bd4e4575'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
CREATE TABLE IF NOT EXISTS notes (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  content       TEXT NOT NULL,
  tags          TEXT,                -- JSON array: ["tag1", "tag2"]
  created_at    TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP NOT NULL
);
""")

    op.execute("""
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
  title,
  content,
  content=notes,
  content_rowid=rowid
);
""")

    op.execute("""
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
  INSERT INTO notes_fts(rowid, title, content)
  VALUES (new.rowid, new.title, new.content);
END;
""")

    op.execute("""
CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, old.title, old.content)
  VALUES('delete', old.rowid, old.title, old.content);
END;
""")

    op.execute("""
CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, old.title, old.content)
  VALUES('delete', old.rowid, old.title, old.content);
  INSERT INTO notes_fts(rowid, title, content)
  VALUES (new.rowid, new.title, new.content);
END;
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS tasks (
  id             TEXT PRIMARY KEY,
  title          TEXT NOT NULL,
  description    TEXT,
  status         TEXT NOT NULL,      -- todo | in_progress | done
  priority       TEXT NOT NULL,      -- low | medium | high
  due_date       TIMESTAMP,
  tags           TEXT,               -- JSON array
  source_note_id TEXT,
  source_line    INTEGER,
  project_id     TEXT,
  created_at     TIMESTAMP NOT NULL,
  completed_at   TIMESTAMP,
  FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE SET NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);
""")

    op.execute("""
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS events (
  id          TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  description TEXT,
  start_time  TIMESTAMP NOT NULL,
  end_time    TIMESTAMP NOT NULL,
  location    TEXT,
  source      TEXT NOT NULL,        -- local | google
  external_id TEXT,
  calendar_id TEXT,
  created_at  TIMESTAMP NOT NULL,
  updated_at  TIMESTAMP NOT NULL
);
""")

    op.execute("""
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS event_notes (
  event_id TEXT NOT NULL,
  note_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, note_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS event_tasks (
  event_id TEXT NOT NULL,
  task_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, task_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS projects (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  root_path  TEXT NOT NULL,
  type       TEXT NOT NULL,      -- code | general
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS project_notes (
  project_id TEXT NOT NULL,
  note_id    TEXT NOT NULL,
  PRIMARY KEY (project_id, note_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS conversations (
  id                    TEXT PRIMARY KEY,
  title                 TEXT NOT NULL,
  created_at            TIMESTAMP NOT NULL,
  updated_at            TIMESTAMP NOT NULL,
  last_message_preview  TEXT,
  pinned                INTEGER NOT NULL DEFAULT 0
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
  id              TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role            TEXT NOT NULL,      -- user | assistant | system
  content         TEXT NOT NULL,
  model           TEXT,
  timestamp       TIMESTAMP NOT NULL,
  references_json TEXT,               -- JSON: { notes: [...], tasks: [...] }
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
""")

    op.execute("""
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS embeddings (
  id          TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,        -- note | task
  source_id   TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content     TEXT NOT NULL,
  embedding   BLOB NOT NULL,        -- Serialized float array
  model       TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL
);
""")

    op.execute("""
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS sync_state (
  id         TEXT PRIMARY KEY,
  provider   TEXT NOT NULL,      -- google_calendar
  last_sync  TIMESTAMP,
  sync_token TEXT,
  metadata   TEXT                -- JSON blob
);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS note_links (
  source_note_id    TEXT NOT NULL,
  target_note_title TEXT NOT NULL,
  PRIMARY KEY (source_note_id, target_note_title),
  FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE CASCADE
);
""")

    op.execute("""
CREATE INDEX IF NOT EXISTS idx_note_links_source_note_id ON note_links(source_note_id);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_note_links_target_note_title ON note_links(target_note_title);
""")

    op.execute("""
CREATE TABLE IF NOT EXISTS settings (
  id         INTEGER PRIMARY KEY CHECK (id = 1),
  data       TEXT NOT NULL,      -- JSON blob
  updated_at TIMESTAMP NOT NULL
);
""")

    op.execute("""
INSERT OR IGNORE INTO settings (id, data, updated_at)
VALUES (1, '{}', CURRENT_TIMESTAMP);
""")


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("note_links")
    op.drop_table("sync_state")
    op.drop_table("embeddings")
    op.drop_table("chat_messages")
    op.drop_table("conversations")
    op.drop_table("project_notes")
    op.drop_table("projects")
    op.drop_table("event_tasks")
    op.drop_table("event_notes")
    op.drop_table("events")
    op.drop_table("tasks")
    op.execute("DROP TRIGGER IF EXISTS notes_au;")
    op.execute("DROP TRIGGER IF EXISTS notes_ad;")
    op.execute("DROP TRIGGER IF EXISTS notes_ai;")
    op.execute("DROP VIRTUAL TABLE IF EXISTS notes_fts;")
    op.drop_table("notes")

