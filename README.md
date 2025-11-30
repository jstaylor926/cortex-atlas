# Atlas - Local-First Personal OS

A comprehensive local-first personal operating system built with Electron, FastAPI, and React.

## Project Structure

```
cortex-atlas/
├── backend/                    # FastAPI backend
│   ├── atlas_api/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database connection
│   │   ├── models/            # Pydantic models
│   │   ├── routers/           # API routes
│   │   ├── ai/                # AI service layer
│   │   └── db/                # Database schema
│   ├── requirements.txt
│   └── uvicorn_entry.py       # Server startup
│
├── app/                        # Electron application
│   ├── electron/              # Main process
│   │   ├── main.ts
│   │   ├── preload.ts
│   │   ├── backendProcess.ts
│   │   ├── ipcHandlers.ts
│   │   └── terminalManager.ts
│   └── renderer/              # React UI
│       ├── src/
│       │   ├── App.tsx
│       │   ├── lib/
│       │   └── types/
│       └── package.json
│
└── IMPLEMENTATION.md          # Technical guide
```

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Initialize Database

```bash
cd backend
source venv/bin/activate
python -c "from atlas_api.database import init_db; init_db()"
```

### 3. Frontend Setup

```bash
cd app

# Install Electron dependencies
npm install

# Install renderer dependencies
cd renderer
npm install
cd ..
```

## Development

### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate
python uvicorn_entry.py
```

The backend will be available at http://127.0.0.1:4100

API documentation: http://127.0.0.1:4100/docs

### Start Frontend Development Server (Terminal 2)

```bash
cd app/renderer
npm run dev
```

The Vite dev server will run on http://localhost:5173

### Start Electron (Terminal 3)

```bash
cd app
npm run dev:electron
```

## Building for Production

### Build Renderer

```bash
cd app/renderer
npm run build
```

### Build Electron App

```bash
cd app
npm run build
```

### Package Application

```bash
cd app
npm run package       # Build for current platform
npm run package:mac   # Build for macOS
npm run package:win   # Build for Windows
npm run package:linux # Build for Linux
```

## Features

- **Notes**: Markdown notes with wiki-links
- **Tasks**: Task management with due dates and priorities
- **Events**: Calendar integration (local + Google Calendar)
- **Projects**: Dev workspace with code editor and terminal
- **AI**: AI-powered assistance and search
- **Local-First**: All data stored locally in SQLite

## API Endpoints

### Notes
- `GET /api/notes` - List notes
- `POST /api/notes` - Create note
- `GET /api/notes/{id}` - Get note
- `PATCH /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Events
- `GET /api/events` - List events
- `POST /api/events` - Create event

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project

### Conversations
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `POST /api/conversations/{id}/messages` - Send message

### AI
- `POST /api/ai/daily-briefing` - Get daily briefing
- `POST /api/ai/summarize-note` - Summarize note
- `POST /api/ai/search` - Semantic search

## Configuration

### Backend (.env)

```env
OPENAI_API_KEY=sk-your-key-here
DATABASE_PATH=./data/atlas.db
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: SQLite 3.42+
- **AI**: OpenAI API (GPT-4, embeddings)
- **Server**: uvicorn

### Frontend
- **Desktop**: Electron 28+
- **UI Framework**: React 18+
- **Build Tool**: Vite
- **Language**: TypeScript 5+

## Architecture

Atlas runs as three coordinated processes:

1. **Electron Main Process**: Window management, backend startup, IPC handlers
2. **FastAPI Backend**: REST API, database, AI integration
3. **React Renderer**: User interface

Communication:
- Renderer ↔ Backend: HTTP/WebSocket
- Renderer ↔ Main: IPC (via preload script)

## Development Workflow

1. Make changes to backend code → backend auto-reloads (uvicorn)
2. Make changes to renderer code → Vite hot module replacement
3. Make changes to Electron code → rebuild and restart Electron

## Security

- Context isolation enabled
- Node integration disabled
- Sandbox mode enabled
- Local-only backend (127.0.0.1)
- IPC surface minimized via preload script

## License

MIT

## Contributing

See IMPLEMENTATION.md for detailed technical documentation.
