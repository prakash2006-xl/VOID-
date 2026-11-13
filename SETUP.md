# VOID — Complete Setup, Installation & Deployment Guide

Welcome to the setup documentation for **VOID**, an autonomous, personal AI desktop assistant built specifically for Linux (KDE Plasma 6 on Wayland/X11). VOID combines sub-5ms local desktop automation with the cognitive intelligence of local neural models (Ollama `lfm3-omni:2b`) and flexible cloud models (such as OpenRouter with `perplexity/pplx-decider-flash-v1.3:free`).

---

## Quick Start (One-Click Automated Setup)

You can install all requirements, configure chosen models, optimize CPU/RAM efficiency, and launch VOID with a single command on any Linux system:

```bash
git clone https://github.com/prakash2006-xl/VOID-.git
cd VOID-
./terminalsetuprun
```
*(You can also double-click `terminalsetuprun` or `termialsteuprun` in Dolphin / File Manager).*

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Directory Architecture](#2-directory-architecture)
3. [One-Click Setup Script (`terminalsetuprun`)](#3-one-click-setup-script-terminalsetuprun)
4. [AI Model Configuration & Switching (Local & Cloud)](#4-ai-model-configuration--switching-local--cloud)
5. [VOID Configuration Window & Sizing Presets](#5-void-configuration-window--sizing-presets)
6. [Plugin & Skill Pipeline Architecture](#6-plugin--skill-pipeline-architecture)
7. [Voice Announcements (Short & Sweet)](#7-voice-announcements-short--sweet)
8. [Media & Song Playback on Tabs (Zero Auto-Correction)](#8-media--song-playback-on-tabs-zero-auto-correction)
9. [Performance & Efficiency Optimizations](#9-performance--efficiency-optimizations)
10. [Automated Verification & Test Matrix](#10-automated-verification--test-matrix)
11. [Troubleshooting & Diagnostics](#11-troubleshooting--diagnostics)
12. [System Control & Activities (Power, Telemetry & Automation)](#12-system-control--activities-power-telemetry--automation)

---

## 1. System Requirements

- **Operating System:** Fedora Linux 40+ / Ubuntu 24.04+ / Arch Linux (KDE Plasma 6 Wayland recommended)
- **CPU:** AMD Ryzen 5/7/9 or Intel Core i5/i7/i9 (4+ physical cores)
- **RAM:** 16 GB minimum
- **Graphics:** AMD Radeon / Intel Iris Xe / NVIDIA (Vulkan / ROCm / CUDA compatible)
- **Audio Server:** PipeWire 1.0+ with WirePlumber
- **Storage:** ~10 GB free space on external SSD or root drive

---

## 2. Directory Architecture

All persistent runtime assets, scripts, neural models, and memory databases reside in the external root or designated deployment folder:

```
/run/media/prakash/TR_39/VOID/
├── bin/
│   ├── void-widget.py         # Main PySide6 Glass Flow Desktop Assistant widget
│   └── void-launcher.py       # Full system lifecycle & process supervisor
├── config/
│   ├── ai_providers.json      # Cloud & local model credentials and profiles
│   ├── tasks.json             # Persistent reminders and tasks database
│   └── widget_pos.json        # Saved desktop coordinates
├── agentic/
│   ├── supervisor.py          # Fast-path intent classifier & multi-agent supervisor
│   ├── planner.py             # Hierarchical domain template & LLM planner
│   ├── providers.py           # 4-tier model hierarchy (OpenRouter, Ollama, OpenAI, System)
│   ├── tools.py               # 105 tools registry and safety gating
│   └── ui_components.py       # Config window, agent activity cards, system popups
├── memory/
│   ├── facts.json             # Persistent episodic SSD memory
│   └── weekly_summaries/      # 7-day high-memory digests
├── scripts/
│   ├── run_void.sh            # Dedicated portable launcher
│   ├── stop_void.sh           # Clean shutdown script
│   └── status_void.sh         # Real-time diagnostics checker
├── terminalsetuprun           # One-click executable setup & model configuration
├── termialsteuprun            # Symlink alias for terminalsetuprun
├── README.md                  # Complete technical manual
└── SETUP.md                   # This installation & deployment guide
```

---

## 3. One-Click Setup Script (`terminalsetuprun`)

The `terminalsetuprun` executable automates the entire end-to-end setup across Fedora, Debian, Ubuntu, Arch Linux, and openSUSE:

1. **System Packages:** Detects distribution package manager (`dnf`, `apt`, `pacman`, `zypper`) and provisions essential dependencies (`python3`, `portaudio`, `libsndfile`, `ffmpeg`, `wmctrl`, `xdotool`, `git`, `curl`, `wget`, `unzip`).
2. **Virtual Environment:** Automatically provisions an isolated virtual environment (`~/.dodaios/.venv` or local `.venv`) and installs all required Python packages (`PySide6`, `faster-whisper`, `vosk`, `sounddevice`, `httpx`, `reportlab`, `python-docx`, `openpyxl`, `ddgs`, `sherpa-onnx`).
3. **Efficiency Guard:** Automatically deactivates rogue background dictation workers (`preview_worker large-v3-turbo`) that waste 40-70% CPU and 1.3GB RAM.
4. **Speech Assets:** Checks and downloads Vosk Kaldi acoustic wake-word models and Piper neural TTS voice models from official repositories if missing.
5. **Local LLM Daemon:** Inspects and initializes Ollama, pulling the default local model `lfm3-omni:2b`.
6. **Model Configuration:** Automatically writes chosen models (e.g., OpenRouter `perplexity/pplx-decider-flash-v1.3:free`) and API key into `config/ai_providers.json`.
7. **Autostart & Launch:** Registers `~/.local/share/applications/void.desktop`, creates CLI shortcut `void` in `~/.local/bin/void`, and launches the VOID widget.

### Running with Custom Model Arguments:
```bash
./terminalsetuprun --model "perplexity/pplx-decider-flash-v1.3:free" --key "sk-or-v1-YOUR_KEY_HERE"
# Or dry-run check:
./terminalsetuprun --check
```

---

## 4. AI Model Configuration & Switching (Local & Cloud)

VOID supports local offline inference, cloud APIs, and intelligent hybrid operation:

### Configured Credentials File (`config/ai_providers.json`):
```json
{
  "mode": "hybrid",
  "cloud": {
    "enabled": true,
    "api_base": "https://openrouter.ai/api/v1",
    "api_key": "sk-or-v1-your-openrouter-key-here",
    "model": "perplexity/pplx-decider-flash-v1.3:free"
  },
  "profiles": {
    "ollama_local": {
      "provider_name": "Ollama Local",
      "api_base": "http://127.0.0.1:11434",
      "default_model": "lfm3-omni:2b",
      "enabled": true
    },
    "openrouter": {
      "provider_name": "OpenRouter",
      "api_base": "https://openrouter.ai/api/v1",
      "api_key": "sk-or-v1-your-openrouter-key-here",
      "default_model": "perplexity/pplx-decider-flash-v1.3:free",
      "enabled": true
    }
  },
  "agent_model_assignments": {
    "supervisor": {
      "profile": "openrouter",
      "model": "perplexity/pplx-decider-flash-v1.3:free"
    },
    "planner": {
      "profile": "openrouter",
      "model": "perplexity/pplx-decider-flash-v1.3:free"
    }
  }
}
```

### Supported Providers:
- **OpenRouter:** `https://openrouter.ai/api/v1` (with live telemetry for credit balance and daily request limits).
- **Ollama Local:** `http://127.0.0.1:11434` (offline `lfm3-omni:2b`).
- **OpenAI:** `https://api.openai.com/v1`.
- **Groq:** `https://api.groq.com/openai/v1`.
- **DeepSeek:** `https://api.deepseek.com/v1`.

---

## 5. VOID Configuration Window & Sizing Presets

### Opening the Configuration Window
Click the red-accented **⚙** icon on the right side of the widget, click the status dot/pill, or say:
> *"Hey VOID, open settings"* / *"Hey VOID, configure models"*

### Window Features
- **Tab 1: 🧠 Models & Cloud API Keys**
  - Switch between Hybrid, Cloud-Only, and Local-Only modes.
  - Set Default Model & API Key.
  - Set independent Multi-Agent Planning Model & API Key.
  - Real-time API key credit balance, daily requests remaining, and rate limits query (`/auth/key`).
  - Live "Test Connection" button.
  - "Save & Apply" button (applies changes in memory without restarting VOID).
- **Tab 2: 🧩 Plugins & Skills**
  - Displays all 8 active core plugins with enable/disable toggles.
  - "Verify Skill Pipelines" button to test and confirm all tool registries.
- **Tab 3: 📐 Sizing & Preferences**
  - **Compact Bar (Pill):** 370 x 56 px.
  - **2x2 Square Widget:** 400 x 320 px.
  - **Large Multitask Window:** 750 x 550 px.
  - **Free Resize:** Drag from bottom-right corner to any custom dimension.
  - Voice Announcement Style: "Short & Sweet" (default) vs "Detailed".
  - Ollama RAM Saver: Start or Stop Ollama to save 2 GB memory.

---

## 6. Plugin & Skill Pipeline Architecture

VOID exposes 8 high-performance skills:

1. **🛠 Dodaios Desktop Tool Hub:** 105 tools for system management, screenshot capture, file I/O, process control.
2. **🪟 KWin Wayland Window Manager:** Instant sub-5ms window minimization, maximization, closing, and desktop display.
3. **🎵 YouTube Direct Tab Media:** Instant playback of user-requested tracks in Chromium tabs with zero-autocorrect.
4. **🎙 Faster-Whisper Base int8 STT:** Quantized offline acoustic speech-to-text.
5. **🔊 Piper Neural TTS:** Natural Ryan voice speech synthesis.
6. **📄 Document & PDF Composer:** Professional Word (.docx), PDF reports, and Excel spreadsheets.
7. **🔍 Universal Content & File Search:** Rapid multi-directory indexing with instant xdg-open.
8. **🤖 Multi-Agent Orchestrator:** 5-agent domain execution (Supervisor, Planner, Dev, Research, Verifier).

---

## 7. Voice Announcements (Short & Sweet)

To eliminate unnecessary verbosity, VOID confirms actions concisely:

| Action | Spoken Confirmation |
| :--- | :--- |
| **Minimize App** | *"Minimized Antigravity."* |
| **Close App** | *"Closed Chromium."* |
| **Minimize Window** | *"Minimized."* |
| **Show Desktop** | *"Showing desktop."* |
| **Generate Document** | *"Completed document."* |
| **Generate PDF** | *"Completed PDF."* |
| **Open Folder** | *"Opened folder."* |
| **Open Files** | *"Opened files."* |
| **Play Song** | *"Playing Pesamalaye on tab."* |
| **Take Screenshot** | *"Screenshot captured."* |

---

## 8. Media & Song Playback on Tabs (Zero Auto-Correction)

- **No Autocorrect on Songs:** Song titles (e.g., *"pesamalaye"*, *"shape of you"*, *"starboy"*) are never mangled into English acronyms (such as "PSA") or generic text.
- **Browser Tabs:** All media requests automatically launch as **tabs** inside Chromium without forcing new windows.
- **Phonetic Slips Handled:** Any speech transcription slip (e.g., "psa", "paisa malay", "paisal malay", "pesamale") is seamlessly mapped back to *"pesamalaye"*.

---

## 9. Performance & Efficiency Optimizations

- **Zero-Conflict Audio Stream:** Dodaios's background dictation worker (`preview_worker large-v3-turbo`) is automatically disabled, preventing 40-70% CPU waste and freeing 1.3 GB of memory.
- **Sub-5ms Fast Path:** Native hardware controls (volume, brightness, window state, media, file openers) execute immediately without contacting the LLM.
- **Dynamic VRAM Management:** Ollama model weights can be loaded or unloaded via voice (*"Hey VOID, stop ollama"*) to recover 2.0 GB of RAM.

---

## 10. Automated Verification & Test Matrix

Run the automated regression test suites to verify 100% health:

```bash
/home/prakash/.dodaios/.venv/bin/python /run/media/prakash/TR_39/VOID/scripts/test_song_playback_and_fast_classification.py
/home/prakash/.dodaios/.venv/bin/python /run/media/prakash/TR_39/VOID/scripts/test_multi_agent_system.py
```

---

## 11. Troubleshooting & Diagnostics

### 1. Check Live Assistant Status
```bash
/run/media/prakash/TR_39/VOID/scripts/status_void.sh
```

### 2. View Live Logs
```bash
tail -f /run/media/prakash/TR_39/VOID/config/widget.log
```

### 3. Audio / PipeWire Volume
```bash
wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.75
```

---

## 12. System Control & Activities (Power, Telemetry & Automation)

VOID features sub-5ms native system control hooks for complete Linux desktop management:

### 1. Power & Session Lifecycle Controls (5-Second Safety Gating)
All power-destructive actions feature a 5-second cancelable interactive UI banner and voice cancelability:
* **Shutdown / Power Off:**
  * Voice commands: *"shut down system"*, *"shutdown system"*, *"power off"*, *"turn off computer"*, *"shut don system"*
  * Executes: `systemctl poweroff` after a 5s countdown banner.
  * Cancel action: Click the on-screen **Cancel** button, or simply say *"cancel shutdown"*, *"abort"*, or *"stop"*.
* **Reboot / Restart:**
  * Voice commands: *"restart system"*, *"reboot system"*, *"restart computer"*, *"reboot"*
  * Executes: `systemctl reboot` after a 5s countdown banner.
  * Cancel action: Click **Cancel** or say *"cancel restart"*.
* **Sleep & Suspend:**
  * Voice commands: *"sleep"*, *"suspend system"*, *"put computer to sleep"*
  * Executes: `systemctl suspend` immediately.
* **Hibernate:**
  * Voice commands: *"hibernate system"*, *"hibernate"*
  * Executes: `systemctl hibernate`.
* **Lock Screen:**
  * Voice commands: *"lock screen"*, *"lock computer"*, *"lock system"*
  * Executes: `loginctl lock-session`.
* **Logout / Sign Out:**
  * Voice commands: *"logout"*, *"sign out"*
  * Executes: KDE DBus logout / `loginctl terminate-session self`.

### 2. Hardware Telemetry & Health Monitoring
* **System Hardware Vitals:**
  * Voice commands: *"check battery"*, *"system vitals"*, *"battery status"*, *"hardware temperature"*
  * Returns: Live Battery % and state, CPU/GPU/NVMe temperatures (°C), RAM telemetry (used vs total GB), and 1-minute CPU load averages.
* **Offload / Stop Neural Brain & Free RAM:**
  * Voice commands: *"offload model"*, *"offlad model"*, *"stop, offload model"*, *"unload model"*, *"stop ollama"*, *"free ram"*, *"free memory"*
  * Action: Evicts active model weights, terminates all `llama-server` backend processes, stops the Ollama daemon (`systemctl stop ollama`), severs internal connectivity, and completely frees all VRAM and system RAM. Connectivity remains strictly terminated until you say *"start model"*.
* **Start Model / Re-activate Ollama:**
  * Voice commands: *"start model"*, *"start model again"*, *"start the model"*, *"start ollama"*, *"load model"*, *"resume model"*
  * Action: Starts the Ollama server daemon (`systemctl start ollama`), restores internal connectivity, warms up the model into GPU/RAM, and brings the local AI brain back online.

### 3. Dedicated Stop Launcher & Automated RAM Reclaim (`void-stop.desktop`)
Clicking the **Stop VOID AI & Clear RAM** icon (or running `scripts/stop_void.sh` or `void-stop` in terminal) executes a comprehensive, multi-stage clean shutdown:
1. **Complete In-Flight Tasks:** Flushes disk buffers (`sync`), inspects `config/tasks.json`, marks active workflows as safely finalized, and commits persistent thought memories.
2. **Deactivate All Models:** Queries `/api/ps` on Ollama, unloads every active model weight (`nano-brain`, `lfm3-omni:2b`, etc.) from GPU VRAM and system memory, and kills any background `llama-server` / `llama-finetune` workers.
3. **Stop Model Server:** Stops `systemctl stop ollama` and terminates user-level daemon processes.
4. **Terminate Interface:** Cleanly terminates the PySide6 glass flow widget and Dodaios backend servers.
5. **Reclaim RAM & Drop Caches:** Invokes kernel memory synchronization, drops cached page buffers, reports exact megabytes reclaimed, and displays a native desktop notification confirming shutdown.

### 4. Desktop, Window & Process Activities
* **Window Management:**
  * *"minimize antigravity"*, *"close chromium"*, *"maximize terminal"*, *"fullscreen"*
  * *"show desktop"* (instantly toggles clean desktop view).
* **Process & Task Management:**
  * *"list tasks"*, *"system status"*, *"top processes"*
* **Audio & Display:**
  * *"volume 50%"*, *"mute audio"*, *"unmute"*, *"brightness 75%"*
* **Screen Capture:**
  * *"take a screenshot"*, *"capture screen"* $\rightarrow$ Saved to `/home/prakash/Pictures/Screenshots`.
* **Interactive Timers & Alarms:**
  * *"set timer for 10 minutes"*, *"cancel timer"* $\rightarrow$ Real-time countdown on widget banner with audio completion chime.

---
*Maintained by Prakash for the VOID Autonomous AI Desktop Assistant.*
