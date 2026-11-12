# VOID AI Tools & Agentic Decomposition Guide

VOID integrates with both Ollama's `lfm3-omni:2b` function calling specification and the 105 tools installed in Dodaios.

---

## 1. Primary AI Tool Schemas (16 Core Tools)

When the AI brain is active, VOID exposes the following tool schemas:

### 1. `search_web`
- **Description:** Live web search via DuckDuckGo.
- **Parameters:** `query` (string)
- **Output:** Top search snippets and source URLs.

### 2. `web_scrape_deep_research`
- **Description:** Fetches live web pages or conducts multi-source topic research.
- **Parameters:** `url` (optional string), `topic` (optional string)
- **Output:** Cleaned plaintext paragraphs (scripts/styles removed) up to 1,500 characters.

### 3. `take_screenshot`
- **Description:** Captures active desktop screen to `~/Pictures/Screenshots/`.
- **Parameters:** `filename` (optional string)
- **Output:** Absolute path to saved `.jpg` file.

### 4. `open_application`
- **Description:** Launches software (Chromium, Firefox, Konsole, Dolphin, KCalc, KWrite, etc.) or opens a URL in Chromium.
- **Parameters:** `app_name` (string), `url` (optional string)

### 5. `close_application`
- **Description:** Closes software by process name.
- **Parameters:** `app_name` (string)

### 6. `manage_window`
- **Description:** Controls KDE Plasma windows via KWin DBus & Wayland Scripting.
- **Parameters:** `action` ("close", "minimize", "maximize", "fullscreen", "show_desktop"), `app_name` (optional string)

### 7. `run_safe_command`
- **Description:** Executes read-only, non-destructive Linux terminal commands (`date`, `uptime`, `free -h`, `df -h`, `uname -a`).
- **Safety Boundary:** Strictly blocks `sudo`, `su`, `rm -rf`, `dd`, `mkfs`, and system-level directories.
- **Parameters:** `command` (string)

### 8. `calculate`
- **Description:** Mathematical evaluation using safe AST parsing.
- **Parameters:** `expression` (string)

### 9. `set_timer`
- **Description:** Starts a desktop countdown timer with visual progress and audio chimes.
- **Parameters:** `seconds` (integer)

### 10. `search_files`
- **Description:** Searches for files in `~/Documents` or specified user directories using regex/glob pattern matching.
- **Safety Boundary:** Restricts searching to `/home/prakash/`.
- **Parameters:** `pattern` (string), `search_path` (optional string)

### 11. `create_document`
- **Description:** Writes a text, markdown, or note document to disk safely.
- **Safety Boundary:** Enforces writing exclusively within `/home/prakash/`.
- **Parameters:** `path` (string), `content` (string)

### 12. `read_document`
- **Description:** Reads text from a specified document in the user directory.
- **Parameters:** `path` (string)

### 13. `compose_email`
- **Description:** Formats a professional email draft with recipient, subject, and body, saving a `.eml` draft to `~/Documents/Drafts/`.
- **Parameters:** `recipient` (string), `subject` (string), `body` (string), `save_draft` (boolean)

### 14. `security_audit`
- **Description:** Performs a read-only security assessment: open listening ports (`ss -tulpn`), active login sessions (`who`), SELinux enforcement, and firewalld status.
- **Parameters:** None

### 15. `system_status`
- **Description:** Gathers CPU load average, RAM % used/free, root disk space, system uptime, and Ollama model residency.
- **Parameters:** None

### 16. `manage_task`
- **Description:** Persistent task & reminder management in `~/.config/void/tasks.json`.
- **Parameters:** `action` ("add", "list", "complete", "delete"), `task_text` (optional string), `task_id` (optional string)

---

## 2. Multi-Step Agentic Task Decomposition Loop

When a user gives a multi-stage request (e.g., *"Search the web for Linux kernel 6.12 features, create a summary document in Documents/kernel.txt, and set a task to review it"*):

1. **Step 1 (Decomposition):** `lfm3-omni:2b` analyzes the prompt and emits `search_web(query='Linux kernel 6.12 features')`.
2. **Step 2 (Tool Execution):** VOID executes DuckDuckGo search in the background, extracts results, and returns them with role `"tool"`.
3. **Step 3 (Chained Sub-Tasks):** `lfm3-omni:2b` receives the search content and emits two tool calls: `create_document(path='~/Documents/kernel.txt', content=...)` and `manage_task(action='add', task_text='Review kernel summary')`.
4. **Step 4 (Execution & Synthesis):** VOID creates the file and saves the task.
5. **Step 5 (Spoken Summary):** `lfm3-omni:2b` synthesizes a concise, spoken reply:
   *"I have gathered the Linux kernel 6.12 features, saved the summary to Documents/kernel.txt, and added a task to your memory to review it."*

