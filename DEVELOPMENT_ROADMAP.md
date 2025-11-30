# Atlas Development Roadmap

> Phased implementation tracking for Atlas v1.0

---

## ✅ Phase 1: Foundation & Architecture (COMPLETED)

### Backend Infrastructure
- [x] FastAPI application structure
- [x] Database schema design (SQLite)
- [x] Pydantic models for all entities
- [x] Configuration management
- [x] Database initialization system
- [x] Environment configuration

### API Layer
- [x] Notes CRUD endpoints
- [x] Tasks CRUD endpoints
- [x] Events CRUD endpoints
- [x] Projects CRUD endpoints
- [x] Conversations & Messages endpoints
- [x] AI endpoint placeholders

### Electron Foundation
- [x] Main process setup
- [x] Backend process manager
- [x] Preload script with IPC bridge
- [x] IPC handlers (file operations, terminal)
- [x] Terminal manager (node-pty)
- [x] Security configuration (context isolation, sandbox)

### React Foundation
- [x] Vite configuration
- [x] TypeScript setup
- [x] Basic App component
- [x] API client module
- [x] Type definitions

### Documentation & Tooling
- [x] Project README
- [x] Setup script
- [x] Git configuration
- [x] Package management
- [x] Build configuration

---

## 🚧 Phase 2: Core Data Features (IN PROGRESS)

### Backend Services
- [ ] Implement wiki-links parser
- [ ] Implement backlinks computation
- [ ] Task extraction from markdown
- [ ] Full-text search (SQLite FTS)
- [ ] Settings router implementation
- [ ] Dashboard aggregation endpoint

### Database Operations
- [ ] Add database migration system (Alembic)
- [ ] Seed data for development
- [ ] Database backup utilities
- [ ] Data export/import

### Testing
- [ ] Backend unit tests (pytest)
- [ ] API integration tests
- [ ] Database test fixtures

---

## 📋 Phase 3: Frontend UI (PENDING)

### Layout & Navigation
- [ ] Main app layout component
- [ ] Sidebar navigation
- [ ] Top bar with search
- [ ] Route setup (React Router)
- [ ] Theme system (light/dark)

### Dashboard View
- [ ] Today overview component
- [ ] Task summary cards
- [ ] Event calendar widget
- [ ] Recent notes list
- [ ] Daily briefing display

### Notes System
- [ ] Note list view
- [ ] Markdown editor (Monaco or CodeMirror)
- [ ] Preview mode
- [ ] Wiki-links autocomplete
- [ ] Backlinks panel
- [ ] Tag input component
- [ ] Task extraction UI

### Tasks View
- [ ] Task list component
- [ ] Task card/item component
- [ ] Filters (status, overdue, due today)
- [ ] Task creation modal
- [ ] Task editing inline
- [ ] Priority visualization
- [ ] Due date picker

### Calendar View
- [ ] Month view component
- [ ] Week view component
- [ ] Day view component
- [ ] Event creation modal
- [ ] Event editing
- [ ] Event-note/task linking UI

### Settings View
- [ ] Settings page layout
- [ ] AI configuration panel
- [ ] Calendar sync panel
- [ ] Dev workspace settings
- [ ] Theme preferences
- [ ] General preferences

---

## 🤖 Phase 4: AI Integration (PENDING)

### AI Service Layer
- [ ] OpenAI client wrapper implementation
- [ ] Streaming response handler
- [ ] Error handling and retries
- [ ] Rate limiting

### Embeddings & Search
- [ ] Embedding generation service
- [ ] Text chunking logic
- [ ] Vector storage (BLOB in SQLite)
- [ ] Cosine similarity search
- [ ] Hybrid search (FTS + embeddings)

### AI Orchestrator
- [ ] Daily briefing orchestrator
- [ ] Note summarization
- [ ] Task extraction (AI-assisted)
- [ ] Semantic Q&A flow
- [ ] Context retrieval system

### Prompt Engineering
- [ ] System prompts
- [ ] Daily briefing template
- [ ] Note summary template
- [ ] Semantic search template
- [ ] Dev assistant templates

### Chat Interface
- [ ] Chat panel component
- [ ] Message list with streaming
- [ ] Context indicators
- [ ] Reference citations
- [ ] Conversation management

---

## 💻 Phase 5: Dev Workspace (PENDING)

### Project Management
- [ ] Project list UI
- [ ] Project creation flow
- [ ] Project switching
- [ ] Project-note/task linking

### Code Editor
- [ ] File tree component
- [ ] Monaco editor integration
- [ ] Multiple tab support
- [ ] Syntax highlighting
- [ ] Auto-save
- [ ] File operations (IPC)

### Terminal Integration
- [ ] Terminal view component (xterm.js)
- [ ] Terminal session management
- [ ] Command history
- [ ] Terminal output capture
- [ ] Copy/paste support

### Dev AI Features
- [ ] Code explanation UI
- [ ] Refactor suggestions
- [ ] Test generation
- [ ] Terminal error interpretation
- [ ] Command suggestions
- [ ] Diff viewer for suggestions

---

## 🔗 Phase 6: Integrations (PENDING)

### Google Calendar
- [ ] OAuth flow implementation
- [ ] Calendar list fetch
- [ ] Event sync (pull)
- [ ] Event sync (push)
- [ ] Sync state tracking
- [ ] Conflict resolution

### External Services
- [ ] Settings for API keys
- [ ] Connection status indicators
- [ ] Sync scheduling

---

## 🎨 Phase 7: Polish & UX (PENDING)

### Onboarding
- [ ] First-run wizard
- [ ] Sample data creation
- [ ] Tutorial/guide
- [ ] Feature highlights

### Command Palette
- [ ] Command palette component
- [ ] Quick actions
- [ ] Search across entities
- [ ] Keyboard shortcuts

### Performance
- [ ] Lazy loading
- [ ] Virtual scrolling for lists
- [ ] Debouncing/throttling
- [ ] Caching strategies

### Accessibility
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] ARIA labels
- [ ] Focus management

---

## 🚀 Phase 8: Build & Distribution (PENDING)

### Production Build
- [ ] Optimize Vite build
- [ ] Minification
- [ ] Code splitting
- [ ] Asset optimization

### Electron Packaging
- [ ] macOS DMG build
- [ ] Windows NSIS installer
- [ ] Linux AppImage
- [ ] Auto-updater setup
- [ ] Code signing

### Python Distribution
- [ ] Bundle Python runtime (optional)
- [ ] Package backend dependencies
- [ ] Cross-platform testing

---

## 📊 Implementation Coverage Analysis

### ✅ Fully Covered (from docs)
1. **System Architecture** - 3 process model implemented
2. **Database Schema** - All tables and relationships defined
3. **API Contracts** - All endpoints structured
4. **Electron Security** - Context isolation, sandbox, IPC bridge
5. **File System Access** - IPC handlers for dev workspace
6. **Terminal Integration** - node-pty manager implemented

### ⚠️ Partially Covered
1. **AI Service Layer** - Structure exists, needs implementation
2. **React Components** - Basic structure, needs all views
3. **Settings Management** - Backend exists, needs frontend

### ❌ Not Yet Implemented
1. **AI Orchestration** - Needs OpenAI integration
2. **Embeddings Pipeline** - Needs implementation
3. **Google Calendar Sync** - OAuth and sync logic
4. **Frontend Views** - All major UI components
5. **Dev Workspace UI** - Editor, terminal, file tree
6. **Chat Streaming** - WebSocket implementation
7. **Testing Suite** - Unit and integration tests
8. **Build Pipeline** - Production packaging

---

## 🎯 Recommended Next Steps

### Immediate (Week 1-2)
1. Implement backend services (wiki-links, task extraction)
2. Set up database migrations
3. Create main layout and routing
4. Build notes list and editor views

### Short-term (Week 3-4)
5. Implement tasks view
6. Add AI client wrapper
7. Create daily briefing endpoint
8. Build chat interface

### Medium-term (Week 5-8)
9. Implement embeddings pipeline
10. Build dev workspace UI
11. Add Google Calendar sync
12. Create dashboard view

### Long-term (Week 9-12)
13. Polish all views
14. Add comprehensive testing
15. Implement onboarding
16. Prepare for production build

---

## 📝 Notes

### Current Status
- **Phase 1**: 100% complete
- **Phase 2**: 0% complete
- **Overall Progress**: ~15% of total v1 scope

### Critical Path
The fastest path to a working prototype:
1. Complete Phase 2 (backend services)
2. Build Notes + Tasks UI (Phase 3)
3. Add basic AI chat (Phase 4)
4. Everything else is enhancement

### Dependencies
- Phase 3 requires Phase 2 completion
- Phase 4 can start in parallel with Phase 3
- Phase 5 can start after Phase 3
- Phase 6-8 depend on Phases 2-5

---

## 🔄 Update Log

- **2025-11-29**: Initial roadmap created
- **2025-11-29**: Phase 1 marked complete

