Here’s how I’d wire the **AI brain** for Atlas in a way that’s powerful but not insane to implement.

I’ll treat this as a design for an **“AI Service Layer”** inside FastAPI that talks to OpenAI and to your DB.

---

## 1. What you want the AI to do (clear roles)

Atlas’s AI isn’t just “chat”. It has **specific jobs**:

1. **General Assistant / Chat**

   * Answer questions
   * Use your notes/tasks/events as context (“What did I decide about X?”)

2. **Daily Briefing**

   * Look at today’s tasks/events/recent notes
   * Produce a structured “here’s your day” summary

3. **Note Intelligence**

   * Summarize a note
   * Extract tasks from notes (either deterministic or AI-assisted)
   * Possibly suggest tags

4. **Semantic Q&A over your data**

   * “What are my open items on project Atlas?”
   * Retrieval + answer synthesis

5. **Dev Assistant (in Dev Workspace)**

   * Explain code
   * Suggest refactors / tests
   * Explain terminal errors
   * Suggest (but not auto-run) commands

Everything funnels into a **small set of API endpoints** under `/ai` and the chat endpoints you already designed.

---

## 2. AI service layer inside FastAPI

Create a dedicated module, e.g.:

```txt
backend/atlas_api/
  ai/
    __init__.py
    client.py          # OpenAI client wrapper
    retrieval.py       # embeddings + search
    prompts.py         # prompt templates
    orchestrator.py    # high-level flows ("daily_briefing", "dev_assist" etc.)
```

### 2.1 The orchestrator

One entry point per “task type”, roughly:

* `generate_daily_briefing(date, settings)`
* `summarize_note(note_id, options)`
* `extract_tasks(note_id, mode)`
* `answer_question(query, options)`  (semantic Q&A)
* `dev_assist(payload)`  (dev mode)

Each orchestrator function does:

1. Gather **structured context** from DB (notes/tasks/events/projects)
2. Call **retrieval** if needed (embeddings search)
3. Build a **prompt** using templates + context
4. Call **OpenAI** with chosen model + options
5. Parse response into structured output for your API

This keeps your FastAPI routes thin:

```python
@router.post("/ai/daily-briefing")
def daily_briefing(req: DailyBriefingRequest):
    return ai.orchestrator.generate_daily_briefing(req.date, req.options)
```

---

## 3. Model choices (practical defaults)

You can make these configurable in `settings.ai`, but here’s a solid pattern:

* **Chat / Reasoning:**

  * Default: `gpt-4.1-mini` (fast, cheap)
  * Heavy: `gpt-4.1` for complex dev stuff or long multi-note reasoning

* **Embeddings:**

  * `text-embedding-3-large` (or “small” if cost > recall)
  * Used for:

    * Indexing notes (and maybe tasks)
    * Query-time similarity search

Expose these in settings so later you can switch or A/B:

```jsonc
"ai": {
  "chat_model": "gpt-4.1-mini",
  "heavy_chat_model": "gpt-4.1",
  "embedding_model": "text-embedding-3-large"
}
```

---

## 4. Retrieval design (embeddings + FTS)

### 4.1 What gets embedded

* **Notes**:

  * Chunk long notes (e.g., ~500–800 tokens per chunk)
  * Each chunk → embedding row in `embeddings` table

* **Tasks** (optional):

  * Brief text → one embedding per task

You already have structure in the schema; just fill `embeddings` table consistently.

### 4.2 Query-time retrieval

For any AI call with `include_context: true`:

1. Compute embedding for the **user query**
2. Search `embeddings` table:

   * Get top N chunks (e.g., 10–20)
3. Group by source note/task
4. Optionally filter by:

   * Date (for “recent” questions)
   * Tag (if user specified)

You can hybridize with FTS later (combine FTS rank + embedding rank), but v1 can be pure embedding search.

### 4.3 Context bundle

For each AI call that uses retrieval, build a **compact context bundle**:

* For **notes**:

  * Title
  * Excerpt(s)
  * Created/updated date
  * Maybe tag list

* For **tasks/events**:

  * Short summary lines

Then you pass that into the prompt as a JSON-ish or bullet-list context section.

---

## 5. Prompting patterns

Keep prompts **templated** and **task-specific**, not “one mega prompt”. In `prompts.py`, define templates like:

### 5.1 Global system prompt (for most chat)

Used for `/conversations/{id}/messages` and many AI calls:

> You are Atlas, a local-first personal knowledge and productivity assistant.
>
> You have access to the user’s notes, tasks, calendar, and (optionally) coding projects.
> Always:
>
> * Prefer concrete, actionable suggestions.
> * When referencing notes/tasks/events, mention them explicitly.
> * If some information is not present in the provided context, say you don’t know rather than inventing details.

Then each use case adds its own instructions.

---

### 5.2 Daily briefing prompt

**Context you pass in:**

* Tasks:

  * Overdue, due today
* Events:

  * Today’s events
* Notes:

  * Summary lines of recent notes (titles + first lines)

**Instructions:**

> The user wants a concise daily briefing for {DATE}.
> You are given:
>
> * A list of overdue tasks
>
> * A list of tasks due today
>
> * A list of events scheduled today
>
> * A list of recent notes with brief excerpts
>
> 1. Start with a short greeting and a one-sentence overview.
> 2. List the top 3–5 priorities as bullets, referencing task titles.
> 3. Mention today’s events with times.
> 4. Optionally highlight any important themes from recent notes.
>
> Return your output as Markdown with headings:
>
> * "## Overview"
> * "## Top Priorities"
> * "## Today’s Schedule"
> * "## Notes to Review" (optional)

The orchestrator fills `{DATE}`, attaches the context, and the `/ai/daily-briefing` endpoint returns the Markdown + reference IDs you already got from DB.

---

### 5.3 Note summarization + action items

**Context:**

* Full note content (or chunk if huge)
* Metadata: title, date

**Prompt skeleton:**

> The user wrote the following note titled "{TITLE}".
>
> 1. Produce a concise summary in 2–4 bullet points.
> 2. Identify any clear action items in the note. For each, return:
>
>    * A short title
>    * Optional due date if explicitly mentioned (otherwise null)
>
> Return JSON with this shape:
>
> ```json
> {
>   "summary": ["bullet 1", "bullet 2", ...],
>   "action_items": [
>     { "title": "...", "due_date": "YYYY-MM-DD or null" }
>   ]
> }
> ```

You then parse JSON, create tasks, attach summary to UI.
(Use `response_format={"type":"json_schema", ...}` or similar if you want strict JSON.)

---

### 5.4 Semantic Q&A (“Ask about my notes”)

**Context from retrieval:**

A list of relevant chunks:

```txt
[Note: "CRE Data Center Requirements", updated 2025-11-20]
- ... chunk text ...

[Note: "Meeting with Parker", updated 2025-11-18]
- ... chunk text ...
```

**Prompt skeleton:**

> The user asked:
> "{QUERY}"
>
> You are given excerpts from their personal notes and tasks that may be relevant. Each excerpt shows a title and content.
>
> 1. Use only the information in these excerpts to answer the question.
> 2. If important details are missing, say that clearly.
> 3. At the end, list which notes/tasks you used by title.
>
> Excerpts:
> {CONTEXT_BUNDLE}

**Output:**

* Answer text (for the user)
* A list of referenced note IDs you already know from retrieval (for UI to show “based on…” badges).

---

## 6. Chat endpoint behavior

For `/conversations/{id}/messages`:

1. Store the **user message** in DB.
2. Decide if you should:

   * Just chat (no context)
   * Do retrieval and attach context
   * Call a specialized flow (e.g., “daily briefing” if they ask “what should I work on today?”) — you can start simple and add intent detection later.

Simplest v1:

* If `options.include_context == true`, run retrieval → build context bundle → call chat model with:

  * System prompt (Atlas role)
  * Context message (role: `system` or `assistant`, “Here are relevant notes/tasks/events…”)
  * Conversation history (last N messages)
  * New user message

3. Get model response, store it as `chat_message` with `references` popped from retrieval results.
4. Return both messages (user + assistant) to UI.

---

## 7. Dev Assistant design (Dev Workspace)

This is its own flow: `/ai/dev/assist`.

**Inputs:**

* `project_id`
* `mode`: `"explain_code" | "suggest_refactor" | "generate_tests" | "interpret_terminal_output"`
* `file_path`
* `code`
* Optional:

  * `selection`
  * `terminal_output`

**Prompt skeleton examples:**

### 7.1 Explain code

> You are a senior software engineer helping the user understand code in their local project "{PROJECT_NAME}".
>
> File: `{FILE_PATH}`
>
> Code:
>
> ```{LANG}
> {CODE}
> ```
>
> The user is focused on lines {START_LINE}–{END_LINE}.
>
> 1. Explain what this code does in clear language.
> 2. Mention any potential pitfalls or edge cases.
> 3. Suggest 1–2 possible improvements, but do not rewrite the entire file.

### 7.2 Suggest refactor

Similar to above, but:

> Suggest a refactor for the selected region.
> Focus on readability and maintainability.
> Return your answer as:
>
> * A short explanation
> * A code block with the **refactored version of only the selected part**, preserving API behavior.

### 7.3 Interpret terminal output

> The user ran a command in their project and got the following terminal output:
>
> ```txt
> {TERMINAL_OUTPUT}
> ```
>
> 1. Explain what went wrong.
> 2. Suggest up to 3 specific things they can try next.
> 3. If relevant, include 1–2 example commands they might run.

**Response shape:**

You can standardize dev responses as:

```jsonc
{
  "message": "Human-readable explanation",
  "suggested_changes": "patch or code snippet (optional)",
  "suggested_commands": ["pytest -k test_foo", "npm run lint"]
}
```

Dev Workspace decides what to do with them (e.g., show commands in a list with “Insert into terminal” buttons).

---

## 8. Logging & future fine-tuning

Since you’ve been deep in SFT/DPO land, design now so you can fine-tune later:

* Log **AI interactions** to a local table (or just JSONL file):

  * Prompt skeleton ID
  * Input context (redacted if needed)
  * Model, parameters
  * Output
  * User feedback (if you ever add thumbs up/down)

That gives you future paths for:

* Fine-tuning a **personal Atlas model** on your own data
* DPO on “better vs worse” responses for dev assistance / daily briefings

But none of this is required for v1.

---

## 9. Putting it together: one example flow

User asks in chat: **“What should I work on today?”**

1. Frontend → `POST /conversations/{id}/messages` with `include_context: true`.
2. Backend:

   * Stores user message.
   * Fetches:

     * Overdue tasks
     * Tasks due today
     * Today’s events
   * Builds context bundle summary.
3. Calls chat model with:

   * System prompt (Atlas role)
   * Context message summarizing tasks/events
   * Conversation history + user question
4. Model replies:

   * Suggests top 3–5 things to do, referencing task titles.
5. Backend stores assistant message with list of referenced task IDs.
6. UI:

   * Shows answer in chat
   * Optionally highlights the referenced tasks in the Tasks view.

That’s the basic pattern repeated for other flows.

---

If you’re happy with this AI integration design, next we can:

* Draft **concrete Python code** for the AI layer (e.g., `orchestrator.daily_briefing` and `dev_assist` examples), **or**
* Zoom in on a single feature (like **daily briefing** or **Dev Assistant**) and fully spec the end-to-end logic + data structures.


Let’s start with **Daily Briefing** — it touches tasks, calendar, notes, and chat, so if we nail this, a lot of other AI flows become “variants” of it.

---

## 1. What “Daily Briefing” actually does

**User experience:**

* From Dashboard:

  * Button: **“Generate daily briefing”**
* From Chat:

  * User: “What should I work on today?” / “Give me a daily plan”

**Behavior (v1):**

For a given date (default = today):

1. Collect:

   * Overdue tasks
   * Tasks due that day
   * Events for that day
   * Recent notes (e.g. last 24–72h)

2. Feed that into OpenAI with a structured prompt.

3. Get back a **Markdown briefing** like:

   * Overview
   * Top priorities
   * Today’s schedule
   * Notes to review

4. Return that to:

   * Dashboard (to render in a briefing card)
   * Chat (as an assistant message in the current conversation)

5. Include **references** (task IDs, event IDs, note IDs) so UI can highlight the source items.

---

## 2. API contract (FastAPI)

### 2.1 Endpoint: `/ai/daily-briefing`

**Request (from Dashboard or Chat):**

```jsonc
POST /api/ai/daily-briefing
{
  "date": "2025-11-29",
  "options": {
    "include_overdue_tasks": true,
    "include_events": true,
    "include_recent_notes": true,
    "conversation_id": "optional-uuid"  // if triggered from chat
  }
}
```

* `date`: ISO date string, default to “today” if omitted.
* `conversation_id`: optional. If present, we also store the AI output as a chat message in that convo.

**Response:**

```jsonc
{
  "date": "2025-11-29",
  "markdown": "## Overview\n...\n",
  "references": {
    "tasks": [
      { "id": "task-1", "title": "Finish Atlas schema" },
      { "id": "task-2", "title": "Review CRE notes" }
    ],
    "events": [
      { "id": "event-1", "title": "Client call – CRE site selection" }
    ],
    "notes": [
      { "id": "note-1", "title": "Atlas Architecture" }
    ]
  },
  "model": "gpt-4.1-mini",
  "conversation_id": "optional-uuid-if-logged"
}
```

Dashboard can just render `markdown` and show linked items based on `references`.

---

## 3. Data gathering logic

### 3.1 Tasks selection

For a target date `D`:

* **Overdue tasks**:

  * `status in ('todo','in_progress')`
  * `due_date < D` (midnight boundary)
* **Due today**:

  * `status in ('todo','in_progress')`
  * `due_date` between `[D 00:00, D 23:59:59]`

Pseudo-SQL:

```sql
SELECT * FROM tasks
WHERE status IN ('todo', 'in_progress')
  AND due_date IS NOT NULL
  AND due_date::date < :date;  -- overdue

SELECT * FROM tasks
WHERE status IN ('todo', 'in_progress')
  AND due_date::date = :date;  -- due today
```

You’ll probably wrap that in a repo function:

```python
def get_overdue_tasks(db, date: date) -> list[Task]: ...
def get_tasks_due_on(db, date: date) -> list[Task]: ...
```

### 3.2 Events selection

Events happening on `D`:

```sql
SELECT * FROM events
WHERE start_time::date = :date
   OR end_time::date = :date;
```

(You can refine to true overlaps, but v1 can be date-based.)

### 3.3 Recent notes

Notes updated in last N days (e.g., 3 days) relative to `D`:

```sql
SELECT * FROM notes
WHERE updated_at >= :date - INTERVAL '3 days'
ORDER BY updated_at DESC
LIMIT 20;
```

Then trim to something like 5–10 most relevant (you can tune).

---

## 4. Context shaping for the model

We don’t want to shovel raw DB rows; we want compact, human-like context.

### 4.1 Shape tasks

For each task, create a short line:

```text
[High] Finish Atlas schema (due 2025-11-30) — tags: atlas, planning
```

Structure in Python:

```python
def format_task_for_briefing(task: Task) -> str:
    prio = {"low": "Low", "medium": "Med", "high": "High"}.get(task.priority, "Med")
    due_str = task.due_date.date().isoformat() if task.due_date else "no due date"
    tags = ", ".join(task.tags) if task.tags else "no tags"
    return f"[{prio}] {task.title} (due {due_str}) — tags: {tags}"
```

### 4.2 Shape events

```text
14:00–15:00 — Client call – CRE site selection (Zoom)
```

### 4.3 Shape notes

Just enough to remind the model what they are:

```text
- Atlas Architecture — high-level design of the desktop app
- CRE Data Center Requirements — power, fiber, zoning, and lot selection criteria
```

You can take either the first line of content or a precomputed “one-liner” if you add that later.

---

## 5. Prompt template

In `prompts.py`:

```python
DAILY_BRIEFING_TEMPLATE = """You are Atlas, a local-first personal productivity assistant.

The user wants a concise daily briefing for {date}.

You are given:
- A list of overdue tasks.
- A list of tasks due today.
- A list of events scheduled for today.
- A list of recently updated notes.

Using ONLY this information:

1. Start with a short friendly overview (1–2 sentences).
2. List the top 3–5 priorities for the day, referencing task titles explicitly.
3. Summarize today’s schedule based on the events.
4. Optionally highlight any important themes or follow-ups from the recent notes.

Make the output helpful but not overwhelming.

Return the result as Markdown with these headings exactly:
- "## Overview"
- "## Top Priorities"
- "## Today’s Schedule"
- "## Notes to Review" (include this even if it’s just "None today")

Here is the context:

[Overdue tasks]
{overdue_tasks_block}

[Tasks due today]
{due_today_tasks_block}

[Events today]
{events_block}

[Recent notes]
{notes_block}
"""
```

The orchestrator will `.format()` those placeholders with the formatted blocks:

```python
overdue_tasks_block = "\n".join(f"- {format_task_for_briefing(t)}" for t in overdue_tasks) or "None"
```

---

## 6. Orchestrator implementation (skeleton)

In `orchestrator.py`:

```python
from datetime import date as date_type
from .client import openai_chat
from .prompts import DAILY_BRIEFING_TEMPLATE
from ..db import repo  # whatever your DB access layer is

async def generate_daily_briefing(db, date: date_type, options: DailyBriefingOptions) -> DailyBriefingResult:
    # 1) Load data
    overdue_tasks = []
    due_today_tasks = []
    events_today = []
    recent_notes = []

    if options.include_overdue_tasks:
        overdue_tasks = await repo.get_overdue_tasks(db, date)

    if options.include_overdue_tasks or options.include_events:
        due_today_tasks = await repo.get_tasks_due_on(db, date)

    if options.include_events:
        events_today = await repo.get_events_on(db, date)

    if options.include_recent_notes:
        recent_notes = await repo.get_recent_notes(db, reference_date=date, days=3)

    # 2) Shape context blocks
    overdue_tasks_block = "\n".join(
        f"- {format_task_for_briefing(t)}" for t in overdue_tasks
    ) or "None"

    due_today_tasks_block = "\n".join(
        f"- {format_task_for_briefing(t)}" for t in due_today_tasks
    ) or "None"

    events_block = "\n".join(
        f"- {format_event_for_briefing(e)}" for e in events_today
    ) or "None"

    notes_block = "\n".join(
        f"- {n.title}" for n in recent_notes
    ) or "None"

    # 3) Build prompt
    prompt = DAILY_BRIEFING_TEMPLATE.format(
        date=date.isoformat(),
        overdue_tasks_block=overdue_tasks_block,
        due_today_tasks_block=due_today_tasks_block,
        events_block=events_block,
        notes_block=notes_block,
    )

    # 4) Call OpenAI
    model = "gpt-4.1-mini"  # or from settings
    response_text = await openai_chat(
        model=model,
        system_prompt=None,  # template already includes meta-instructions
        user_content=prompt,
    )

    # 5) Build references
    refs = {
        "tasks": [{"id": t.id, "title": t.title} for t in overdue_tasks + due_today_tasks],
        "events": [{"id": e.id, "title": e.title} for e in events_today],
        "notes": [{"id": n.id, "title": n.title} for n in recent_notes],
    }

    return DailyBriefingResult(
        date=date,
        markdown=response_text,
        model=model,
        references=refs,
    )
```

**`openai_chat`** is your thin wrapper over the OpenAI API (with model, temperature, etc.).

---

## 7. Connecting it to the FastAPI route

In `routers/ai.py`:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import date
from ..db.session import get_db
from ..ai import orchestrator
from ..models import ConversationRepo  # pseudo

router = APIRouter(prefix="/ai", tags=["ai"])

class DailyBriefingOptions(BaseModel):
    include_overdue_tasks: bool = True
    include_events: bool = True
    include_recent_notes: bool = True
    conversation_id: str | None = None

class DailyBriefingRequest(BaseModel):
    date: date | None = None
    options: DailyBriefingOptions = DailyBriefingOptions()

class DailyBriefingResponse(BaseModel):
    date: date
    markdown: str
    references: dict
    model: str
    conversation_id: str | None = None

@router.post("/daily-briefing", response_model=DailyBriefingResponse)
async def daily_briefing(
    req: DailyBriefingRequest,
    db = Depends(get_db),
):
    target_date = req.date or date.today()

    result = await orchestrator.generate_daily_briefing(
        db=db,
        date=target_date,
        options=req.options,
    )

    conversation_id = req.options.conversation_id
    if conversation_id:
        # Optionally log this as a chat message in the given conversation
        await ConversationRepo.log_assistant_message(
            db,
            conversation_id=conversation_id,
            content=result.markdown,
            model=result.model,
            references=result.references,
            kind="daily_briefing"
        )

    return DailyBriefingResponse(
        date=target_date,
        markdown=result.markdown,
        references=result.references,
        model=result.model,
        conversation_id=conversation_id,
    )
```

Now Dashboard and Chat can both hit this same route.

---

## 8. How Dashboard uses it

**Flow:**

1. Dashboard loads `/dashboard/today` (tasks/events/notes summary) as usual.
2. When user clicks **“Generate briefing”**:

   * Frontend `POST /api/ai/daily-briefing` with today’s date
   * Display:

     * A loading spinner in a “Daily Briefing” card
     * Then render the returned markdown in a markdown viewer
   * UI also:

     * Shows chips/buttons for referenced tasks/events/notes (using `references`)

Optional: “Pin briefing as note” button that:

* `POST /notes` with `title: "Daily Briefing 2025-11-29"`, `content: markdown`
* Possibly link tasks/events back to that note.

---

## 9. How Chat uses it

In chat, you have two options:

1. **Implicit**: Use intent classification (later) to detect “what should I work on today?” and call this orchestrator behind the scenes.
2. **Explicit** (v1): Chat UI shows a small “Use daily briefing” helper when user types something like “daily briefing”.

Implementation for explicit:

* Chat component calls `POST /ai/daily-briefing` with `conversation_id`.
* The route logs the assistant message in the conversation.
* Chat UI appends the markdown as the assistant’s reply.

No need to use the generic `/conversations/{id}/messages` path for this specific mode in v1; you can treat it as a shortcut.

---

## 10. Error handling & fallbacks

* If OpenAI call fails:

  * Return a minimal fallback:

    ```markdown
    ## Overview
    I wasn’t able to generate an AI briefing right now.

    ## Top Priorities
    - {some key tasks listed directly from DB}

    ## Today’s Schedule
    - {events from DB}

    ## Notes to Review
    - {recent notes from DB}
    ```

  * Include a `fallback: true` flag in the response so UI can show a subtle warning.

* If there are no tasks/events at all:

  * Acknowledge it:

    > “You have no scheduled events or tasks today. You might want to add…”

---

This gives you a **fully specified, end-to-end design** for one AI feature:

* API contract
* DB access patterns
* Context shaping
* Prompt template
* Orchestrator & route skeleton
* Dashboard + Chat integration
* Error handling

Next, we can either:

* Do the same level of detail for **Dev Assistant** (AI + code/terminal), or
* Start **implementing** some of this in concrete Python (FastAPI + OpenAI client) so you have real code to drop into `backend/`.


Alright, let’s give the **Dev Assistant** the same treatment we gave Daily Briefing.

Think of this as the spec for a **local, project-aware coding assistant** that lives inside your Dev Workspace.

---

## 1. What the Dev Assistant actually does

**User-facing jobs in v1:**

From the Dev Workspace, the user can:

1. **Explain code**

   * “What does this function / file do?”

2. **Suggest a refactor**

   * “How can I clean up this section?”

3. **Generate tests**

   * “Give me tests for this function/module.”

4. **Interpret terminal output**

   * “Why did my tests fail? What should I try next?”

All of these are **read-only suggestions** in v1:

* AI **never edits files directly**
* AI **never runs commands**
* It only suggests code/commands; the user applies them via the editor/terminal.

---

## 2. API contract: `/ai/dev/assist`

### 2.1 Request shape

```jsonc
POST /api/ai/dev/assist
{
  "project_id": "uuid",
  "mode": "explain_code", // "explain_code" | "suggest_refactor" | "generate_tests" | "interpret_terminal_output",
  "file_path": "src/app/main.py",
  "language": "python", // optional hint
  "code": "def foo():\n    ...",
  "selection": {
    "start_line": 10,
    "end_line": 35
  },
  "terminal_output": "pytest failed with ...",   // optional, used for interpret_terminal_output
  "extra_context": "User typed notes, optional"  // optional free-text
}
```

Notes:

* `project_id`: must correspond to a Project in DB (so dev assistant can pull project name, maybe other metadata).
* `file_path`: relative to `project.root_path`. Used for prompt.
* `code`: full file content as seen by the editor (so backend doesn’t have to touch the FS).
* `selection`: optional; when present, prompts focus on that region.
* `terminal_output`: only needed for `interpret_terminal_output`.
* `extra_context`: optional text for anything you don’t want to bake into prompts yet.

### 2.2 Response shape

Standardized across all modes:

```jsonc
{
  "mode": "explain_code",
  "project_id": "uuid",
  "file_path": "src/app/main.py",

  "message": "High-level explanation or guidance.",
  "code_suggestion": {
    "type": "replacement",  // "replacement" | "addition" | "none"
    "language": "python",
    "target": {
      "start_line": 10,
      "end_line": 35     // the region this patch applies to
    },
    "code": "def foo(...):\n    # refactored code\n    ..."
  },
  "suggested_commands": [
    "pytest -k test_main",
    "ruff src/app/main.py"
  ],

  "model": "gpt-4.1-mini"
}
```

* `message`: the main human-readable explanation (“Here’s what’s going on…”).
* `code_suggestion`:

  * For `explain_code`: might be `type: "none"` or a small example.
  * For `suggest_refactor` / `generate_tests`: usually `type: "replacement"` or `type: "addition"`.
* `suggested_commands`: for dev workflow suggestions (run tests, linters, etc.).

The Dev Workspace UI decides how to present this:

* Show `message` in a side panel.
* Show `code_suggestion.code` in a diff/viewer with an “Apply” button (still v1 manual).
* Show commands with an “Insert into terminal” button (doesn’t auto-run).

---

## 3. Data gathering & context shaping

The Dev Assistant doesn’t need to query DB heavy like daily briefing, but it does pull some metadata.

### 3.1 Project info (from DB)

From `project_id`, you can fetch:

* `name`: e.g., “Atlas Desktop”
* `root_path`: for context string, not for code reading (code is passed from UI).

Optional: also fetch linked notes/tasks to mention in prompt later (v2+). For v1, not required.

### 3.2 Code & selection

Renderer sends:

* `code`: full file content (string)
* `selection`:

  * `start_line`, `end_line` (1-based or 0-based, but be consistent)

You can derive a **selected snippet**:

```python
def extract_selected_code(code: str, selection: Selection | None) -> tuple[str, int, int]:
    lines = code.splitlines()
    if not selection:
        return code, 1, len(lines)
    start = max(selection.start_line, 1)
    end = min(selection.end_line, len(lines))
    snippet = "\n".join(lines[start-1:end])
    return snippet, start, end
```

This lets you decide:

* Pass the **whole file** but emphasize the selected part in the prompt, or
* Pass **only the selected code** for brevity.

For v1, I’d pass both:

* Whole file as background (if not huge)
* Selected snippet highlighted as the focus.

### 3.3 Terminal output

Only relevant for `interpret_terminal_output`:

* Renderer can send either:

  * Last N lines from the terminal buffer (e.g., 50–200 lines), or
  * A trimmed version with only the error region.

Backend just needs a clean string.

---

## 4. Prompt templates (per mode)

In `prompts.py`.

### 4.1 Shared header

```python
DEV_ASSISTANT_HEADER = """You are Atlas Dev, a senior software engineer assisting the user with their local project.

Project name: {project_name}
File path: {file_path}

Follow these rules:
- Prefer clear, concise explanations.
- Do not assume any tools beyond what’s in the code or terminal output.
- Do not say you executed commands; you can only suggest them.
- Be explicit about risks when suggesting changes."""
```

Use this as the base for all modes.

---

### 4.2 Mode: `explain_code`

````python
EXPLAIN_CODE_TEMPLATE = DEV_ASSISTANT_HEADER + """

The user wants to understand this code.

Full file content:

```{language}
{full_code}
````

The primary focus is the region from lines {start_line} to {end_line}:

```{language}
{selected_code}
```

Tasks:

1. Explain what this selected region does in clear language.
2. Mention any noteworthy edge cases, error paths, or assumptions.
3. Optionally suggest small improvements, but do not rewrite the entire file.

Respond in Markdown. Start with a short summary paragraph, then use bullet points where helpful."""

````

---

### 4.3 Mode: `suggest_refactor`

```python
SUGGEST_REFACTOR_TEMPLATE = DEV_ASSISTANT_HEADER + """

The user wants to refactor the selected region of this file to improve clarity and maintainability.

Full file content:

```{language}
{full_code}
````

Selected region (lines {start_line}–{end_line}):

```{language}
{selected_code}
```

Tasks:

1. Briefly describe the main issues with the current implementation (if any).
2. Propose a refactored version of ONLY the selected region.
3. Preserve the public behavior and signatures (unless clearly unsafe).

Return your answer as JSON with this structure:

```json
{
  "message": "High-level explanation of the refactor.",
  "code_suggestion": {
    "type": "replacement",
    "language": "{language}",
    "target": {
      "start_line": {start_line},
      "end_line": {end_line}
    },
    "code": "refactored code here"
  },
  "suggested_commands": ["optional command", "another command"]
}
```

Make sure the JSON is valid."""

````

Here, you explicitly use JSON output so you can parse it into your response model.

---

### 4.4 Mode: `generate_tests`

```python
GENERATE_TESTS_TEMPLATE = DEV_ASSISTANT_HEADER + """

The user wants to generate tests for the selected code.

Full file content:

```{language}
{full_code}
````

Selected region (lines {start_line}–{end_line}):

```{language}
{selected_code}
```

Assume the project uses a conventional testing stack (for Python, pytest; for JavaScript, jest/vitest; etc.)

Tasks:

1. Identify what behavior should be tested.
2. Provide example test cases that cover typical and edge cases.
3. Organize tests into a single code block that can be pasted into a test file.
4. Suggest a test command the user can run.

Return JSON with:

````json
{
  "message": "Explanation of what the tests cover.",
  "code_suggestion": {
    "type": "addition",
    "language": "{test_language}",
    "target": {
      "start_line": 0,
      "end_line": 0
    },
    "code": "test code here"
  },
  "suggested_commands": ["pytest -k test_file", "npm test -- my-test"]
}
```"""
````

---

### 4.5 Mode: `interpret_terminal_output`

````python
INTERPRET_TERMINAL_TEMPLATE = DEV_ASSISTANT_HEADER + """

The user ran a command in the terminal and got this output:

```txt
{terminal_output}
````

If relevant, here is the selected region of code they were working on:

```{language}
{selected_code}
```

Tasks:

1. Explain in plain language what went wrong.
2. Suggest up to 3 specific things they can try to fix or diagnose the issue.
3. Suggest up to 3 commands they could run next (if appropriate).

Return JSON with:

````json
{
  "message": "Explanation and guidance.",
  "code_suggestion": {
    "type": "none",
    "language": "{language}",
    "target": null,
    "code": ""
  },
  "suggested_commands": ["..."]
}
```"""
````

---

## 5. Orchestrator implementation (skeleton)

In `orchestrator.py`:

```python
from .client import openai_chat_json, openai_chat_text
from .prompts import (
    EXPLAIN_CODE_TEMPLATE,
    SUGGEST_REFACTOR_TEMPLATE,
    GENERATE_TESTS_TEMPLATE,
    INTERPRET_TERMINAL_TEMPLATE,
)
from ..db import repo

class DevAssistMode(str, Enum):
    EXPLAIN_CODE = "explain_code"
    SUGGEST_REFACTOR = "suggest_refactor"
    GENERATE_TESTS = "generate_tests"
    INTERPRET_TERMINAL_OUTPUT = "interpret_terminal_output"

async def dev_assist(db, payload: DevAssistRequest) -> DevAssistResult:
    project = await repo.get_project(db, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    full_code = payload.code or ""
    selected_code, start_line, end_line = extract_selected_code(full_code, payload.selection)
    language = payload.language or guess_language(payload.file_path)

    base_kwargs = dict(
        project_name=project.name,
        file_path=payload.file_path,
        language=language,
        full_code=full_code,
        selected_code=selected_code,
        start_line=start_line,
        end_line=end_line,
    )

    mode = DevAssistMode(payload.mode)

    if mode == DevAssistMode.EXPLAIN_CODE:
        prompt = EXPLAIN_CODE_TEMPLATE.format(**base_kwargs)
        text = await openai_chat_text(model="gpt-4.1-mini", user_content=prompt)
        # Wrap into DevAssistResult with no structured code suggestion
        return DevAssistResult(
            mode=mode.value,
            project_id=project.id,
            file_path=payload.file_path,
            message=text,
            code_suggestion=CodeSuggestion.none(language),
            suggested_commands=[],
            model="gpt-4.1-mini",
        )

    elif mode == DevAssistMode.SUGGEST_REFACTOR:
        prompt = SUGGEST_REFACTOR_TEMPLATE.format(**base_kwargs)
        json_resp = await openai_chat_json(model="gpt-4.1-mini", user_content=prompt)
        return DevAssistResult(
            mode=mode.value,
            project_id=project.id,
            file_path=payload.file_path,
            message=json_resp["message"],
            code_suggestion=CodeSuggestion.from_json(json_resp["code_suggestion"]),
            suggested_commands=json_resp.get("suggested_commands", []),
            model="gpt-4.1-mini",
        )

    elif mode == DevAssistMode.GENERATE_TESTS:
        test_lang = infer_test_language(language)
        prompt = GENERATE_TESTS_TEMPLATE.format(
            **base_kwargs,
            test_language=test_lang,
        )
        json_resp = await openai_chat_json(model="gpt-4.1-mini", user_content=prompt)
        return DevAssistResult(
            mode=mode.value,
            project_id=project.id,
            file_path=payload.file_path,
            message=json_resp["message"],
            code_suggestion=CodeSuggestion.from_json(json_resp["code_suggestion"]),
            suggested_commands=json_resp.get("suggested_commands", []),
            model="gpt-4.1-mini",
        )

    elif mode == DevAssistMode.INTERPRET_TERMINAL_OUTPUT:
        prompt = INTERPRET_TERMINAL_TEMPLATE.format(
            **base_kwargs,
            terminal_output=payload.terminal_output or "",
        )
        json_resp = await openai_chat_json(model="gpt-4.1-mini", user_content=prompt)
        return DevAssistResult(
            mode=mode.value,
            project_id=project.id,
            file_path=payload.file_path,
            message=json_resp["message"],
            code_suggestion=CodeSuggestion.from_json(json_resp["code_suggestion"]),
            suggested_commands=json_resp.get("suggested_commands", []),
            model="gpt-4.1-mini",
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mode {payload.mode}")
```

Where:

* `openai_chat_text` → returns plain string.
* `openai_chat_json` → uses `response_format` to enforce JSON and parses it.

---

## 6. FastAPI route

In `routers/ai_dev.py` or grouped under `ai.py`:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..db.session import get_db
from ..ai.orchestrator import dev_assist

router = APIRouter(prefix="/ai/dev", tags=["ai-dev"])

class Selection(BaseModel):
    start_line: int
    end_line: int

class DevAssistRequest(BaseModel):
    project_id: str
    mode: str
    file_path: str
    language: str | None = None
    code: str
    selection: Selection | None = None
    terminal_output: str | None = None
    extra_context: str | None = None

class CodeSuggestionModel(BaseModel):
    type: str  # replacement | addition | none
    language: str
    target: dict | None = None
    code: str

class DevAssistResponse(BaseModel):
    mode: str
    project_id: str
    file_path: str
    message: str
    code_suggestion: CodeSuggestionModel
    suggested_commands: list[str]
    model: str

@router.post("/assist", response_model=DevAssistResponse)
async def dev_assist_endpoint(
    payload: DevAssistRequest,
    db = Depends(get_db),
):
    result = await dev_assist(db, payload)
    return DevAssistResponse(**result.model_dump())
```

---

## 7. Dev Workspace UI flow

**Example: “Explain selection” button**

1. User selects a region in the editor.
2. Clicks **“Dev Assistant → Explain selection”**.
3. Renderer gathers:

   * `project_id` (from Dev Workspace state)
   * `file_path` (from open tab)
   * `code` (full editor buffer)
   * `selection` (line numbers)
4. `POST /api/ai/dev/assist` with `mode: "explain_code"`.
5. Show loading indicator in a side panel.
6. Render `response.message` as Markdown when ready.
7. If `code_suggestion.type !== "none"`, show a “Suggested code” expandable section.

**Example: “Suggest refactor”**

Same as above, but `mode: "suggest_refactor"`:

* After response:

  * Show `message` and a diff viewer with `code_suggestion.code` vs selected region.
  * Provide an “Apply to editor” button (v1: manual; you can later add an IPC/apply hook).

**Example: “Explain test failure”**

1. User clicks “Send last output to Dev Assistant” in the terminal.
2. Renderer sends:

   * `terminal_output` (captured buffer)
   * Current file selection (optional)
3. Backend `mode: "interpret_terminal_output"` returns message + suggested commands.
4. UI:

   * Shows explanation.
   * Renders a list of suggested commands with “Insert into terminal” buttons.

---

## 8. Safety & scope constraints

* AI **never executes** commands; only suggests.
* AI **never writes files** directly; only suggests patches.
* Renderer must:

  * Only send code that the user has open (or explicitly selected).
  * Only apply code changes when user confirms.

---

This gives you an end-to-end, detailed spec for the **Dev Assistant**:

* UX behavior
* API shape
* Prompt templates
* Orchestrator and route skeletons
* Concrete UI interaction patterns

If you’d like, next step we can:

* Turn the OpenAI client wrapper (`openai_chat_text` / `openai_chat_json`) into concrete code, or
* Start sketching the React Dev Workspace components (how they call `/ai/dev/assist`, how they render suggestions, etc.).
