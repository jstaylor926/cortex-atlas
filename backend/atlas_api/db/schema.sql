-- Atlas Database Schema
-- SQLite schema for local-first personal OS

-- ============================================================================
-- NOTES
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  content       TEXT NOT NULL,
  tags          TEXT,                -- JSON array: ["tag1", "tag2"]
  created_at    TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP NOT NULL
);

-- Full-text search index for notes
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
  title,
  content,
  content=notes,
  content_rowid=rowid
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
  INSERT INTO notes_fts(rowid, title, content)
  VALUES (new.rowid, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, content)
  VALUES('delete', old.rowid, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, content)
  VALUES('delete', old.rowid, old.title, old.content);
  INSERT INTO notes_fts(rowid, title, content)
  VALUES (new.rowid, new.title, new.content);
END;

-- ============================================================================
-- TASKS
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);

-- ============================================================================
-- EVENTS
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);

-- Event Links
CREATE TABLE IF NOT EXISTS event_notes (
  event_id TEXT NOT NULL,
  note_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, note_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_tasks (
  event_id TEXT NOT NULL,
  task_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, task_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ============================================================================
-- PROJECTS (Dev Workspace)
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  root_path  TEXT NOT NULL,
  type       TEXT NOT NULL,      -- code | general
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS project_notes (
  project_id TEXT NOT NULL,
  note_id    TEXT NOT NULL,
  PRIMARY KEY (project_id, note_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- ============================================================================
-- CONVERSATIONS & MESSAGES
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversations (
  id                    TEXT PRIMARY KEY,
  title                 TEXT NOT NULL,
  created_at            TIMESTAMP NOT NULL,
  updated_at            TIMESTAMP NOT NULL,
  last_message_preview  TEXT,
  pinned                INTEGER NOT NULL DEFAULT 0
);

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

CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id);

-- ============================================================================
-- EMBEDDINGS
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);

-- ============================================================================
-- SYNC STATE
-- ============================================================================

CREATE TABLE IF NOT EXISTS sync_state (
  id         TEXT PRIMARY KEY,
  provider   TEXT NOT NULL,      -- google_calendar
  last_sync  TIMESTAMP,
  sync_token TEXT,
  metadata   TEXT                -- JSON blob
);

-- ============================================================================
-- SETTINGS (single row)
-- ============================================================================

CREATE TABLE IF NOT EXISTS settings (
  id         INTEGER PRIMARY KEY CHECK (id = 1),
  data       TEXT NOT NULL,      -- JSON blob
  updated_at TIMESTAMP NOT NULL
);

-- Initialize default settings
INSERT OR IGNORE INTO settings (id, data, updated_at)
VALUES (1, '{}', CURRENT_TIMESTAMP);
