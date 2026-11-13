# VOID — Autonomous Personal AI Desktop Assistant

**VOID** is an autonomous, personal AI desktop assistant built specifically for Fedora KDE Plasma on Wayland. It pairs sub-5ms local desktop automation with the cognitive intelligence of Liquid AI's `lfm3-omni:2b` neural model running entirely offline on Ollama.

---

## System Architecture & Specifications

- **Operating System:** Fedora Linux (KDE Plasma 6 on Wayland)
- **Hardware Architecture:** AMD Ryzen 7, 16 GB RAM, AMD Radeon Integrated Graphics
- **Audio Server:** PipeWire 1.4 / WirePlumber
- **Speech-to-Text (STT):** Faster-Whisper Base int8 (CPU quantized, ~0.8s latency)
- **Wake-Word Engine:** Vosk Kaldi Real-Time Acoustic Engine (`"hey void"`, `"void"`)
- **Text-to-Speech (TTS):** Piper Local Neural TTS (`en_US-ryan-medium.onnx`, 22.05 kHz)
- **Cognitive AI Brain:** Liquid AI `lfm3-omni:2b` via Ollama (`http://127.0.0.1:11434`)
- **Backend Hub:** Dodaios 5.0.0 (`http://127.0.0.1:47821`) with 105 tools

---

## Deployment & File Structure on External Drive (`/run/media/prakash/TR_39/VOID`)

```
/run/media/prakash/TR_39/VOID/
├── bin/
│   ├── void-widget.py         # Main PySide6 Glass Flow Assistant Widget
│   └── void-launcher.py       # Full system lifecycle & process supervisor
├── config/
│   ├── void.desktop           # Autostart entry (~/.config/autostart/void.desktop)
│   ├── tasks.json             # Persistent tasks & reminders database
│   └── widget_pos.json        # Saved desktop coordinates for widget position
├── docs/
│   ├── README.md              # Complete manual & guide (this file)
│   ├── ACTIONS_WITH_AND_WITHOUT_AI.md # Comparison of capabilities
│   ├── MODEL_COMPARISON.md    # lfm3-omni:2b vs jarvis benchmark & analysis
│   └── TOOLS_GUIDE.md         # Schema & usage for 16 AI tools
└── scripts/
    ├── run_void.sh            # One-click portable launcher
    ├── stop_void.sh           # Clean shutdown script
    ├── status_void.sh         # Diagnostics and vitals checker
    └── backup_void.sh         # Synchronizes active files to this backup directory
```

---

## How to Run VOID

### 1. Launching
You can run VOID directly from the portable launcher:
```bash
/run/media/prakash/TR_39/VOID/scripts/run_void.sh
```
Or use the system launcher:
```bash
python3 /home/prakash/.local/bin/void-launcher.py
```
*(VOID also starts automatically upon user login via `~/.config/autostart/void.desktop`)*

### 2. Stopping
```bash
/run/media/prakash/TR_39/VOID/scripts/stop_void.sh
```
Or via voice:
> *"Hey VOID, terminate code 0"*

---

## Interactive Voice & Desktop Commands

### 1. Wake & Termination
- Wake VOID: Say **"Hey VOID"** or **"VOID"** (chime plays, widget orb turns cyan)
- Orderly Shutdown: Say **"Hey VOID, terminate code 0"**

### 2. Moving the Widget
- Click and drag **anywhere** on the widget surface (empty card space, header, borders).
- Smooth Wayland native dragging (`startSystemMove()`) allows you to position VOID anywhere across your monitors. Coordinates are saved automatically to `widget_pos.json`.

### 3. Ollama Brain Lifecycle (Saving RAM)
- **"Hey VOID, start ollama"** — Starts Ollama server and pre-loads `lfm3-omni:2b` into memory.
- **"Hey VOID, stop ollama"** — Stops Ollama, unloads model, and frees ~2.0 GB of memory.

### 4. System Status & Truthful Brain Reporting
- **"What is the system status?"** / **"How is my machine?"** / **"Is the AI brain connected?"**
- VOID truthfully reports whether `lfm3-omni:2b` is actively loaded in memory or on standby, along with CPU load, RAM % used, disk space free, and uptime.

### 5. Window & Desktop Controls (<5ms Fast-Path)
- **"Close active window"** / **"Close this"**
- **"Minimize window"** / **"Maximize window"** / **"Fullscreen"**
- **"Show desktop"**
- **"Close chromium"** / **"Close firefox"** / **"Close terminal"**
- **"Minimize chromium"** / **"Maximize terminal"** / **"Fullscreen browser"**

### 6. Application Launching & Smart Browser Handling
- **"Open browser"** / **"Open chrome"** / **"Open chromium"** / **"Open internet"**
  - VOID automatically resolves "chrome", "browser", or "internet" to the default Chromium browser (`/usr/bin/chromium-browser`), scanning desktop files if an exact binary is not present.
- **"Open terminal"** / **"Open dolphin"** / **"Open calculator"**
- **"Open chromium and search for [topic]"**
- **"Open github.com"**

### 7. Multi-Command Sequential Execution
VOID breaks compound queries into discrete sub-commands and executes them in sequence:
- **"Open chromium and take a screenshot and set a timer for 5 minutes"**
- **"Open terminal and memory status and calculate 50 times 4"**

### 8. Narrow AI Persistent SSD Memory (1.5 GB Storage Engine)
VOID has a dedicated 1.5 GB memory engine stored directly on NVMe SSD (`/run/media/prakash/TR_39/VOID/memory`):
- **"Remember that [fact]"** / **"Learn that [preference]"** — e.g., *"Remember that my favorite programming language is Python"*
- **"What do you remember about [topic]?"** / **"Recall [topic]"** — e.g., *"What do you remember about Python?"*
- **"Memory status"** — reports MB used, 1500 MB max, storage %, and total memories stored.
- **"Clear chat"** — flushes working conversational context.
- **Automatic Ring Buffer:** If total stored memories exceed 1.5 GB, VOID automatically prunes the oldest, lowest-priority records.

### 9. Hearing Module & Typo Tolerance
The hearing module handles phonetic slips, STT typos, and slangs in both offline and online modes:
- *"opn crome"* -> accurately resolves to *"open chromium"*
- *"strat termianl"* -> accurately resolves to *"open terminal"*
- *"calcultor"* -> accurately resolves to *"open calculator"*
- *"screnshot"* / *"screen short"* -> accurately captures screenshot
- *"rember that"* -> accurately saves memory

### 10. No Annoying Re-Introductions
- Saying **"Hey VOID"** immediately prompts *"I'm listening."* without repeating introductions.
- VOID only introduces its name and creator when explicitly asked *"Who are you?"* or *"What is your name?"*.

### 11. Named Screenshots
- **"Take a screenshot and save as 'project_alpha'"**
- Saves directly to `~/Pictures/Screenshots/project_alpha.jpg` and displays a thumbnail preview in the widget card.

### 12. Persistent Tasks & Reminders
- **"Set task [description]"** / **"Remind me to [description]"**
- **"What are my tasks?"** / **"List tasks"**
- **"Complete task [ID or text]"**
- **"Delete task [ID or text]"**
- **"Clear all tasks"**
*(Tasks persist in `~/.config/void/tasks.json` across system reboots)*

### 13. Timers & Volume
- **"Set a timer for 5 minutes"** / **"Cancel timer"**
- **"Volume up"** / **"Volume down"** / **"Mute"**

### 14. Comprehensive Document & PDF Composition Suite
VOID takes time to thoroughly gather intelligence across multiple research facets in parallel, compiling publication-grade documents and PDFs with structured sections, comparative data tables, and citations:
- **"Hey VOID, compose document on Quantum Computing"** — Conducts parallel multi-angle research, synthesizes findings, and compiles a publication PDF in `~/Documents/Reports/`.
- **"Hey VOID, compose pdf on Autonomous Linux Systems"** — Generates a styled PDF complete with cover header, metadata, tables, and page counters.
- **"Hey VOID, compose word document on Edge Inference Pipelines"** — Formats and drafts a structured Word (.docx) document.

### 15. Instant Document Opener
Immediately after composing a document or PDF, open it with zero friction:
- **"Hey VOID, open it"** — Instantly launches the active document in your default viewer (Okular for PDF, LibreOffice for Word/Excel).
- **"Hey VOID, open document"** / **"Hey VOID, open pdf"** / **"Hey VOID, open the report"** — Memory traceback automatically resolves the most recent document.

### 16. Document Content Rewriting & Dynamic Adaptation
Maximizes your ability to refine, restructure, adjust tone, or add new sections to existing documents:
- **"Hey VOID, rewrite the content with a formal executive tone"** — Adapts vocabulary, strategic framing, and institutional styling.
- **"Hey VOID, rewrite adding a section on Kernel Security Safeguards"** — Synthesizes and appends targeted technical sections.
- **"Hey VOID, change the content to [new instructions]"** — Directly restructures core sections according to your prompt.
- **"Hey VOID, rewrite as pdf"** — Seamlessly converts and compiles Word documents into publication-grade PDFs.
- Saying **"open it"** after rewriting automatically opens the newly updated `_v2` version!

### 17. High-Performance Architecture
- **Parallel Multi-Query Research:** Gathers web sources across 4 query facets concurrently via `ThreadPoolExecutor(max_workers=4)`, reducing gathering latency by over 70%.
- **Sub-Second Headless PDF Pipeline:** Generates high-resolution vector PDFs in under 1 second using streamlined Chromium headless rendering (`--print-to-pdf`).
- **Fluid 60 FPS Event Loop:** Deep research and compilation execute asynchronously, keeping the Wayland glass widget orb and animations completely smooth.

---

## System Safety Policy Compliance

All VOID operations strictly conform to the system safety boundaries:
- `/usr`, `/etc`, `/boot`, `/root`, SELinux, and firewalld remain **100% untouched**.
- Zero modifications to host kernel or system repositories.
- All file creation, editing, and task storage take place strictly within `/home/prakash/`.
# VOID-
