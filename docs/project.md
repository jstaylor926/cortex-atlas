## 1. Product Scope (One-liner)

> **Atlas** is a local-first desktop personal operating system for knowledge work: notes, tasks, calendar, and an AI assistant all in one, now with an optional dev/IDE workspace for engineers.

Runs as: **Electron desktop app**
Backend: **FastAPI + SQLite + OpenAI**
Mode: **Local-first**, cloud only for AI + sync (e.g., Google Calendar).

---

## 2. Core Data Types (Conceptual)

These are language-agnostic “entities” the whole feature set builds on.

1. **Note**

   * Fields (conceptual):

     * `id`, `title`, `content (markdown)`, `tags[]`
     * `created_at`, `updated_at`
     * `links[]` (wiki-links to other notes)
     * `backlinks[]` (derived)
   * Behaviors:

     * Markdown editing
     * Wiki-links (`[[Note Title]]`) + backlinks graph 
     * Task extraction from `- [ ]` style syntax 

2. **Task**

   * Fields:

     * `id`, `title`, `status (todo/in_progress/done)`
     * `priority`, `due_date`, `tags[]`
     * `source_note_id`, `source_line` (if created from note) 
     * `created_at`, `completed_at`
   * Behaviors:

     * CRUD, filtering (overdue, due today, by status) 

3. **Event**

   * Fields:

     * `id`, `title`, `description`
     * `start_time`, `end_time`, `location`
     * `source` (local | google), `external_id`
     * `linked_notes[]`, `linked_tasks[]` 
   * Behaviors:

     * Local calendar events + sync to/from Google Calendar 

4. **ChatMessage / Conversation**

   * Fields:

     * `id`, `conversation_id`
     * `role` (user/assistant/system), `content`, `model`
     * `timestamp` 
   * Behaviors:

     * Persistent chat history per conversation/thread
     * Messages can be associated with notes/tasks/events as context.

5. **Embedding / ContextChunk**

   * Fields:

     * `id`, `source_type` (note/task/etc.), `source_id`
     * `chunk_index`, `content`
     * `embedding` (vector)
     * `created_at` 
   * Behaviors:

     * Vector search for notes/tasks
     * Context retrieval for AI chat & “Ask about my notes” 

6. **SyncState**

   * Fields:

     * `id`, `provider`, `last_sync`, `sync_token`, `metadata_json` 

7. **Project (new, for Dev Workspace)**

   * Fields (conceptual):

     * `id`, `name`, `root_path`
     * `type` (code | general)
     * `linked_notes[]`, `linked_tasks[]`
   * Behaviors:

     * Used by Dev Workspace to open a folder in terminal/editor
     * Used by tasks/notes to reference specific code work.

---

## 3. Feature Pillars

### 3.1 Dashboard

**Goal:** Single “Today” view that pulls together tasks, notes, events, and AI summary.

**Key Capabilities**

* **Today / Overview**

  * Show:

    * Overdue tasks
    * Tasks due today
    * Upcoming events
    * Recent notes 
* **Daily Briefing (AI)**

  * One-click: “Generate my daily briefing”
  * Uses:

    * Tasks (overdue, due today)
    * Today’s calendar
    * Recent notes
  * Renders markdown briefing (goals, schedule, priorities). 

---

### 3.2 Notes

**Goal:** Markdown-first note system with wiki-style linking, backlinks, and tight task integration.

**Key Capabilities**

* **Note List**

  * List of notes with:

    * Title, preview, tags, updated_at, task_count 
  * Search by text and tags.

* **Note Editor**

  * Markdown editor with:

    * Title, content
    * Auto-save
    * Preview mode (rendered markdown + syntax highlighting) 
  * Wiki-links:

    * `[[Note Title]]` creation/links
    * Backlinks section (notes that refer here) 

* **Task Extraction from Notes**

  * On save, parse `- [ ]` / `- [x]` in content.
  * Create/update tasks with:

    * Title, status, priority, due date, source_note_id, source_line. 
  * In-editor “Tasks from this note” panel (status toggling, counts). 

* **Tagging & Templates (polish)**

  * Tag input + autocomplete + tag filters. 
  * Note templates (daily note, meeting note, etc.). 

---

### 3.3 Tasks

**Goal:** Turn notes into actionable tasks, track them, and make them the backbone of your day.

**Key Capabilities**

* **Task List & Board**

  * Group tasks by:

    * Status (todo/in_progress/done)
    * Filters: all, overdue, due today, by status. 
  * Show key fields: title, priority, due date, source note link.

* **Task CRUD**

  * Create via:

    * Dedicated task form
    * Automatic extraction from notes.
  * Edit:

    * Title, priority, due date, tags.
  * Update status (with completion timestamp). 
  * Delete with confirmation.

* **Priority & Due Date UX (polish)**

  * Color-coded priorities.
  * Date picker + natural language due dates (“tomorrow”, “next week”). 

* **Links**

  * Each task can link to:

    * A source note
    * A project (for Dev Workspace)
    * Related events (e.g., due at meeting time).

---

### 3.4 Calendar & Events

**Goal:** Integrate time-bound commitments into the same system as notes/tasks and AI.

**Key Capabilities**

* **Local Calendar**

  * Event CRUD:

    * Create, update, delete events in local DB. 
  * Views:

    * Month / Week / Day views via calendar component. 

* **Google Calendar Sync**

  * OAuth for Google Calendar.
  * One or more calendars synced:

    * Pull events into local `events` table
    * Two-way sync for changes. 
  * Sync state tracked in `sync_state` (last_sync, tokens, metadata). 

* **Linking with Notes/Tasks**

  * Events can reference:

    * Related notes (meeting notes, agendas)
    * Related tasks (preparation, follow-ups).

* **Dashboard Integration**

  * Calendar widget on Dashboard (today/this week). 

---

### 3.5 AI Assistant & Chat

**Goal:** Persistent AI partner that understands your notes, tasks, events, and (optionally) dev projects.

**Key Capabilities**

* **Global Chat Panel**

  * Right-side panel accessible from any view. 
  * Persistent history per conversation.
  * Basic send/receive with streaming responses. 

* **Task-Specific AI Actions**

  * AI “Task Types” (conceptual):

    * `extract_tasks` – parse tasks from a note
    * `summarize_note` – TL;DR plus action items
    * `daily_briefing`
    * `quick_question`, `deep_analysis`, `study_plan`, `complex_planning` 

* **Context-Aware Chat**

  * Uses embeddings to:

    * Find relevant notes/tasks/events for a query
    * Inject them into the prompt
    * Cite which notes/tasks were used. 

* **Study / Review Features**

  * Study recommendations based on:

    * Review history
    * Note importance/tags
    * Linked notes/tasks. 

---

### 3.6 Search & Embeddings

**Goal:** Make your entire knowledge base searchable semantically and structurally.

**Key Capabilities**

* **Full-text Search**

  * Use SQLite FTS for:

    * Notes content
    * Task titles/descriptions. 

* **Embedding Generation**

  * Generate embeddings for:

    * Notes (chunked)
    * Optionally tasks.
  * Store in `embeddings` table. 

* **Vector Search**

  * Semantic search endpoint:

    * `query` → top N chunks (notes/tasks).
  * Used by:

    * AI “Ask about my notes”
    * Dashboard/command palette search. 

---

### 3.7 Dev Workspace (IDE + Terminal)

**Goal:** A dedicated workspace for software projects that connects code, tasks, notes, terminal, and AI.

**Key Capabilities**

1. **Project Management**

   * Define a `Project` with:

     * Name, root path, type (code/general)
   * Link:

     * Notes (design docs, dev logs)
     * Tasks (issues, TODOs)
   * Quickly switch between active projects.

2. **Code Editor**

   * File tree for the selected project directory.
   * Editor with:

     * Multiple tabs
     * Syntax highlighting (at minimum)
   * Basic UX:

     * “Open in Dev Workspace” button from:

       * Task (with file_path)
       * Note (with referenced file path).

3. **Embedded Terminal**

   * Terminal pane bound to the project root:

     * Runs user commands (build, test, dev servers).
   * Command history per project.
   * Integration pattern:

     * User manually executes commands
     * Optionally send terminal output to AI for explanation.

4. **AI-Assisted Dev**

   * In Dev Workspace, AI gets additional context:

     * Active project name + root path
     * Open file content (via explicit send)
     * Recent terminal output (optional)
   * Feature examples:

     * “Explain this function”
     * “Propose a refactor”
     * “Why is this test failing?” (user pastes log or sends captured output)
   * AI generates suggestions, diffs, or commands—but **doesn’t auto-run commands**; user stays in control.

5. **Connections to Notes/Tasks**

   * Tasks can include:

     * `project_id`, `file_path`, `symbol`
   * Clicking such a task:

     * Opens project in Dev Workspace
     * Opens file, scrolls to relevant section.
   * Dev notes:

     * Daily dev logs saved as notes
     * AI can cross-reference logs + code to suggest next steps.

---

### 3.8 Settings & Integrations

**Goal:** Central configuration for AI providers, calendar sync, and behavior preferences.

**Key Capabilities**

* **AI Providers**

  * Configure:

    * OpenAI API key
    * Preferred models (chat vs embeddings)
    * Toggles: prefer local vs cloud, etc. (conceptually mirroring the old router). 

* **Calendar / External Services**

  * Manage Google auth
  * Toggle which calendars to sync.

* **Dev Workspace Settings**

  * Project list management
  * Per-project settings (e.g., default test command).

* **General Preferences**

  * Theme, keyboard shortcuts
  * Daily briefing schedule (if we later add background generation).

---

### 3.9 Onboarding & UX Polish

**Goal:** Make the first 10 minutes delightful and reduce friction over time.

**Key Capabilities**

* First-run setup:

  * Explain “Notes, Tasks, Calendar, Dev Workspace, AI” in a quick tour.
  * Optionally prompt:

    * Connect Google Calendar
    * Add first project for Dev Workspace
    * Set OpenAI key.

* Defaults:

  * Daily note template
  * Example note with tasks + wiki-links to showcase features.

---

If this overall feature map looks right to you, the next step is:

* Pick what belongs in **v1** vs **v2** (e.g., Dev Workspace v1 = terminal + simple editor + project links, embeddings maybe v1.1).
* Then we can translate these features into:

  * Concrete **data schemas** (still conceptual, like JSON shapes)
  * Then **FastAPI endpoints** + **Electron view structure**.


Perfect — then here is a clean, **official v1 feature spec** for the project.

This will be our reference document for all future implementation steps (schemas, API design, Electron architecture, AI workflows, etc.). You can consider this the **Product Specification v1.0** for your Electron + FastAPI + OpenAI reboot.

---

# **📘 Atlas — Product Specification v1.0**

*A local-first personal OS for knowledge work, with a built-in Dev Workspace.*

This specification defines the **complete v1 feature set** you approved, split across the core pillars of the application.

---

# **1. High-Level Overview**

Atlas is a **local desktop application (Electron)** backed by a **FastAPI server** that manages:

* Notes
* Tasks
* Calendar & events
* AI assistant
* Dev workspace (terminal + code editor)
* Search & embeddings
* Settings & integrations

Atlas emphasizes:

* **Local-first storage** (SQLite)
* **OpenAI-powered intelligence**
* **Integrated workflows** between notes → tasks → calendar → dev

---

# **2. Core Entities (Data Types)**

These conceptual entities guide database schema, API contracts, and UI structure.

### **2.1 Note**

* `id`
* `title`
* `content` (markdown)
* `tags[]`
* `created_at`, `updated_at`
* `links[]` → wiki-links to other notes
* `backlinks[]` (derived)
* Derived: tasks extracted from content

### **2.2 Task**

* `id`
* `title`
* `description` (optional)
* `status` (todo / in_progress / done)
* `priority` (low/medium/high)
* `due_date`
* `tags[]`
* `source_note_id`
* `source_line`
* `project_id` (Dev Workspace)
* Timestamps: `created_at`, `completed_at`

### **2.3 Event**

* `id`
* `title`, `description`
* `start_time`, `end_time`, `location`
* `source` (local | google)
* `external_id` (for sync)
* Relationships: `linked_notes[]`, `linked_tasks[]`

### **2.4 Conversation & ChatMessage**

* `conversation_id`
* `id`
* `role` (user / assistant / system)
* `content`
* `model`
* `timestamp`
* Optional: `references[]` (notes/tasks/events included as context)

### **2.5 Embedding / ContextChunk**

* `id`
* `source_type` (note, task, etc.)
* `source_id`
* `chunk_index`
* `content`
* `embedding` (vector)
* `created_at`

### **2.6 SyncState**

* `provider` (google_calendar)
* `last_sync`
* `sync_token`
* `metadata_json`

### **2.7 Project (Dev Workspace)**

* `id`
* `name`
* `root_path`
* `type` (code/general)
* Relationships:

  * Linked tasks
  * Linked notes

---

# **3. v1 Feature Set (Fully Approved)**

This part lists every v1 feature organized by the major app pillars.

---

## **3.1 Dashboard (v1)**

**Goal:** Instant visibility into your day + an optional AI-powered daily briefing.

### **v1 Features**

* Today’s overview:

  * Overdue tasks
  * Tasks due today
  * Today’s calendar events
  * Recent notes
* Daily Briefing:

  * AI-generated briefing from:

    * Tasks
    * Calendar
    * Recent notes

---

## **3.2 Notes (v1)**

### **v1 Features**

* Note list:

  * Title, preview snippet, updated time, tags
* Markdown editor (edit + preview)
* Wiki-links: `[[Note Title]]`
* Backlinks pane
* Tags
* Task extraction from notes:

  * `- [ ]` → todo task
  * `- [x]` → completed task
  * Links back to note line number
* Note metadata sidebar:

  * Links
  * Backlinks
  * Tasks in this note

---

## **3.3 Tasks (v1)**

### **v1 Features**

* Task list:

  * Filter: All, Overdue, Due Today, By Status
  * Fields shown: title, priority, due date, source note, project
* CRUD (create/update/delete)
* Set task priority (3 levels)
* Set due date
* Link to:

  * Source note (auto)
  * Project (manual selection)
* Toggle status (todo → in progress → done)

---

## **3.4 Calendar & Events (v1)**

### **v1 Features**

* Local calendar:

  * Month view
  * Week view
  * Basic day view
* Event CRUD
* Link events ↔ notes/tasks
* Google Calendar sync:

  * Pull from selected Google calendars
  * Display in-app
  * Push local edits → Google Calendar
  * Track sync state

---

## **3.5 AI Assistant & Chat (v1)**

### **v1 Features**

* Dedicated chat panel
* Persistent conversation threads
* AI message streaming
* Contextual assistant:

  * Automatically pulls relevant:

    * Notes
    * Tasks
    * Calendar events
  * Cites which entities were used in context
* AI task types:

  * Extract tasks from note
  * Summarize note
  * Daily briefing
  * Quick question
  * Study plan
  * Deep analysis (multi-chunk retrieval)

---

## **3.6 Search & Embeddings (v1)**

### **v1 Features**

* Full-text search for notes + tasks
* Embeddings generated for:

  * Notes (chunked)
  * Optionally task descriptions
* Semantic search endpoint
* “Ask about my notes” → semantic retrieval → AI answer

---

# **4. Dev Workspace (v1)**

This is the new major feature pillar.

---

## **4.1 Project System**

### **v1 Features**

* Create a Project:

  * Name
  * Root folder path
* Project list
* Switch between projects
* Each project stores:

  * Root path
  * Linked tasks
  * Linked notes

---

## **4.2 Code Editor (v1)**

### **v1 Features**

* File tree of selected project
* Open text/code files
* Syntax highlighting for major languages
* Multiple open tabs
* Auto-save edits
* “Open file in Dev Workspace” from tasks/notes

---

## **4.3 Integrated Terminal (v1)**

### **v1 Features**

* Terminal pane bound to project root
* Runs shell commands (zsh/bash on Mac, powershell/cmd on Windows)
* Terminal history per project
* “Send last terminal output to AI” button

---

## **4.4 AI-Assisted Dev (v1)**

### **v1 Features**

* In Dev Workspace, AI receives additional context:

  * Active project name
  * Open file content (on demand)
  * Terminal output (on demand)
* Actions:

  * Explain selected code
  * Suggest improvements
  * Generate tests
  * Suggest commands to run (not auto-run)

---

## **4.5 Links Between Dev & Notes/Tasks**

### **v1 Features**

* Tasks may include:

  * `project_id`
  * `file_path`
* Clicking:

  * Opens project in Dev Workspace
  * Opens file
  * Scrolls to code selection (optional)
* Notes may include:

  * Paths to files
  * AI can cross-reference notes + code

---

# **5. Settings (v1)**

### **v1 Features**

* AI:

  * OpenAI API key
  * Preferred chat model
  * Preferred embedding model
* Calendar:

  * Connect Google Calendar
  * Select which calendars to sync
* Dev Workspace:

  * Manage projects
  * Default test/build commands (optional)
* General:

  * Theme (light/dark/system)
  * Keybindings
  * Autosave settings

---

# **6. Onboarding & UX (v1)**

### **v1 Features**

* First-run onboarding:

  * Connect Google Calendar (optional)
  * Add OpenAI API key
  * Create first note
  * Create first project (optional)
* Demo content:

  * Example note
  * Example tasks
  * Example project bootstrap (optional)
* Getting started guide

---

# **7. Summary — v1 Scope Unlocked**

You now have a full **v1 product spec** with:

✔ Notes
✔ Tasks
✔ Calendar
✔ AI Assistant
✔ Search & embeddings
✔ Dev Workspace (editor + terminal + AI context)
✔ Settings
✔ Onboarding

Everything in this list is included in v1.

---

## **Next Step Options**

Choose how you want to proceed:

### **Option A — Define data schemas (JSON / conceptual DB schema)**

We turn each feature into specific, clean JSON shapes + DB tables.

### **Option B — Define API design**

We map every feature into FastAPI endpoints.

### **Option C — Electron architecture**

Define the layout (views, panels, routing), preload scripts, IPC, and file system access patterns.

### **Option D — AI system design**

Define prompts, tools, retrieval flow, and how Dev Workspace integrates with AI.

Which direction do you want to go next?
