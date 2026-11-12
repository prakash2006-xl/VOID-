# VOID Capabilities: Actions With AI vs Actions Without AI

VOID is engineered with a dual-tier architecture:
1. **Tier 1 (Sub-5ms Local Fast Path - Without AI):** Zero latency, zero GPU/VRAM load, deterministic execution. Functions 100% locally even when Ollama is completely offline or stopped.
2. **Tier 2 (Cognitive Agentic Brain - With AI):** Powered by Liquid AI's `lfm3-omni:2b` via Ollama, equipped with iterative tool-calling and multi-step task decomposition.

---

## 1. Actions VOID Can Perform WITHOUT AI (Local Fast-Path)

When the AI brain is sleeping or Ollama is stopped, VOID instantly handles the following commands in **less than 5 milliseconds** using native system calls, DBus, and local regex dispatch:

| Action Category | Example Voice / Chat Commands | Underlying Mechanism |
| :--- | :--- | :--- |
| **Window Controls (Active)** | `"close active window"`, `"close window"`, `"close this"` | `kwin_shortcut("Window Close")` |
| | `"minimize active window"`, `"minimize window"` | `kwin_shortcut("Window Minimize")` |
| | `"maximize active window"`, `"fullscreen"` | `kwin_shortcut("Window Maximize / Fullscreen")` |
| | `"show desktop"`, `"minimize all"` | `kwin_shortcut("Show Desktop")` |
| **Targeted Window Controls** | `"close chromium"`, `"close firefox"`, `"close konsole"` | Process match & graceful kill via `pkill` |
| | `"minimize chromium"`, `"maximize terminal"`, `"fullscreen browser"` | KWin Wayland Scripting (`workspace.windowList()`) |
| **Application Launching** | `"open chromium"`, `"launch firefox"`, `"open terminal"` | Fast subprocess spawn via system PATH |
| | `"open dolphin"`, `"open calculator"`, `"open text editor"` | Native KDE Plasma binaries (`kcalc`, `kwrite`) |
| **Smart Browser Navigation**| `"open chromium and search for quantum mechanics"` | Direct URL generation and Chromium spawn |
| | `"search machine learning in browser"`, `"open github.com"` | Native Wayland Ozone browser integration |
| **Instant Screenshots** | `"take a screenshot"`, `"capture screen"`, `"grab screen"` | KDE Spectacle background capture |
| | `"take a screenshot and save as 'project_review'"` | Direct named file write to `~/Pictures/Screenshots/` |
| **System & Brain Truthfulness**| `"status"`, `"system status"`, `"how is my machine"` | Reads `/proc/meminfo`, `/proc/loadavg`, `/proc/uptime`, `os.statvfs` |
| | `"is the ai brain connected"`, `"brain status"` | Inspects Ollama `http://127.0.0.1:11434/api/ps` model residency |
| **Task Management** | `"set task buy groceries"`, `"add reminder to finish code"` | Persistent `~/.config/void/tasks.json` storage |
| | `"what are my tasks"`, `"list tasks"`, `"my tasks"` | Instant active tasks enumeration |
| | `"complete task T2"`, `"done with task review paper"` | Status update with ISO completion timestamps |
| | `"delete task T1"`, `"clear all tasks"` | Deterministic task database mutation |
| **Ollama Brain Lifecycle** | `"hey void, start ollama"`, `"activate brain"` | Starts Ollama daemon, preloads `lfm3-omni:2b` |
| | `"hey void, stop ollama"`, `"deactivate brain"` | Unloads model, frees ~2.0 GB VRAM & system RAM |
| **Hardware & Audio** | `"volume up"`, `"volume down"`, `"mute"` | PipeWire / WirePlumber (`wpctl`) sink control |
| | `"show audio devices"`, `"list microphones"` | Dodaios hardware introspection endpoint |
| **Power & Security** | `"shutdown system"`, `"reboot system"` | 5-second cancelable interactive countdown banner |
| | `"lock screen"`, `"lock computer"` | `loginctl lock-session` |
| **Calculations & Time** | `"calculate 144 * 25"`, `"what is sqrt(625)"` | Safe Python AST evaluator (no `eval()` vulnerability) |
| | `"what time is it"`, `"what is the date"` | Local system clock format |
| **Interactive Timers** | `"set timer for 10 minutes"`, `"timer 45 seconds"` | Native QTimer with visual capsule countdown and audio chime |
| | `"cancel timer"`, `"stop timer"` | Instant timer abort |
| **Safe Terminal Commands** | `"run terminal command uname -a"`, `"execute df -h"` | Safe bash execution; strictly blocks destructive/root paths |
| **Session & Termination** | `"clear chat"`, `"reset memory"` | Flushes dialogue history buffer |
| | `"hey void terminate code 0"` | Orderly assistant shutdown with audio chime |

---

## 2. Actions VOID Can Perform WITH AI (`lfm3-omni:2b` Brain)

When Ollama is started (`"hey void, start ollama"`), VOID activates cognitive reasoning and the **Multi-Step Agentic Loop**:

| Action Category | What VOID Does With The Brain | Integrated AI Tools |
| :--- | :--- | :--- |
| **Multi-Step Complex Tasks** | Decomposes a multi-part command into sequential steps, executes each tool, and synthesizes a spoken summary. | `search_web`, `create_document`, `manage_task` |
| **Live Deep Web Research** | Queries DuckDuckGo for multiple sources, parses web pages, and condenses findings into clean research notes. | `web_scrape_deep_research`, `search_web` |
| **Document Authoring & Reading** | Drafts essays, meeting notes, project summaries, and code snippets directly to `~/Documents/*.md` or reads existing files. | `create_document`, `read_document` |
| **Email Drafting** | Composes professional emails with subject line, greeting, context, and closing, saving drafts to `~/Documents/Drafts/*.eml`. | `compose_email` |
| **Intelligent File Search** | Searches user directories for files based on fuzzy patterns, topics, or extensions. | `search_files` |
| **Security Auditing** | Scans open network sockets (`ss -tulpn`), logged-in users, firewall status, and SELinux enforcement. | `security_audit` |
| **Natural Language Synthesis** | Answers general programming, Linux administration, science, and knowledge queries with concise 1-2 sentence spoken summaries. | Conversational inference |
| **Context Retention (16 Turns)** | Understands pronouns and references from previous dialogue (e.g. "What did we just discuss?", "Search for that in Chromium"). | Rolling `self._chat_history` |

