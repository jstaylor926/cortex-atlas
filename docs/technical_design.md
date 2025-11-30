Nice, let’s lock down the data model.

I’ll do two layers:

1. **API-facing JSON shapes** (what FastAPI returns/accepts)
2. **Conceptual DB schema** (tables + columns + relationships)

You can treat this as your “source of truth” for models / migrations.

---

## 1. Conventions

* IDs: strings (`uuid` on the DB side).
* Timestamps: ISO 8601 strings in JSON (`TIMESTAMP` with timezone in DB).
* Optional fields: `null` or omitted in JSON, `NULL` in DB.
* Single-user desktop app assumption (no multi-user auth yet), so no `user_id` everywhere.

---

## 2. API JSON Shapes

### 2.1 Note

```jsonc
{
  "id": "uuid",
  "title": "Daily Log 2025-11-29",
  "content": "## Today\n- [ ] Finish Atlas schema\n- [x] Coffee",
  "tags": ["daily", "work"],
  "created_at": "2025-11-29T10:32:00Z",
  "updated_at": "2025-11-29T10:45:12Z",

  // Derived / convenience fields
  "links": ["Atlas Architecture", "Dev Workspace Spec"],  // wiki links by title
  "backlinks": [
    { "note_id": "uuid-2", "title": "Atlas Architecture" }
  ],
  "task_count": {
    "total": 3,
    "open": 2,
    "done": 1
  }
}
```

---

### 2.2 Task

```jsonc
{
  "id": "uuid",
  "title": "Define JSON schemas for Atlas v1",
  "description": "Cover notes, tasks, calendar, dev workspace, AI, settings.",
  "status": "todo", // "todo" | "in_progress" | "done"
  "priority": "high", // "low" | "medium" | "high"
  "due_date": "2025-11-30T23:59:59Z",
  "tags": ["atlas", "architecture"],

  "source_note_id": "uuid-or-null",
  "source_line": 12,            // line number in note content where the task lives
  "project_id": "uuid-or-null", // Dev workspace project

  "created_at": "2025-11-29T10:40:00Z",
  "completed_at": null
}
```

List response:

```jsonc
{
  "tasks": [ /* Task */ ],
  "filters": {
    "status": "todo",
    "overdue_only": false,
    "due_today_only": false
  }
}
```

---

### 2.3 Event

```jsonc
{
  "id": "uuid",
  "title": "Client call – CRE data center scouting",
  "description": "Review candidate parcels and Atlas prototype.",
  "start_time": "2025-12-01T14:00:00Z",
  "end_time": "2025-12-01T15:00:00Z",
  "location": "Zoom",

  "source": "google",  // "local" | "google"
  "external_id": "google-event-id-or-null",
  "calendar_id": "primary", // Google calendar id or local label

  "linked_notes": [
    { "note_id": "uuid", "title": "CRE Call Notes 2025-12-01" }
  ],
  "linked_tasks": [
    { "task_id": "uuid", "title": "Send follow-up deck" }
  ],

  "created_at": "2025-11-28T09:00:00Z",
  "updated_at": "2025-11-28T09:05:00Z"
}
```

---

### 2.4 Project (Dev Workspace)

```jsonc
{
  "id": "uuid",
  "name": "Atlas Desktop",
  "root_path": "/Users/josh/Projects/atlas-desktop",
  "type": "code", // "code" | "general"

  "linked_notes": [
    { "note_id": "uuid-1", "title": "Atlas Architecture" }
  ],
  "linked_tasks": [
    { "task_id": "uuid-2", "title": "Implement FastAPI models" }
  ],

  "created_at": "2025-11-20T12:00:00Z",
  "updated_at": "2025-11-20T12:02:00Z"
}
```

---

### 2.5 Conversation & ChatMessage

**Conversation summary:**

```jsonc
{
  "id": "uuid",
  "title": "Daily planning – 2025-11-29",
  "created_at": "2025-11-29T11:00:00Z",
  "updated_at": "2025-11-29T11:15:00Z",
  "last_message_preview": "Here’s your daily briefing...",
  "pinned": false
}
```

**Chat message:**

```jsonc
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant", // "user" | "assistant" | "system"
  "content": "Here’s your daily briefing...",
  "model": "gpt-4.1-mini",
  "timestamp": "2025-11-29T11:05:12Z",

  // optional reference metadata for transparency
  "references": {
    "notes": [
      { "note_id": "uuid1", "title": "Daily Log 2025-11-29" }
    ],
    "tasks": [
      { "task_id": "uuid2", "title": "Review CRE parcels" }
    ],
    "events": [
      { "event_id": "uuid3", "title": "Client call – CRE data center scouting" }
    ]
  }
}
```

---

### 2.6 Embedding / ContextChunk

This is usually backend-only, but we’ll define it:

```jsonc
{
  "id": "uuid",
  "source_type": "note",     // "note" | "task" | ...
  "source_id": "uuid",
  "chunk_index": 0,
  "content": "First 512 tokens of the note...",
  "embedding": [0.001, -0.023, ...],
  "model": "text-embedding-3-large",
  "created_at": "2025-11-29T11:10:00Z"
}
```

---

### 2.7 SyncState

```jsonc
{
  "id": "uuid",
  "provider": "google_calendar",
  "last_sync": "2025-11-29T10:00:00Z",
  "sync_token": "opaque_google_sync_token",
  "metadata": {
    "calendar_ids": ["primary"],
    "status": "ok"
  }
}
```

---

### 2.8 Settings (single-user)

```jsonc
{
  "ai": {
    "openai_api_key": "sk-***",
    "chat_model": "gpt-4.1-mini",
    "embedding_model": "text-embedding-3-large"
  },
  "calendar": {
    "google_connected": true,
    "selected_calendars": ["primary"]
  },
  "dev": {
    "default_test_command": "pytest",
    "default_shell": "/bin/zsh"
  },
  "ui": {
    "theme": "system",  // "light" | "dark" | "system"
    "editor_font_size": 14
  }
}
```

(Stored as a single row in `settings` table with a JSON blob.)

---

## 3. Conceptual DB Schema

I’ll describe tables with rough SQL-ish types; you can translate to real migrations later.

### 3.1 `notes`

```sql
notes (
  id            TEXT PRIMARY KEY,    -- uuid
  title         TEXT NOT NULL,
  content       TEXT NOT NULL,
  tags          TEXT,                -- JSON-encoded array of strings
  created_at    TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP NOT NULL
);
```

Optional: FTS table `notes_fts` for full-text search.

---

### 3.2 `tasks`

```sql
tasks (
  id             TEXT PRIMARY KEY,
  title          TEXT NOT NULL,
  description    TEXT,
  status         TEXT NOT NULL,      -- todo | in_progress | done
  priority       TEXT NOT NULL,      -- low | medium | high
  due_date       TIMESTAMP,
  tags           TEXT,               -- JSON array
  source_note_id TEXT,               -- fk -> notes.id (nullable)
  source_line    INTEGER,
  project_id     TEXT,               -- fk -> projects.id (nullable)
  created_at     TIMESTAMP NOT NULL,
  completed_at   TIMESTAMP,
  CONSTRAINT fk_task_note FOREIGN KEY (source_note_id) REFERENCES notes(id),
  CONSTRAINT fk_task_project FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

Indexes:

* `CREATE INDEX idx_tasks_status ON tasks(status);`
* `CREATE INDEX idx_tasks_due_date ON tasks(due_date);`
* `CREATE INDEX idx_tasks_project ON tasks(project_id);`

---

### 3.3 `events`

```sql
events (
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
```

Link tables:

```sql
event_notes (
  event_id TEXT NOT NULL,
  note_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, note_id),
  FOREIGN KEY (event_id) REFERENCES events(id),
  FOREIGN KEY (note_id) REFERENCES notes(id)
);

event_tasks (
  event_id TEXT NOT NULL,
  task_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, task_id),
  FOREIGN KEY (event_id) REFERENCES events(id),
  FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

### 3.4 `projects`

```sql
projects (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  root_path  TEXT NOT NULL,
  type       TEXT NOT NULL,      -- code | general
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

project_notes (
  project_id TEXT NOT NULL,
  note_id    TEXT NOT NULL,
  PRIMARY KEY (project_id, note_id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

(Tasks already link directly via `tasks.project_id`, so no join table needed there.)

---

### 3.5 `conversations` & `chat_messages`

```sql
conversations (
  id                    TEXT PRIMARY KEY,
  title                 TEXT NOT NULL,
  created_at            TIMESTAMP NOT NULL,
  updated_at            TIMESTAMP NOT NULL,
  last_message_preview  TEXT,
  pinned                INTEGER NOT NULL DEFAULT 0   -- boolean
);

chat_messages (
  id              TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role            TEXT NOT NULL,      -- user | assistant | system
  content         TEXT NOT NULL,
  model           TEXT,
  timestamp       TIMESTAMP NOT NULL,
  references_json TEXT,               -- JSON: { notes: [...], tasks: [...], events: [...] }
  FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id);
```

---

### 3.6 `embeddings`

```sql
embeddings (
  id          TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,        -- note | task | ...
  source_id   TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content     TEXT NOT NULL,
  embedding   BLOB NOT NULL,        -- or TEXT for JSON array
  model       TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL
);

CREATE INDEX idx_embeddings_source ON embeddings(source_type, source_id);
```

(You might also add a vector index if you move to Postgres/pgvector later; for SQLite you’ll handle approximate search in app code.)

---

### 3.7 `sync_state`

```sql
sync_state (
  id         TEXT PRIMARY KEY,
  provider   TEXT NOT NULL,      -- google_calendar
  last_sync  TIMESTAMP,
  sync_token TEXT,
  metadata   TEXT                -- JSON blob
);
```

---

### 3.8 `settings`

For now: single row with JSON blob for everything.

```sql
settings (
  id       INTEGER PRIMARY KEY CHECK (id = 1),
  data     TEXT NOT NULL,      -- JSON (see settings JSON above)
  updated_at TIMESTAMP NOT NULL
);
```

(You can enforce a single row by always using `id = 1`.)

---

## 4. Relationships (mental model)

* **Note** 1—*many* **Task**
  via `tasks.source_note_id`.

* **Note** *many—many* **Note**
  via wiki-links/backlinks (can be derived from content, not stored).

* **Event** *many—many* **Note**
  via `event_notes`.

* **Event** *many—many* **Task**
  via `event_tasks`.

* **Project** 1—*many* **Task**
  via `tasks.project_id`.

* **Project** *many—many* **Note**
  via `project_notes`.

* **Conversation** 1—*many* **ChatMessage**
  via `chat_messages.conversation_id`.

* **Embedding** *many—1* (**Note** | **Task** | etc.)
  via `source_type`, `source_id`.

---

If this looks good to you, next logical step is:

* Either map these JSON shapes directly into **Pydantic models** (FastAPI layer),
* Or start drafting the **FastAPI endpoints** (Option B from before) using these as request/response contracts.

If you’d like, I can take one domain (e.g., Notes + Tasks) and turn it into concrete Pydantic models + CRUD endpoint signatures next.


Awesome, let’s turn the data model into a **clean FastAPI API surface**.

I’ll keep this at the **API design level** (routes, methods, payload shapes, how they map to features), not full implementation.

---

## 0. API Conventions

* **Base URL**: `http://localhost:PORT/api`
* **Format**: JSON in/out.
* **Auth**: local desktop app → no multi-user auth in v1.
* **Errors** (pattern):

  ```jsonc
  {
    "detail": "Not found",
    "error_code": "NOTE_NOT_FOUND"
  }
  ```
* **Pagination (where needed)**:

  * Query params: `limit`, `offset`
  * Response:

    ```jsonc
    {
      "items": [ /* ... */ ],
      "total": 42,
      "limit": 20,
      "offset": 0
    }
    ```

---

## 1. Notes API

### 1.1 List Notes

**GET `/notes`**

Query params:

* `q` — optional text query
* `tag` — optional filter by tag
* `limit`, `offset` — pagination
* `sort` — e.g. `updated_desc` (default)

**Response** (simplified):

```jsonc
{
  "items": [
    {
      "id": "uuid",
      "title": "Daily Log 2025-11-29",
      "tags": ["daily", "work"],
      "created_at": "...",
      "updated_at": "...",
      "task_count": { "total": 3, "open": 2, "done": 1 }
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### 1.2 Create Note

**POST `/notes`**

```jsonc
{
  "title": "Daily Log 2025-11-29",
  "content": "## Today\n- [ ] Finish API design",
  "tags": ["daily", "work"]
}
```

**Response**: full Note object.

---

### 1.3 Get Note

**GET `/notes/{note_id}`**

Returns full note including backlinks, derived fields.

---

### 1.4 Update Note

**PATCH `/notes/{note_id}`**

```jsonc
{
  "title": "Updated title (optional)",
  "content": "New markdown (optional)",
  "tags": ["work", "planning"]
}
```

Partial update; returns updated note.

---

### 1.5 Delete Note

**DELETE `/notes/{note_id}`**

204 on success.

---

### 1.6 Extract Tasks from Note

This ties Notes ↔ Tasks and also feeds the AI pipeline if needed.

**POST `/notes/{note_id}/extract-tasks`**

Body (optional config):

```jsonc
{
  "mode": "parse_only" // "parse_only" | "ai_assisted"
}
```

**Response**:

```jsonc
{
  "created_tasks": [ /* Task */ ],
  "updated_tasks": [ /* Task */ ]
}
```

---

### 1.7 Note Backlinks (optional explicit endpoint)

**GET `/notes/{note_id}/backlinks`**

```jsonc
{
  "items": [
    { "note_id": "uuid-2", "title": "Related Note" }
  ]
}
```

*(You can also just embed backlinks in `GET /notes/{id}`; this endpoint is just for editor UX if needed.)*

---

## 2. Tasks API

### 2.1 List Tasks

**GET `/tasks`**

Query params:

* `status` — `todo|in_progress|done|any`
* `overdue` — `true|false`
* `due_today` — `true|false`
* `project_id` — filter by Dev Workspace project
* `tag` — filter by tag
* `q` — search
* `limit`, `offset`

**Response**:

```jsonc
{
  "items": [ /* Task */ ],
  "total": 12,
  "limit": 50,
  "offset": 0
}
```

---

### 2.2 Create Task

**POST `/tasks`**

```jsonc
{
  "title": "Implement FastAPI models",
  "description": "Start with notes + tasks",
  "status": "todo",
  "priority": "high",
  "due_date": "2025-11-30T23:59:59Z",
  "tags": ["atlas"],
  "source_note_id": "uuid-or-null",
  "project_id": "uuid-or-null"
}
```

---

### 2.3 Get / Update / Delete Task

* **GET** `/tasks/{task_id}`
* **PATCH** `/tasks/{task_id}`

  ```jsonc
  {
    "title": "Optional",
    "status": "in_progress",
    "priority": "medium",
    "due_date": null,
    "project_id": "uuid-or-null"
  }
  ```
* **DELETE** `/tasks/{task_id}`

---

### 2.4 Bulk Update (nice-to-have)

**PATCH `/tasks/bulk`**

```jsonc
{
  "task_ids": ["uuid1", "uuid2"],
  "status": "done"
}
```

---

## 3. Events & Calendar API

### 3.1 List Events

**GET `/events`**

Query params:

* `start` — ISO timestamp
* `end` — ISO timestamp
* `source` — `local|google|any`
* `limit`, `offset`

Response: list of Event objects.

---

### 3.2 Create / Update / Delete Event

* **POST** `/events`
* **GET** `/events/{event_id}`
* **PATCH** `/events/{event_id}`
* **DELETE** `/events/{event_id}`

Create body:

```jsonc
{
  "title": "Client call",
  "description": "Discuss Atlas",
  "start_time": "2025-12-01T14:00:00Z",
  "end_time": "2025-12-01T15:00:00Z",
  "location": "Zoom",
  "source": "local"
}
```

---

### 3.3 Link Notes/Tasks to Event

Two flavors (pick one style or both):

**POST `/events/{event_id}/links`**

```jsonc
{
  "notes": ["note-id-1", "note-id-2"],
  "tasks": ["task-id-1"]
}
```

**or explicit endpoints:**

* `POST /events/{event_id}/notes/{note_id}`
* `POST /events/{event_id}/tasks/{task_id}`
* `DELETE` variants to unlink.

---

### 3.4 Google Calendar Integration

**Start OAuth flow** (desktop flow is tricky, but API-wise):

* **GET `/calendar/google/auth-url`**

  * Returns URL to open in browser.

* **POST `/calendar/google/callback`**

  * Called by Electron after capturing code/redirect.

  ```jsonc
  {
    "code": "oauth-code"
  }
  ```

**Sync endpoint:**

* **POST `/calendar/google/sync`**

  * Body:

    ```jsonc
    {
      "calendar_ids": ["primary"]
    }
    ```
  * Response:

    ```jsonc
    {
      "synced_events": 42,
      "last_sync": "2025-11-29T10:03:00Z",
      "status": "ok"
    }
    ```

---

## 4. Projects (Dev Workspace) API

### 4.1 List / Create Projects

* **GET `/projects`**
* **POST `/projects`**

  ```jsonc
  {
    "name": "Atlas Desktop",
    "root_path": "/Users/josh/Projects/atlas-desktop",
    "type": "code"
  }
  ```

---

### 4.2 Get / Update / Delete Project

* **GET** `/projects/{project_id}`
* **PATCH** `/projects/{project_id}`

  ```jsonc
  {
    "name": "Atlas Desktop (v1)",
    "root_path": "/new/path"
  }
  ```
* **DELETE** `/projects/{project_id}`

---

### 4.3 Project ↔ Notes Links

**POST `/projects/{project_id}/notes`**

```jsonc
{
  "note_ids": ["note-id-1", "note-id-2"]
}
```

**DELETE `/projects/{project_id}/notes/{note_id}`**

---

### 4.4 Project Summary for Dev Workspace

**GET `/projects/{project_id}/summary`**

Returns:

```jsonc
{
  "project": { /* Project */ },
  "linked_notes": [ /* Note summary */ ],
  "linked_tasks": [ /* Task summary */ ]
}
```

This powers the Dev Workspace sidebar.

---

## 5. Conversations & Chat API

### 5.1 List / Create Conversations

* **GET `/conversations`**

  * Query:

    * `limit`, `offset`
    * `pinned=true|false` (optional)
* **POST `/conversations`**

  ```jsonc
  {
    "title": "Daily planning – 2025-11-29"
  }
  ```

---

### 5.2 Get / Update / Delete Conversation

* **GET** `/conversations/{conversation_id}`
* **PATCH** `/conversations/{conversation_id}`

  ```jsonc
  {
    "title": "Renamed conversation",
    "pinned": true
  }
  ```
* **DELETE** `/conversations/{conversation_id}`

---

### 5.3 List Messages in Conversation

**GET `/conversations/{conversation_id}/messages`**

Query: `limit`, `offset` (for infinite scroll).

---

### 5.4 Send Message (and get AI reply)

**POST `/conversations/{conversation_id}/messages`**

```jsonc
{
  "role": "user",
  "content": "Can you give me a daily briefing for today?",
  "options": {
    "include_context": true,
    "context_types": ["notes", "tasks", "events"]
  }
}
```

**Response (non-streaming):**

```jsonc
{
  "messages": [
    { "id": "uuid-user", "role": "user", "content": "..." },
    { "id": "uuid-assistant", "role": "assistant", "content": "Here’s your briefing...", "references": { /* ... */ } }
  ]
}
```

For **streaming**, you’ll likely have:

* WebSocket: `GET /ws/conversations/{conversation_id}`
  or
* SSE: `GET /conversations/{conversation_id}/stream`

…but at the API-design level, the main thing is: messages go through this one endpoint; the server handles OpenAI calls and message persistence.

---

## 6. AI Utility Endpoints

These are “shortcuts” that do specific jobs without going through the general chat interface (though internally they may reuse the same logic).

### 6.1 Daily Briefing

**POST `/ai/daily-briefing`**

```jsonc
{
  "date": "2025-11-29",
  "options": {
    "include_overdue_tasks": true,
    "include_events": true,
    "include_recent_notes": true
  }
}
```

Response:

```jsonc
{
  "markdown": "## Daily Briefing\n...",
  "references": {
    "tasks": [...],
    "events": [...],
    "notes": [...]
  }
}
```

---

### 6.2 Summarize Note

**POST `/ai/summarize-note`**

```jsonc
{
  "note_id": "uuid",
  "include_action_items": true
}
```

Response:

```jsonc
{
  "summary": "Short TL;DR...",
  "action_items": [
    { "title": "Follow up with X", "suggested_due_date": "2025-12-01" }
  ]
}
```

---

### 6.3 Extract Tasks (AI-Assisted)

You can either reuse `/notes/{id}/extract-tasks` or have a generic endpoint:

**POST `/ai/extract-tasks`**

```jsonc
{
  "note_id": "uuid"
}
```

Response: same shape as the note endpoint version.

---

### 6.4 Semantic Search (“Ask about my notes”)

**POST `/ai/search`**

```jsonc
{
  "query": "What did I decide about the CRE data center power requirements?",
  "types": ["notes", "tasks"],
  "limit": 10
}
```

Response:

```jsonc
{
  "matches": [
    {
      "source_type": "note",
      "source_id": "uuid",
      "score": 0.89,
      "snippet": "We need at least..."
    }
  ]
}
```

Optionally a **follow-up** endpoint:

**POST `/ai/answer-from-search`**

```jsonc
{
  "query": "Same question...",
  "matches": [ /* from above */ ]
}
```

Or just collapse that into one endpoint that does retrieval + answer.

---

### 6.5 Dev Assistant (code-focused)

**POST `/ai/dev/assist`**

```jsonc
{
  "project_id": "uuid",
  "mode": "explain_code", // or "suggest_refactor", "generate_tests", ...
  "file_path": "src/app/main.py",
  "code": "def foo(): ...", // (editor sends current buffer)
  "selection": {
    "start_line": 10,
    "end_line": 30
  },
  "terminal_output": "pytest failed with ... (optional)"
}
```

Response:

```jsonc
{
  "message": "The issue is that...",
  "suggested_changes": "diff or patch text",
  "suggested_commands": ["pytest -k test_foo"]
}
```

The Dev Workspace UI can then show suggestions, diffs, and commands without auto-running them.

---

## 7. Search API (Non-AI)

### 7.1 Text Search

**GET `/search`**

Query params:

* `q` — text
* `type` — `notes|tasks|all`
* `limit`, `offset`

Response: list of lightweight matches.

---

## 8. Settings API

### 8.1 Get Settings

**GET `/settings`**

Returns the settings JSON blob.

---

### 8.2 Update Settings

**PUT `/settings`**

```jsonc
{
  "ai": {
    "openai_api_key": "sk-***",
    "chat_model": "gpt-4.1-mini"
  },
  "calendar": {
    "selected_calendars": ["primary"]
  },
  "dev": {
    "default_test_command": "pytest"
  },
  "ui": {
    "theme": "dark"
  }
}
```

Backend merges/validates and persists.

---

## 9. Dashboard API

### 9.1 Today Overview

**GET `/dashboard/today`**

Query param:

* `date` — optional (default = today)

Response:

```jsonc
{
  "date": "2025-11-29",
  "tasks": {
    "overdue": [ /* Task summary */ ],
    "due_today": [ /* Task summary */ ]
  },
  "events": [ /* Events happening today */ ],
  "recent_notes": [ /* Recent notes */ ]
}
```

The frontend can augment this with AI-generated briefing via `/ai/daily-briefing`.

---

## Where this leaves us

We now have:

* A **clear mapping** from v1 features → routes/methods.
* Endpoints grouped by domain:

  * `/notes`, `/tasks`, `/events`, `/projects`, `/conversations`, `/ai`, `/settings`, `/dashboard`.
* Special AI endpoints for:

  * Chat
  * Daily briefing
  * Note summarization
  * Task extraction
  * Semantic search
  * Dev assistant

---

**Next step options:**

1. **Turn these into concrete FastAPI route stubs** (Pydantic models + routers).
2. **Design Electron view → API interactions** (which screens call which endpoints, and when).
3. **Design the AI orchestration** in a bit more detail (OpenAI calls, retrieval flow, model choices).

If you want, I can take, say, **Notes + Tasks + Conversations** and write out real FastAPI router skeletons (with Pydantic models) that match this API design.
