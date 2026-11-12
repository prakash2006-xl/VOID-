# VOID — Complete Setup, Installation & Deployment Guide

Welcome to the setup documentation for **VOID**, an autonomous, keyless, personal AI desktop assistant built specifically for Linux (KDE Plasma 6 on Wayland/X11). VOID combines sub-5ms local desktop automation with the cognitive intelligence of Liquid AI's neural models running 100% offline via Ollama.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Directory Architecture](#2-directory-architecture)
3. [System Dependencies Installation](#3-system-dependencies-installation)
4. [Python Virtual Environment Setup](#4-python-virtual-environment-setup)
5. [Local Neural Brain (Ollama) Setup](#5-local-neural-brain-ollama-setup)
6. [Offline Speech Models Setup (STT & TTS)](#6-offline-speech-models-setup-stt--tts)
7. [Running & Launching VOID](#7-running--launching-void)
8. [Automated System Verification & Tests](#8-automated-system-verification--tests)
9. [Voice Commands & Feature Reference](#9-voice-commands--feature-reference)
10. [Git Setup & GitHub Repository Synchronization](#10-git-setup--github-repository-synchronization)
11. [Troubleshooting & Diagnostics](#11-troubleshooting--diagnostics)

---

## 1. System Requirements

- **Operating System:** Fedora Linux 40+ / Ubuntu 24.04+ / Arch Linux (KDE Plasma 6 Wayland recommended)
- **CPU:** AMD Ryzen 5/7/9 or Intel Core i5/i7/i9 (4+ physical cores)
- **RAM:** 16 GB minimum (8 GB for OS/apps, 4–6 GB for local LLM & whisper in-memory)
- **Graphics:** AMD Radeon / Intel Iris Xe / NVIDIA (Vulkan / ROCm / CUDA compatible)
- **Audio Server:** PipeWire 1.0+ with WirePlumber
- **Storage:** ~10 GB free space (5 GB for LLM weights, 2 GB for STT/TTS models)

---

## 2. Directory Architecture

All persistent runtime assets, scripts, neural models, and memory databases reside in the external root or designated deployment folder:

```
/run/media/prakash/TR_39/VOID/
├── bin/
│   ├── void-widget.py         # Main PySide6 Glass Island Desktop Assistant daemon
│   └── dodaios_tool_hub.py    # 105 Dodaios local automation tools engine
├── config/
│   └── void-config.json       # Assistant preferences, wake words, thresholds
├── docs/
│   ├── README.md              # Project overview
│   ├── TOOLS_GUIDE.md         # Fast-path vs AI tool reference
│   └── ACTIONS_WITH_AND_WITHOUT_AI.md
├── memory/
│   └── facts.json             # Persistent episodic SSD memory and user preferences
├── models/
│   ├── ollama/                # Local LLM weights (lfm3-omni:2b)
│   ├── tts/                   # Piper VITS ONNX models (en_US-ryan-medium.onnx)
│   └── vosk/                  # Vosk Kaldi acoustic grammar model
├── scripts/
│   ├── run_void.sh            # One-click launcher script
│   ├── stop_void.sh           # Safe termination script
│   ├── status_void.sh         # Real-time daemon & memory diagnostics
│   └── test_*.py              # Comprehensive test suites (94 regression tests)
├── .gitignore                 # Shields heavy binary model weights from git tracking
├── README.md                  # Main GitHub documentation
└── SETUP.md                   # This installation and deployment guide
```

---

## 3. System Dependencies Installation

### Fedora / RHEL:
```bash
sudo dnf install -y \
    pipewire-utils \
    wireplumber \
    espeak-ng \
    espeak-ng-devel \
    wl-clipboard \
    qt6-qdbus \
    alsa-utils \
    git \
    curl \
    python3-devel
```

### Ubuntu / Debian:
```bash
sudo apt update && sudo apt install -y \
    pipewire-bin \
    wireplumber \
    espeak-ng \
    libespeak-ng-dev \
    wl-clipboard \
    qdbus-qt6 \
    alsa-utils \
    git \
    curl \
    python3-dev \
    python3-venv
```

### Arch Linux:
```bash
sudo pacman -S --needed \
    pipewire \
    wireplumber \
    espeak-ng \
    wl-clipboard \
    qt6-tools \
    alsa-utils \
    git \
    curl \
    python
```

---

## 4. Python Virtual Environment Setup

Create an isolated virtual environment and install all required machine learning and desktop automation libraries:

```bash
# Create directory and virtual environment
python3 -m venv /home/prakash/.dodaios/.venv

# Activate virtual environment
source /home/prakash/.dodaios/.venv/bin/activate

# Upgrade pip, wheel, and setuptools
pip install --upgrade pip setuptools wheel

# Install PySide6 and GUI dependencies
pip install PySide6

# Install Audio and Neural Voice dependencies
pip install \
    sounddevice \
    numpy \
    vosk \
    faster-whisper \
    sherpa-onnx

# Install Document Generation and Utility packages
pip install \
    python-docx \
    openpyxl \
    httpx \
    beautifulsoup4 \
    pillow
```

---

## 5. Local Neural Brain (Ollama) Setup

VOID uses **Ollama** to serve quantized neural models on-device with zero external API dependencies.

### Step 1: Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Configure Ollama Storage Directory (Optional)
To store heavy models on an external high-speed disk instead of the root partition:
```bash
# Add to ~/.bashrc or systemd service override:
export OLLAMA_MODELS="/run/media/prakash/TR_39/VOID/models/ollama"
```

### Step 3: Start Ollama and Pull the Recommended Brain Model
```bash
# Start Ollama service
ollama serve &

# Pull Liquid AI lfm3-omni:2b (fast, articulate, 1.7B parameter instruction model)
ollama pull lfm3-omni:2b
```

---

## 6. Offline Speech Models Setup (STT & TTS)

### A. Vosk Real-Time Acoustic Wake Word Model
Download and unpack the small English acoustic model for low-power continuous listening:
```bash
mkdir -p /home/prakash/.dodaios/data/wake_models/vosk/en
cd /home/prakash/.dodaios/data/wake_models/vosk/en
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### B. Faster-Whisper Base STT
Faster-Whisper automatically downloads its quantized int8 weights on first invocation to `~/.cache/huggingface/hub/`.

### C. Piper Local Neural TTS Voice
VOID uses Piper via `sherpa-onnx` for conversational speech:
```bash
mkdir -p /run/media/prakash/TR_39/VOID/models/tts
cd /run/media/prakash/TR_39/VOID/models/tts

# Download Ryan Medium English neural voice
wget -c https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-medium.tar.gz
tar -xvf voice-en-us-ryan-medium.tar.gz
```

---

## 7. Running & Launching VOID

### Interactive Launch (with Wayland Environment Flags)
```bash
env WAYLAND_DISPLAY=wayland-1 DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 QT_WAYLAND_RECONNECT=1 \
    /home/prakash/.dodaios/.venv/bin/python /run/media/prakash/TR_39/VOID/bin/void-widget.py
```

### Using the Dedicated Runner Script
```bash
cd /run/media/prakash/TR_39/VOID
chmod +x scripts/run_void.sh
./scripts/run_void.sh
```

### Setting up Auto-Start on System Login (KDE Plasma)
Create an autostart desktop entry:
```bash
mkdir -p ~/.config/autostart
cat << 'EOF' > ~/.config/autostart/void-widget.desktop
[Desktop Entry]
Type=Application
Name=VOID Desktop Assistant
Exec=env WAYLAND_DISPLAY=wayland-1 DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 /home/prakash/.dodaios/.venv/bin/python /run/media/prakash/TR_39/VOID/bin/void-widget.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

---

## 8. Automated System Verification & Tests

To verify that all 105 tools, the audio pipeline, document generation, and safeguards are functioning at 100%:

```bash
# Run the full regression matrix (all 12 test suites, 94 unit tests)
/home/prakash/.dodaios/.venv/bin/python -c '
import subprocess
tests = [
    "test_speech_and_system_invariance.py",
    "test_all_tools_and_emotion.py",
    "test_generalised_ollama_commands.py",
    "test_universal_open_and_search.py",
    "test_youtube_dictation_and_memory.py",
    "test_dictation_and_documents.py",
    "test_glass_rendering.py",
    "test_3d_globe_states.py",
    "test_browser_and_email.py",
    "test_audio_and_wake_isolation.py",
    "test_offline_routing_and_phonetics.py",
    "automated_system_test.py"
]
for t in tests:
    res = subprocess.run(["/home/prakash/.dodaios/.venv/bin/python", f"/run/media/prakash/TR_39/VOID/scripts/{t}"], capture_output=True, text=True)
    status = "PASSED" if res.returncode == 0 else "FAILED"
    print(f"{status}: {t}")
'
```

---

## 9. Voice Commands & Feature Reference

| Category | Spoken Command Variations | System Action |
| :--- | :--- | :--- |
| **Wake Words** | *"Hey VOID"*, *"VOID"*, *"Hi VOID"*, *"Hello VOID"* | Wakes the assistant and begins listening. |
| **Voice Diagnostics** | *"Test speech"*, *"Check speech"*, *"Test voice"*, *"Audio test"* | Synthesizes and plays diagnostic speech aloud via PipeWire (`pw-play`). |
| **Volume Control** | *"Set volume to 75%"*, *"Volume up"*, *"Volume down"*, *"Mute audio"* | Adjusts PipeWire audio sink with strict intent guards. |
| **Baseline Restore** | *"Reset volume"*, *"Restore volume"*, *"Reset brightness"*, *"Restore brightness"* | Restores audio volume or display brightness back to initial session baseline. |
| **Display Brightness** | *"Set brightness to 80%"*, *"Brightness up"*, *"Brightness down"*, *"Screen dimmer"*, *"Screen brighter"* | Adjusts KDE display brightness percentage via DBus. |
| **Universal Opener** | *"Open Mothers_Importance.docx"*, *"Open sample.mp4"*, *"Open calculator"*, *"Open terminal"* | Universal content opener: exact files, videos, photos, apps, web services. |
| **YouTube Streaming** | *"Open YouTube and play believer song"* | Directly searches and plays the requested song or artist in Chromium. |
| **Voice Dictation** | *"Start dictation"*, *"Voice typing"*, *"Write note"* | Live speech-to-text dictation into `~/Documents/Notes/`. |
| **Exit Dictation** | *"Stop dictation"*, *"Cancel dictate"*, *"Done"* | Stops dictation mode, saves file, and speaks completion confirmation. |
| **Document Drafting** | *"Draft docx on Quantum Computing"*, *"Create excel for budget"* | Creates fully formatted Word (`.docx`) or Excel (`.xlsx`) files. |
| **Brain Lifecycle** | *"Start ollama"*, *"Activate brain"*, *"Put brain on standby"*, *"Stop ollama"* | Dynamically unloads/loads models from GPU memory (saving 2 GB VRAM). |
| **Emergency Abort** | *"Stop"*, *"Cancel"*, *"Shut up"*, *"Stop talking"*, *"Stop thinking"* | Instantly interrupts speech and neural processing in `< 5ms`. |
| **Shutdown** | *"Hey VOID terminate code 0"* | Gracefully closes VOID and shuts down the assistant process. |

---

## 10. Git Setup & GitHub Repository Synchronization

### Step 1: Configure Git Identity
```bash
git config --global user.name "prakash2006-xl"
git config --global user.email "rskakavin@gmail.com"
git config --global credential.helper store
```

### Step 2: Push Initial Commit to GitHub
Ensure the `.gitignore` excludes heavy model binaries before pushing:

```bash
cd /run/media/prakash/TR_39/VOID
git init
git branch -M main
git remote add origin https://github.com/prakash2006-xl/VOID-.git

# Stage documentation, configuration, and scripts
git add README.md SETUP.md .gitignore bin/ config/ docs/ memory/ scripts/
git commit -m "Initialize VOID assistant core and deployment documentation"

# Push to GitHub (enter Personal Access Token when prompted)
git push -u origin main
```

---

## 11. Troubleshooting & Diagnostics

### 1. No Audio Heard During Spoken Response
- Verify PipeWire default audio sink is unmuted:
  ```bash
  wpctl get-volume @DEFAULT_AUDIO_SINK@
  wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
  ```
- Test PipeWire native playback directly:
  ```bash
  pw-play /usr/share/sounds/freedesktop/stereo/complete.oga
  ```

### 2. Microphone Not Picking Up Wake Word
- Verify microphone capture source volume:
  ```bash
  wpctl get-volume @DEFAULT_AUDIO_SOURCE@
  wpctl set-volume @DEFAULT_AUDIO_SOURCE@ 0.60
  ```

### 3. Wayland Display Connection Issue
Ensure environment variables point to the active Wayland socket:
```bash
echo $WAYLAND_DISPLAY
# Should print 'wayland-0' or 'wayland-1'
```

### 4. Ollama Out-of-Memory (VRAM)
If your GPU VRAM is constrained, run:
```bash
# Unload models from memory
ollama stop lfm3-omni:2b
```
VOID's voice command *"put brain on standby"* or *"stop ollama"* unloads models automatically.

---

*Documentation maintained by Prakash for VOID AI Assistant.*

