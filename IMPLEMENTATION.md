# Cortex Atlas - Technical Implementation Guide

> Comprehensive technical implementation details for the Atlas local-first personal OS

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Technology Stack](#2-technology-stack)
3. [Database Implementation](#3-database-implementation)
4. [Backend Implementation (FastAPI)](#4-backend-implementation-fastapi)
5. [Electron Application](#5-electron-application)
6. [AI Service Layer](#6-ai-service-layer)
7. [Development Workflow](#7-development-workflow)
8. [Security Considerations](#8-security-considerations)
9. [Build & Deployment](#9-build--deployment)

---

## 1. System Architecture

### 1.1 Process Model

Atlas runs as three coordinated processes:

```
┌─────────────────────────────────────────────────────────┐
│                    Electron App                          │
│  ┌────────────────┐         ┌─────────────────────────┐ │
│  │  Main Process  │◄───────►│  Renderer (React/TS)    │ │
│  │                │   IPC   │                         │ │
│  │  - Window mgmt │         │  - UI Components        │ │
│  │  - Backend     │         │  - API Client           │ │
│  │    startup     │         │  - Dev Workspace UI     │ │
│  │  - Terminal    │         │                         │ │
│  │  - File I/O    │         │                         │ │
│  └────────┬───────┘         └──────────┬──────────────┘ │
│           │                            │                 │
└───────────┼────────────────────────────┼─────────────────┘
            │                            │
            │ Child Process              │ HTTP/WebSocket
            │                            │
            ▼                            ▼
    ┌───────────────────────────────────────────┐
    │       FastAPI Backend (Python)             │
    │                                            │
    │  ├─ API Routes (/notes, /tasks, etc.)     │
    │  ├─ AI Service Layer                      │
    │  ├─ Database (SQLite)                     │
    │  ├─ OpenAI Integration                    │
    │  └─ Google Calendar Sync                  │
    │                                            │
    │  Port: 127.0.0.1:4100                     │
    └───────────────────────────────────────────┘
```

### 1.2 Communication Patterns

**Renderer → FastAPI (HTTP/WebSocket)**
- All domain data operations (notes, tasks, events, projects)
- AI chat and assistant features
- Settings and configuration
- Search and embeddings

**Renderer → Main (IPC via Preload)**
- File system operations (read/write project files)
- Folder selection dialogs
- Terminal process management
- OS-level integrations

---

## 2. Technology Stack

### 2.1 Frontend Stack

```json
{
  "runtime": "Electron 28+",
  "ui-framework": "React 18+",
  "language": "TypeScript 5+",
  "build-tool": "Vite",
  "router": "React Router 6",
  "state": "React Context + Custom Hooks",
  "editor": "Monaco Editor or CodeMirror",
  "terminal": "xterm.js",
  "markdown": "react-markdown + remark/rehype",
  "styling": "Tailwind CSS or styled-components"
}
```

### 2.2 Backend Stack

```json
{
  "framework": "FastAPI 0.104+",
  "language": "Python 3.11+",
  "server": "uvicorn",
  "database": "SQLite 3.42+",
  "orm": "SQLAlchemy 2.0+ or raw SQL",
  "ai-client": "openai 1.3+",
  "calendar": "google-api-python-client",
  "auth": "google-auth-oauthlib",
  "migrations": "alembic (optional for v1)"
}
```

### 2.3 AI & Embeddings

```json
{
  "chat-model-default": "gpt-4.1-mini",
  "chat-model-heavy": "gpt-4.1",
  "embedding-model": "text-embedding-3-large",
  "vector-search": "In-memory (NumPy/cosine) for v1"
}
```

---

## 3. Database Implementation

### 3.1 Schema Overview

**Core Tables:**
- `notes` - Markdown notes with wiki-links
- `tasks` - Actionable items linked to notes/projects
- `events` - Calendar events (local + synced)
- `projects` - Dev workspace projects
- `conversations` - AI chat threads
- `chat_messages` - Individual messages in conversations
- `embeddings` - Vector embeddings for semantic search
- `sync_state` - Sync status for external services
- `settings` - Application configuration (single row JSON blob)

**Join Tables:**
- `event_notes` - Many-to-many: events ↔ notes
- `event_tasks` - Many-to-many: events ↔ tasks
- `project_notes` - Many-to-many: projects ↔ notes

### 3.2 Complete Schema (SQLite)

```sql
-- Notes
CREATE TABLE notes (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  content       TEXT NOT NULL,
  tags          TEXT,                -- JSON array: ["tag1", "tag2"]
  created_at    TIMESTAMP NOT NULL,
  updated_at    TIMESTAMP NOT NULL
);

-- Full-text search index
CREATE VIRTUAL TABLE notes_fts USING fts5(
  title,
  content,
  content=notes,
  content_rowid=rowid
);

-- Tasks
CREATE TABLE tasks (
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

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_project ON tasks(project_id);

-- Events
CREATE TABLE events (
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

CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_source ON events(source);

-- Event Links
CREATE TABLE event_notes (
  event_id TEXT NOT NULL,
  note_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, note_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE event_tasks (
  event_id TEXT NOT NULL,
  task_id  TEXT NOT NULL,
  PRIMARY KEY (event_id, task_id),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Projects (Dev Workspace)
CREATE TABLE projects (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  root_path  TEXT NOT NULL,
  type       TEXT NOT NULL,      -- code | general
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE project_notes (
  project_id TEXT NOT NULL,
  note_id    TEXT NOT NULL,
  PRIMARY KEY (project_id, note_id),
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

-- Conversations & Messages
CREATE TABLE conversations (
  id                    TEXT PRIMARY KEY,
  title                 TEXT NOT NULL,
  created_at            TIMESTAMP NOT NULL,
  updated_at            TIMESTAMP NOT NULL,
  last_message_preview  TEXT,
  pinned                INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE chat_messages (
  id              TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  role            TEXT NOT NULL,      -- user | assistant | system
  content         TEXT NOT NULL,
  model           TEXT,
  timestamp       TIMESTAMP NOT NULL,
  references_json TEXT,               -- JSON: { notes: [...], tasks: [...] }
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id);

-- Embeddings
CREATE TABLE embeddings (
  id          TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,        -- note | task
  source_id   TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content     TEXT NOT NULL,
  embedding   BLOB NOT NULL,        -- Serialized float array
  model       TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL
);

CREATE INDEX idx_embeddings_source ON embeddings(source_type, source_id);

-- Sync State
CREATE TABLE sync_state (
  id         TEXT PRIMARY KEY,
  provider   TEXT NOT NULL,      -- google_calendar
  last_sync  TIMESTAMP,
  sync_token TEXT,
  metadata   TEXT                -- JSON blob
);

-- Settings (single row)
CREATE TABLE settings (
  id         INTEGER PRIMARY KEY CHECK (id = 1),
  data       TEXT NOT NULL,      -- JSON blob
  updated_at TIMESTAMP NOT NULL
);
```

### 3.3 Data Conventions

- **IDs**: UUID v4 as TEXT
- **Timestamps**: ISO 8601 format with timezone
- **JSON Fields**: Stored as TEXT, validated in application layer
- **Tags**: JSON arrays of strings
- **Embeddings**: Pickled NumPy arrays or JSON arrays stored as BLOB

---

## 4. Backend Implementation (FastAPI)

### 4.1 Project Structure

```
backend/
├── atlas_api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings, env vars
│   ├── database.py             # DB connection, session management
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── note.py
│   │   ├── task.py
│   │   ├── event.py
│   │   ├── project.py
│   │   ├── conversation.py
│   │   └── settings.py
│   │
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── notes.py
│   │   ├── tasks.py
│   │   ├── events.py
│   │   ├── projects.py
│   │   ├── conversations.py
│   │   ├── ai.py
│   │   ├── search.py
│   │   ├── settings.py
│   │   └── dashboard.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── note_service.py
│   │   ├── task_service.py
│   │   ├── event_service.py
│   │   ├── calendar_sync.py
│   │   └── search_service.py
│   │
│   ├── ai/                     # AI service layer
│   │   ├── __init__.py
│   │   ├── client.py           # OpenAI client wrapper
│   │   ├── retrieval.py        # Embeddings & vector search
│   │   ├── prompts.py          # Prompt templates
│   │   └── orchestrator.py     # High-level AI flows
│   │
│   └── db/
│       ├── schema.sql
│       └── migrations/
│
├── pyproject.toml
└── uvicorn_entry.py            # Server startup script
```

### 4.2 Core API Routes

**Base URL**: `http://127.0.0.1:4100/api`

#### Notes

```python
# routers/notes.py
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("")
async def list_notes(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort: str = "updated_desc"
):
    """List notes with optional filters"""
    pass

@router.post("")
async def create_note(note: NoteCreate):
    """Create a new note"""
    pass

@router.get("/{note_id}")
async def get_note(note_id: str):
    """Get a single note with backlinks and derived fields"""
    pass

@router.patch("/{note_id}")
async def update_note(note_id: str, update: NoteUpdate):
    """Partial update of a note"""
    pass

@router.delete("/{note_id}")
async def delete_note(note_id: str):
    """Delete a note"""
    pass

@router.post("/{note_id}/extract-tasks")
async def extract_tasks(note_id: str, mode: str = "parse_only"):
    """Extract tasks from note content"""
    pass
```

#### Tasks

```python
# routers/tasks.py
@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    overdue: bool = False,
    due_today: bool = False,
    project_id: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    pass

@router.post("/tasks")
async def create_task(task: TaskCreate):
    pass

@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, update: TaskUpdate):
    pass

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    pass
```

#### AI Endpoints

```python
# routers/ai.py
@router.post("/ai/daily-briefing")
async def daily_briefing(req: DailyBriefingRequest):
    """Generate AI-powered daily briefing"""
    pass

@router.post("/ai/summarize-note")
async def summarize_note(req: SummarizeNoteRequest):
    """Generate note summary and action items"""
    pass

@router.post("/ai/search")
async def semantic_search(req: SemanticSearchRequest):
    """Semantic search across notes/tasks"""
    pass

@router.post("/ai/dev/assist")
async def dev_assist(req: DevAssistRequest):
    """Dev workspace AI assistance"""
    pass
```

#### Conversations

```python
# routers/conversations.py
@router.get("/conversations")
async def list_conversations(limit: int = 20, offset: int = 0):
    pass

@router.post("/conversations")
async def create_conversation(conv: ConversationCreate):
    pass

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, limit: int = 50, offset: int = 0):
    pass

@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, msg: MessageCreate):
    """Send user message and get AI response"""
    pass

# WebSocket for streaming
@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_stream(websocket: WebSocket, conversation_id: str):
    pass
```

### 4.3 Pydantic Models Example

```python
# models/note.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: str
    tags: List[str] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class NoteTaskCount(BaseModel):
    total: int
    open: int
    done: int

class Backlink(BaseModel):
    note_id: str
    title: str

class Note(NoteBase):
    id: str
    created_at: datetime
    updated_at: datetime
    links: List[str] = []           # Wiki-link titles
    backlinks: List[Backlink] = []
    task_count: NoteTaskCount

    class Config:
        from_attributes = True
```

### 4.4 Main Application Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import (
    notes, tasks, events, projects,
    conversations, ai, search, settings, dashboard
)
from .database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Atlas API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Register routers
app.include_router(notes.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
```

---

## 5. Electron Application

### 5.1 Project Structure

```
app/
├── electron/
│   ├── main.ts                 # Main process entry
│   ├── preload.ts              # Preload script
│   ├── backendProcess.ts       # FastAPI lifecycle
│   ├── terminalManager.ts      # Terminal process management
│   └── ipcHandlers.ts          # IPC handler implementations
│
└── renderer/
    ├── src/
    │   ├── main.tsx            # React entry point
    │   ├── App.tsx             # Root component
    │   │
    │   ├── routes/             # Page components
    │   │   ├── Dashboard.tsx
    │   │   ├── Notes.tsx
    │   │   ├── Tasks.tsx
    │   │   ├── Calendar.tsx
    │   │   ├── DevWorkspace.tsx
    │   │   └── Settings.tsx
    │   │
    │   ├── components/         # Reusable components
    │   │   ├── Layout/
    │   │   │   ├── Sidebar.tsx
    │   │   │   ├── TopBar.tsx
    │   │   │   └── ChatPanel.tsx
    │   │   ├── Notes/
    │   │   │   ├── NoteEditor.tsx
    │   │   │   ├── NoteList.tsx
    │   │   │   └── BacklinksPanel.tsx
    │   │   ├── Tasks/
    │   │   │   ├── TaskList.tsx
    │   │   │   └── TaskCard.tsx
    │   │   ├── Calendar/
    │   │   │   └── CalendarView.tsx
    │   │   └── Dev/
    │   │       ├── FileTree.tsx
    │   │       ├── CodeEditor.tsx
    │   │       └── TerminalView.tsx
    │   │
    │   ├── lib/                # Utilities & hooks
    │   │   ├── apiClient.ts    # HTTP client for FastAPI
    │   │   ├── useApi.ts       # React hook for API calls
    │   │   ├── useChatStream.ts
    │   │   └── useDevWorkspace.ts
    │   │
    │   └── types/              # TypeScript definitions
    │       ├── api.ts
    │       └── electron.d.ts
    │
    ├── index.html
    └── vite.config.ts
```

### 5.2 Main Process Implementation

```typescript
// electron/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { startBackend, stopBackend, waitForHealth } from './backendProcess';
import { registerIpcHandlers } from './ipcHandlers';

let mainWindow: BrowserWindow | null = null;

async function createWindow() {
  // Start FastAPI backend
  console.log('Starting backend...');
  await startBackend();
  await waitForHealth('http://127.0.0.1:4100/health', 30000);
  console.log('Backend ready');

  // Create browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  // Load renderer
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  registerIpcHandlers();
  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
```

### 5.3 Backend Process Manager

```typescript
// electron/backendProcess.ts
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

let backendProcess: ChildProcess | null = null;

export async function startBackend(): Promise<void> {
  const pythonPath = 'python3'; // Or bundled Python path
  const scriptPath = path.join(__dirname, '../../backend/uvicorn_entry.py');

  backendProcess = spawn(pythonPath, [scriptPath, '--port', '4100'], {
    cwd: path.join(__dirname, '../../backend'),
    env: { ...process.env }
  });

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend Error] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend exited with code ${code}`);
  });
}

export function stopBackend(): void {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

export async function waitForHealth(
  url: string,
  timeout: number = 30000
): Promise<void> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch (e) {
      // Not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  throw new Error('Backend health check timeout');
}
```

### 5.4 Preload Script

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('atlas', {
  // File dialogs
  selectProjectRoot: () => ipcRenderer.invoke('dialog:selectProjectRoot'),

  // Dev workspace - File operations
  dev: {
    readDir: (projectId: string, relPath: string) =>
      ipcRenderer.invoke('dev:readDir', { projectId, relPath }),

    readFile: (projectId: string, filePath: string) =>
      ipcRenderer.invoke('dev:readFile', { projectId, filePath }),

    writeFile: (projectId: string, filePath: string, content: string) =>
      ipcRenderer.invoke('dev:writeFile', { projectId, filePath, content })
  },

  // Terminal
  terminal: {
    start: (projectId: string) =>
      ipcRenderer.invoke('terminal:start', { projectId }),

    send: (terminalId: string, data: string) =>
      ipcRenderer.invoke('terminal:send', { terminalId, data }),

    onData: (callback: (payload: any) => void) =>
      ipcRenderer.on('terminal:data', (_event, payload) => callback(payload)),

    stop: (terminalId: string) =>
      ipcRenderer.send('terminal:stop', { terminalId }),

    resize: (terminalId: string, cols: number, rows: number) =>
      ipcRenderer.invoke('terminal:resize', { terminalId, cols, rows })
  }
});

// Type definitions for renderer
export interface AtlasAPI {
  selectProjectRoot: () => Promise<string | null>;
  dev: {
    readDir: (projectId: string, relPath: string) => Promise<FileEntry[]>;
    readFile: (projectId: string, filePath: string) => Promise<string>;
    writeFile: (projectId: string, filePath: string, content: string) => Promise<void>;
  };
  terminal: {
    start: (projectId: string) => Promise<{ terminalId: string }>;
    send: (terminalId: string, data: string) => Promise<void>;
    onData: (callback: (payload: any) => void) => void;
    stop: (terminalId: string) => void;
    resize: (terminalId: string, cols: number, rows: number) => Promise<void>;
  };
}

declare global {
  interface Window {
    atlas: AtlasAPI;
  }
}
```

### 5.5 IPC Handlers

```typescript
// electron/ipcHandlers.ts
import { ipcMain, dialog } from 'electron';
import * as fs from 'fs/promises';
import * as path from 'path';
import { startTerminal, sendToTerminal, stopTerminal } from './terminalManager';

export function registerIpcHandlers() {
  // File dialog
  ipcMain.handle('dialog:selectProjectRoot', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // Dev workspace file operations
  ipcMain.handle('dev:readDir', async (_event, { projectId, relPath }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, relPath);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    return entries.map(entry => ({
      name: entry.name,
      isDir: entry.isDirectory()
    }));
  });

  ipcMain.handle('dev:readFile', async (_event, { projectId, filePath }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, filePath);
    return await fs.readFile(fullPath, 'utf-8');
  });

  ipcMain.handle('dev:writeFile', async (_event, { projectId, filePath, content }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, filePath);
    await fs.writeFile(fullPath, content, 'utf-8');
  });

  // Terminal
  ipcMain.handle('terminal:start', async (_event, { projectId }) => {
    const projectRoot = await getProjectRoot(projectId);
    const terminalId = await startTerminal(projectRoot);
    return { terminalId };
  });

  ipcMain.handle('terminal:send', async (_event, { terminalId, data }) => {
    sendToTerminal(terminalId, data);
  });

  ipcMain.on('terminal:stop', (_event, { terminalId }) => {
    stopTerminal(terminalId);
  });
}

async function getProjectRoot(projectId: string): Promise<string> {
  // Fetch from FastAPI or cache
  const response = await fetch(`http://127.0.0.1:4100/api/projects/${projectId}`);
  const project = await response.json();
  return project.root_path;
}
```

### 5.6 Terminal Manager

```typescript
// electron/terminalManager.ts
import { spawn } from 'node-pty';
import { BrowserWindow } from 'electron';
import { v4 as uuidv4 } from 'uuid';

interface Terminal {
  id: string;
  pty: any;
  cwd: string;
}

const terminals = new Map<string, Terminal>();

export function startTerminal(cwd: string): string {
  const terminalId = uuidv4();

  const shell = process.platform === 'win32' ? 'powershell.exe' : '/bin/zsh';

  const ptyProcess = spawn(shell, [], {
    name: 'xterm-color',
    cols: 80,
    rows: 24,
    cwd,
    env: process.env as any
  });

  ptyProcess.onData((data: string) => {
    // Send data to renderer
    const mainWindow = BrowserWindow.getAllWindows()[0];
    mainWindow?.webContents.send('terminal:data', {
      terminalId,
      data
    });
  });

  terminals.set(terminalId, {
    id: terminalId,
    pty: ptyProcess,
    cwd
  });

  return terminalId;
}

export function sendToTerminal(terminalId: string, data: string): void {
  const terminal = terminals.get(terminalId);
  if (terminal) {
    terminal.pty.write(data);
  }
}

export function stopTerminal(terminalId: string): void {
  const terminal = terminals.get(terminalId);
  if (terminal) {
    terminal.pty.kill();
    terminals.delete(terminalId);
  }
}
```

### 5.7 React API Client

```typescript
// renderer/src/lib/apiClient.ts
const API_BASE = 'http://127.0.0.1:4100/api';

class ApiClient {
  private async request<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Notes
  async getNotes(params?: {
    q?: string;
    tag?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/notes?${query}`);
  }

  async createNote(note: { title: string; content: string; tags?: string[] }) {
    return this.request('/notes', {
      method: 'POST',
      body: JSON.stringify(note)
    });
  }

  async updateNote(id: string, update: Partial<any>) {
    return this.request(`/notes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(update)
    });
  }

  // Tasks
  async getTasks(params?: {
    status?: string;
    overdue?: boolean;
    project_id?: string;
  }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/tasks?${query}`);
  }

  async createTask(task: any) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(task)
    });
  }

  // Conversations
  async sendMessage(conversationId: string, content: string, options?: any) {
    return this.request(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        role: 'user',
        content,
        options
      })
    });
  }

  // AI
  async getDailyBriefing(date: string, options?: any) {
    return this.request('/ai/daily-briefing', {
      method: 'POST',
      body: JSON.stringify({ date, options })
    });
  }
}

export const api = new ApiClient();
```

---

## 6. AI Service Layer

### 6.1 AI Module Structure

```
backend/atlas_api/ai/
├── __init__.py
├── client.py          # OpenAI client wrapper
├── retrieval.py       # Embeddings & vector search
├── prompts.py         # Prompt templates
└── orchestrator.py    # High-level AI flows
```

### 6.2 OpenAI Client Wrapper

```python
# ai/client.py
from openai import OpenAI
from typing import List, Dict, Optional
import os

class AtlasAIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.chat_model = "gpt-4.1-mini"
        self.heavy_model = "gpt-4.1"
        self.embedding_model = "text-embedding-3-large"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ):
        """Send chat completion request"""
        response = self.client.chat.completions.create(
            model=model or self.chat_model,
            messages=messages,
            temperature=temperature,
            stream=stream
        )

        if stream:
            return response
        else:
            return response.choices[0].message.content

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
```

### 6.3 Retrieval Service

```python
# ai/retrieval.py
import numpy as np
from typing import List, Dict, Tuple
from ..database import get_db

class RetrievalService:
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def chunk_text(self, text: str, chunk_size: int = 800) -> List[str]:
        """Split text into chunks for embedding"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1

            if current_length >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def embed_note(self, note_id: str, content: str):
        """Generate and store embeddings for a note"""
        chunks = self.chunk_text(content)
        embeddings = self.ai_client.embed_batch(chunks)

        db = get_db()
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db.execute("""
                INSERT INTO embeddings
                (id, source_type, source_id, chunk_index, content, embedding, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                f"{note_id}-{idx}",
                "note",
                note_id,
                idx,
                chunk,
                np.array(embedding).tobytes(),
                self.ai_client.embedding_model
            ))
        db.commit()

    def search(
        self,
        query: str,
        source_types: List[str] = ["note"],
        limit: int = 10
    ) -> List[Dict]:
        """Semantic search across embeddings"""
        query_embedding = np.array(self.ai_client.embed(query))

        db = get_db()
        results = db.execute("""
            SELECT source_type, source_id, chunk_index, content, embedding
            FROM embeddings
            WHERE source_type IN ({})
        """.format(','.join(['?' for _ in source_types])), source_types).fetchall()

        # Compute cosine similarity
        scored_results = []
        for row in results:
            chunk_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            scored_results.append({
                'source_type': row['source_type'],
                'source_id': row['source_id'],
                'chunk_index': row['chunk_index'],
                'content': row['content'],
                'score': float(similarity)
            })

        # Sort by score and return top N
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results[:limit]
```

### 6.4 Prompt Templates

```python
# ai/prompts.py

SYSTEM_PROMPT = """You are Atlas, a local-first personal knowledge and productivity assistant.

You have access to the user's notes, tasks, calendar, and (optionally) coding projects.
Always:
- Prefer concrete, actionable suggestions.
- When referencing notes/tasks/events, mention them explicitly.
- If some information is not present in the provided context, say you don't know rather than inventing details.
"""

DAILY_BRIEFING_PROMPT = """The user wants a concise daily briefing for {date}.
You are given:
- A list of overdue tasks
- A list of tasks due today
- A list of events scheduled today
- A list of recent notes with brief excerpts

1. Start with a short greeting and a one-sentence overview.
2. List the top 3–5 priorities as bullets, referencing task titles.
3. Mention today's events with times.
4. Optionally highlight any important themes from recent notes.

Return your output as Markdown with headings:
- "## Overview"
- "## Top Priorities"
- "## Today's Schedule"
- "## Notes to Review" (optional)

Context:
{context}
"""

NOTE_SUMMARY_PROMPT = """The user wrote the following note titled "{title}".

1. Produce a concise summary in 2–4 bullet points.
2. Identify any clear action items in the note. For each, return:
   - A short title
   - Optional due date if explicitly mentioned (otherwise null)

Return JSON with this shape:
{{
  "summary": ["bullet 1", "bullet 2", ...],
  "action_items": [
    {{ "title": "...", "due_date": "YYYY-MM-DD or null" }}
  ]
}}

Note content:
{content}
"""

SEMANTIC_QA_PROMPT = """The user asked:
"{query}"

You are given excerpts from their personal notes and tasks that may be relevant. Each excerpt shows a title and content.

1. Use only the information in these excerpts to answer the question.
2. If important details are missing, say that clearly.
3. At the end, list which notes/tasks you used by title.

Excerpts:
{context}
"""

DEV_EXPLAIN_CODE_PROMPT = """You are a senior software engineer helping the user understand code in their local project "{project_name}".

File: `{file_path}`

Code:
```{lang}
{code}
```

The user is focused on lines {start_line}–{end_line}.

1. Explain what this code does in clear language.
2. Mention any potential pitfalls or edge cases.
3. Suggest 1–2 possible improvements, but do not rewrite the entire file.
"""

DEV_REFACTOR_PROMPT = """Suggest a refactor for the selected region.
Focus on readability and maintainability.
Return your answer as:
- A short explanation
- A code block with the **refactored version of only the selected part**, preserving API behavior.
"""

DEV_TERMINAL_PROMPT = """The user ran a command in their project and got the following terminal output:

```txt
{terminal_output}
```

1. Explain what went wrong.
2. Suggest up to 3 specific things they can try next.
3. If relevant, include 1–2 example commands they might run.
"""
```

### 6.5 Orchestrator

```python
# ai/orchestrator.py
from typing import Dict, Any, List
from .client import AtlasAIClient
from .retrieval import RetrievalService
from .prompts import *
import json

class AIOrchestrator:
    def __init__(self, ai_client: AtlasAIClient):
        self.client = ai_client
        self.retrieval = RetrievalService(ai_client)

    def generate_daily_briefing(
        self,
        date: str,
        tasks: List[Dict],
        events: List[Dict],
        notes: List[Dict]
    ) -> Dict[str, Any]:
        """Generate AI-powered daily briefing"""

        # Build context
        context_parts = []

        if tasks:
            context_parts.append("## Tasks")
            for task in tasks:
                context_parts.append(f"- [{task['status']}] {task['title']}")

        if events:
            context_parts.append("\n## Events")
            for event in events:
                context_parts.append(
                    f"- {event['start_time']} - {event['title']}"
                )

        if notes:
            context_parts.append("\n## Recent Notes")
            for note in notes:
                context_parts.append(f"- {note['title']}: {note.get('preview', '')}")

        context = '\n'.join(context_parts)

        # Generate briefing
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": DAILY_BRIEFING_PROMPT.format(
                date=date,
                context=context
            )}
        ]

        markdown = self.client.chat(messages)

        return {
            "markdown": markdown,
            "references": {
                "tasks": [{"task_id": t["id"], "title": t["title"]} for t in tasks],
                "events": [{"event_id": e["id"], "title": e["title"]} for e in events],
                "notes": [{"note_id": n["id"], "title": n["title"]} for n in notes]
            }
        }

    def summarize_note(
        self,
        note_id: str,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """Generate note summary and extract action items"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": NOTE_SUMMARY_PROMPT.format(
                title=title,
                content=content
            )}
        ]

        response = self.client.chat(messages)
        return json.loads(response)

    def dev_assist(
        self,
        mode: str,
        project_name: str,
        file_path: str,
        code: str,
        selection: Dict[str, int] = None,
        terminal_output: str = None
    ) -> Dict[str, Any]:
        """Dev workspace AI assistance"""

        if mode == "explain_code":
            prompt = DEV_EXPLAIN_CODE_PROMPT.format(
                project_name=project_name,
                file_path=file_path,
                code=code,
                lang=self._detect_language(file_path),
                start_line=selection.get('start_line', 1) if selection else 1,
                end_line=selection.get('end_line', 1) if selection else 1
            )
        elif mode == "interpret_terminal":
            prompt = DEV_TERMINAL_PROMPT.format(
                terminal_output=terminal_output
            )
        else:
            prompt = "Unknown mode"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(messages, model=self.client.heavy_model)

        return {
            "message": response,
            "suggested_changes": None,
            "suggested_commands": []
        }

    def _detect_language(self, file_path: str) -> str:
        ext = file_path.split('.')[-1]
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'java': 'java',
            'rs': 'rust',
            'go': 'go'
        }
        return lang_map.get(ext, 'text')
```

---

## 7. Development Workflow

### 7.1 Setup

```bash
# Clone repo
git clone <repo-url>
cd atlas

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup
cd ../app
npm install

# Initialize database
cd ../backend
python -c "from atlas_api.database import init_db; init_db()"
```

### 7.2 Development Mode

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python uvicorn_entry.py

# Terminal 2: Start Vite dev server
cd app/renderer
npm run dev

# Terminal 3: Start Electron
cd app
npm run electron:dev
```

### 7.3 Environment Variables

```bash
# backend/.env
OPENAI_API_KEY=sk-...
DATABASE_PATH=./data/atlas.db
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

---

## 8. Security Considerations

### 8.1 Electron Security

- ✅ `contextIsolation: true`
- ✅ `nodeIntegration: false`
- ✅ `sandbox: true`
- ✅ Minimal IPC surface via `contextBridge`
- ✅ No remote module usage
- ✅ CSP headers in production

### 8.2 File System Access

- Restrict file operations to selected project roots
- Validate all file paths (prevent `../` traversal)
- No arbitrary command execution from renderer

### 8.3 API Security

- Backend only listens on `127.0.0.1` (localhost)
- No external network access in v1
- API keys stored in local settings (encrypted in future versions)

---

## 9. Build & Deployment

### 9.1 Production Build

```bash
# Build renderer
cd app/renderer
npm run build

# Package Electron app
cd ..
npm run package  # electron-builder
```

### 9.2 Electron Builder Config

```json
{
  "build": {
    "appId": "com.atlas.desktop",
    "productName": "Atlas",
    "directories": {
      "output": "dist"
    },
    "files": [
      "electron/**/*",
      "renderer/dist/**/*"
    ],
    "extraResources": [
      {
        "from": "../backend",
        "to": "backend",
        "filter": ["**/*", "!venv", "!__pycache__"]
      }
    ],
    "mac": {
      "target": "dmg",
      "icon": "assets/icon.icns"
    },
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "linux": {
      "target": "AppImage",
      "icon": "assets/icon.png"
    }
  }
}
```

### 9.3 Python Distribution

For v1: Require Python 3.11+ on user system

For v2: Bundle Python runtime
- Use PyInstaller or similar
- Or embed Python in Electron resources

---

## Appendix: Key Implementation Notes

### Wiki-Links Parsing

```python
import re

def extract_wiki_links(content: str) -> List[str]:
    """Extract [[Note Title]] style links"""
    pattern = r'\[\[([^\]]+)\]\]'
    return re.findall(pattern, content)

def compute_backlinks(note_id: str, db) -> List[Dict]:
    """Find all notes that link to this note"""
    target_note = db.execute(
        "SELECT title FROM notes WHERE id = ?", (note_id,)
    ).fetchone()

    if not target_note:
        return []

    all_notes = db.execute(
        "SELECT id, title, content FROM notes WHERE id != ?", (note_id,)
    ).fetchall()

    backlinks = []
    for note in all_notes:
        links = extract_wiki_links(note['content'])
        if target_note['title'] in links:
            backlinks.append({
                'note_id': note['id'],
                'title': note['title']
            })

    return backlinks
```

### Task Extraction from Notes

```python
import re
from typing import List, Dict

def extract_tasks_from_markdown(content: str) -> List[Dict]:
    """Parse markdown checkboxes into tasks"""
    lines = content.split('\n')
    tasks = []

    for line_num, line in enumerate(lines, start=1):
        # Match: - [ ] Task title
        match = re.match(r'^-\s+\[([ x])\]\s+(.+)$', line.strip())
        if match:
            is_done = match.group(1) == 'x'
            title = match.group(2)

            tasks.append({
                'title': title,
                'status': 'done' if is_done else 'todo',
                'source_line': line_num
            })

    return tasks
```

---

**End of Implementation Guide**

This document provides the complete technical foundation for building Atlas v1. Refer to the individual specification documents (`ai_implementation.md`, `project.md`, `electron_design.md`, `technical_design.md`) for additional context and design rationale.
