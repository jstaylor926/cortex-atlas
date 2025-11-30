# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI service (`atlas_api/main.py`, routers, AI helpers, SQLite schema in `db/`); `uvicorn_entry.py` boots the server.
- `app/`: Electron shell; TypeScript main process in `electron/`, React renderer in `renderer/src/`.
- `docs/`, `IMPLEMENTATION.md`, and `DEVELOPMENT_ROADMAP.md`: design notes and planning.
- Data and virtualenv artifacts live under `backend/data` and `backend/venv`; keep user data out of commits.

## Build, Test, and Development Commands
- Backend setup: `cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
- Run backend: `cd backend && source venv/bin/activate && python uvicorn_entry.py` (serves `127.0.0.1:4100`).
- Renderer dev: `cd app/renderer && npm install && npm run dev` (Vite at `localhost:5173`).
- Electron dev shell: `cd app && npm install && npm run dev:electron` (waits for renderer build, then launches Electron).
- Production builds: `cd app/renderer && npm run build`; `cd app && npm run build` then `npm run package[:mac|:win|:linux]`.

## Coding Style & Naming Conventions
- Python: follow PEP 8 with type hints; prefer dataclasses/Pydantic models in `atlas_api/models`; keep routers small and compose via dependency injection.
- TypeScript/React: favor functional components, hooks, and explicit prop types; group shared helpers under `renderer/src/lib` and types under `renderer/src/types`.
- Electron main process: keep IPC handlers in `electron/ipcHandlers.ts`; isolate OS/process logic in `terminalManager.ts` or `backendProcess.ts`.
- Use consistent casing: snake_case for Python modules and vars; camelCase for JS/TS values; PascalCase for React components.

## Testing Guidelines
- No test harness is committed yet; add Python tests under `backend/tests/` (pytest) and renderer tests under `app/renderer/src/__tests__/` (Vitest/React Testing Library) when introducing new features.
- Name tests after the unit under test (e.g., `test_main.py`, `App.test.tsx`) and keep fixtures small.
- Aim for coverage on new routes, data access, and IPC boundaries; include regression tests for bug fixes.

## Commit & Pull Request Guidelines
- Write clear, imperative commit subjects (e.g., “Add note search API”); keep scope focused. Conventional Commit prefixes are welcome but not required.
- In PRs, include a short summary, testing notes/commands run, and any screenshots or API samples that help reviewers.
- Link related issues/tasks when available and call out breaking changes or migration steps (env vars, schema updates).

## Security & Configuration Tips
- Never commit real secrets; copy `backend/.env.example` to `.env` and populate locally. Keep API keys out of logs.
- If schema or AI prompt files change, note the impact on stored data and cache invalidation in PR descriptions.
