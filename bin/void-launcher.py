#!/usr/bin/env python3
"""
VOID Desktop Assistant Launcher & Lifecycle Manager
Manages Ollama, Dodaios, and the VOID desktop interface cleanly and safely.
"""

import sys
import os
import time
import json
import signal
import shutil
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

HOME_DIR = Path.home()
SSD_VOID_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = HOME_DIR / ".dodaios/data"
CONFIG_DIR = SSD_VOID_DIR / "config" if (SSD_VOID_DIR / "config").exists() else HOME_DIR / ".config/void"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE = CONFIG_DIR / ".void_launcher.json"
OLLAMA_MODELS_DIR = SSD_VOID_DIR / "models" if (SSD_VOID_DIR / "models").exists() else HOME_DIR / ".ollama/models"
if OLLAMA_MODELS_DIR.exists():
    os.environ["OLLAMA_MODELS"] = str(OLLAMA_MODELS_DIR)

OLLAMA_ENDPOINT = "http://127.0.0.1:11434/api/tags"
DODAIOS_HEALTH = "http://127.0.0.1:47821/api/health"
DODAIOS_APP_URL = "http://127.0.0.1:47821/"

# Locate Python binary dynamically
candidate_pythons = [
    sys.executable,
    str(SSD_VOID_DIR / ".venv/bin/python"),
    str(HOME_DIR / ".dodaios/.venv/bin/python"),
    str(HOME_DIR / ".void/.venv/bin/python"),
    shutil.which("python3") or "python3"
]
VENV_PYTHON = next((p for p in candidate_pythons if p and Path(p).is_file() and os.access(p, os.X_OK)), sys.executable)
DODAIOS_BIN = str(Path(VENV_PYTHON).parent / "dodaios")
CHROMIUM_BIN = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome") or "/usr/bin/chromium-browser"

def is_url_alive(url, timeout=1.5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VOID-Launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False

def wait_for_service(url, timeout_s=30, interval_s=0.5):
    start = time.time()
    while time.time() - start < timeout_s:
        if is_url_alive(url):
            return True
        time.sleep(interval_s)
    return False

def stop_void():
    print("[VOID] Stopping VOID processes...")
    if not PID_FILE.exists():
        print("[VOID] No running VOID instance tracked.")
        # Check if dodaios serve is running and stop it
        return

    try:
        with open(PID_FILE, "r") as f:
            state = json.load(f)
    except Exception as e:
        print(f"[VOID] Error reading state file: {e}")
        state = {}

    # Stop Dodaios if started by VOID
    dodai_pid = state.get("dodaios_pid")
    if dodai_pid:
        try:
            print(f"[VOID] Terminating Dodaios (PID {dodai_pid})...")
            os.kill(dodai_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"[VOID] Warning terminating Dodaios: {e}")

    # Stop Chromium app window if started by VOID
    ui_pid = state.get("ui_pid")
    if ui_pid:
        try:
            print(f"[VOID] Terminating VOID UI (PID {ui_pid})...")
            os.kill(ui_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"[VOID] Warning terminating UI: {e}")

    # Stop Ollama ONLY if VOID started it
    if state.get("started_ollama"):
        ollama_pid = state.get("ollama_pid")
        if ollama_pid:
            try:
                print(f"[VOID] Terminating VOID-started Ollama (PID {ollama_pid})...")
                os.kill(ollama_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    else:
        print("[VOID] Preserving existing shared Ollama service.")

    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    print("[VOID] Stop complete.")

def start_void():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "started_ollama": False,
        "ollama_pid": None,
        "dodaios_pid": None,
        "ui_pid": None,
        "start_time": time.time()
    }

    # 1. Check Ollama
    print("[VOID] Checking Ollama service...")
    if not is_url_alive(OLLAMA_ENDPOINT):
        print(f"[VOID] Starting Ollama serve with models in {OLLAMA_MODELS_DIR}...")
        ollama_env = dict(os.environ, OLLAMA_MODELS=str(OLLAMA_MODELS_DIR))
        ollama_proc = subprocess.Popen(
            ["ollama", "serve"],
            env=ollama_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        state["started_ollama"] = True
        state["ollama_pid"] = ollama_proc.pid
        if not wait_for_service(OLLAMA_ENDPOINT, timeout_s=15):
            print("[VOID] Warning: Ollama took too long to answer health check.")
    else:
        print("[VOID] Existing Ollama service detected and active.")

    # 2. Check Dodaios
    print("[VOID] Checking Dodaios backend...")
    if not is_url_alive(DODAIOS_HEALTH):
        print("[VOID] Starting Dodaios backend server...")
        log_file = open(DATA_DIR / "dodaios.log", "a")
        dodai_proc = subprocess.Popen(
            [DODAIOS_BIN, "serve"],
            cwd=str(HOME_DIR / ".dodaios") if (HOME_DIR / ".dodaios").exists() else str(SSD_VOID_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        state["dodaios_pid"] = dodai_proc.pid
        if not wait_for_service(DODAIOS_HEALTH, timeout_s=30):
            print("[VOID] Error: Dodaios backend failed to start.")
            stop_void()
            sys.exit(1)
        print("[VOID] Dodaios backend is ready.")
    else:
        print("[VOID] Existing Dodaios backend detected and active.")

    # 3. Launch VOID Native Glass Flow Mini Widget
    widget_bin = SSD_VOID_DIR / "bin" / "void-widget.py"
    if "--web" in sys.argv or "--browser" in sys.argv:
        print("[VOID] Launching VOID Web Dashboard in Chromium...")
        ui_args = [
            CHROMIUM_BIN,
            f"--app={DODAIOS_APP_URL}",
            "--class=VOID",
            "--name=VOID",
            "--enable-features=UseOzonePlatform",
            "--ozone-platform=wayland"
        ]
        ui_proc = subprocess.Popen(
            ui_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    else:
        print("[VOID] Launching VOID Native Glass Flow Mini Widget...")
        subprocess.run(["pkill", "-f", "void-widget.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)
        log_path = CONFIG_DIR / "widget.log"
        log_out = open(log_path, "a")
        ui_proc = subprocess.Popen(
            [VENV_PYTHON, str(widget_bin)],
            stdout=log_out,
            stderr=log_out,
            start_new_session=True
        )
    state["ui_pid"] = ui_proc.pid

    # Save state
    with open(PID_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print("[VOID] VOID Desktop Assistant is running.")
    print(f"[VOID] Backend: {DODAIOS_HEALTH}")
    print(f"[VOID] Interface: {DODAIOS_APP_URL}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--stop", "stop", "-s"):
        stop_void()
    else:
        start_void()
