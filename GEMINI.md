# Cortex Atlas - Gemini Context

This file provides context for the Gemini AI agent working on the Cortex Atlas project.

## 1. Project Overview

**Cortex Atlas** is a local-first personal operating system designed to integrate notes, tasks, events, and a developer workspace into a single cohesive application. It emphasizes data privacy (local SQLite) and AI assistance.

### Tech Stack
*   **Desktop Shell:** Electron 28+ (TypeScript)
*   **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS (planned)
*   **Backend:** Python 3.11+, FastAPI, Uvicorn
*   **Database:** SQLite 3.42+
*   **AI:** OpenAI API (GPT-4, Embeddings) via Python backend

### Architecture
The application runs as three coordinated processes:
1.  **Electron Main Process:** Handles window management, backend lifecycle (spawns Python process), and IPC.
2.  **FastAPI Backend:** Provides REST API for data, AI services, and database access. Listens on `127.0.0.1:4100`.
3.  **React Renderer:** The UI, communicating with the Backend via HTTP/WebSocket and the Main process via IPC (for file I/O and terminal).

## 2. Current Status (as of Nov 2025)

*   **Phase:** Phase 2 (Core Data Features) is in progress.
*   **Completed:** Phase 1 (Foundation & Architecture) - Basic setup of Electron, FastAPI, and React is done.
*   **Immediate Goals:** Implementing backend services (wiki-links, task extraction), DB migrations, and basic UI views (Notes/Tasks).

## 3. Development Setup & Commands

### Prerequisites
*   Python 3.11+
*   Node.js 18+

### Initialization
```bash
# 1. Backend Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env from .env.example and init DB
python -c "from atlas_api.database import init_db; init_db()"

# 2. Frontend/Electron Setup
cd app
npm install
cd renderer
npm install
```

### Running the App (Development)
Requires 3 separate terminal processes:

1.  **Backend:**
    ```bash
    cd backend
    source venv/bin/activate
    python uvicorn_entry.py
    # Runs at http://127.0.0.1:4100
    ```

2.  **Frontend (Renderer):**
    ```bash
    cd app/renderer
    npm run dev
    # Runs at http://localhost:5173
    ```

3.  **Electron (Main):**
    ```bash
    cd app
    npm run dev:electron
    ```

## 4. Project Structure

```text
cortex-atlas/
├── backend/                 # Python FastAPI Backend
│   ├── atlas_api/
│   │   ├── main.py          # App entry point
│   │   ├── models/          # Pydantic models
│   │   ├── routers/         # API endpoints
│   │   └── database.py      # SQLite connection
│   └── uvicorn_entry.py     # Server starter
│
├── app/                     # Electron + React
│   ├── electron/            # Main process (TypeScript)
│   │   ├── main.ts
│   │   └── ipcHandlers.ts
│   └── renderer/            # React Frontend
│       ├── src/
│       │   ├── lib/apiClient.ts  # REST client
│       │   └── App.tsx
│       └── vite.config.ts
```

## 5. Development Conventions

### Code Style
*   **Python:** Follow PEP 8. Use Pydantic for data validation.
*   **TypeScript:** Strict typing. Use functional React components with hooks.

### Communication Patterns
*   **Data Fetching:** The React frontend talks directly to the Python backend via HTTP (`lib/apiClient.ts`).
*   **System Ops:** File I/O, Terminal spawning, and native dialogs use Electron IPC (`electron/ipcHandlers.ts` <-> `renderer/src/lib/electron.d.ts`).

### Database
*   Schema is defined in `backend/atlas_api/db/schema.sql` (or via models/SQLAlchemy if transitioning).
*   Currently using raw SQL or lightweight ORM patterns as defined in `database.py`.

## 6. Key Documentation
*   **`IMPLEMENTATION.md`**: Detailed technical specs, database schema, and API contracts. **Read this before modifying backend logic.**
*   **`DEVELOPMENT_ROADMAP.md`**: Tracks progress and next steps.
*   **`README.md`**: General overview and setup.
