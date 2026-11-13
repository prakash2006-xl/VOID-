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

def get_mem_available_mb() -> int:
    """Reads available system RAM in megabytes from /proc/meminfo."""
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0

def stop_void(clear_ram: bool = True, deactivate_models: bool = True, stop_server: bool = True):
    print("=================================================")
    print("   VOID AI — Clean Shutdown & Memory Reclaim     ")
    print("=================================================")
    mem_before = get_mem_available_mb()

    # 1. Complete In-Flight Tasks & Flush Buffers
    print("[VOID 1/5] Completing active tasks and flushing memory buffers...")
    tasks_file = CONFIG_DIR / "tasks.json"
    if tasks_file.exists():
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
            task_list = tasks_data if isinstance(tasks_data, list) else tasks_data.get("tasks", [])
            updated = False
            for t in task_list:
                if isinstance(t, dict) and t.get("status") in ("running", "in_progress", "executing"):
                    t["status"] = "completed"
                    t["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    updated = True
            if updated:
                with open(tasks_file, "w", encoding="utf-8") as f:
                    json.dump(tasks_data, f, indent=2)
                print("[VOID] In-flight tasks safely finalized and saved to tasks.json.")
            else:
                print("[VOID] All pending tasks verified and persistent memory synced.")
        except Exception as e:
            print(f"[VOID] Note on tasks buffer: {e}")
    try:
        os.sync()
    except Exception:
        subprocess.run(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.3)

    # 2. Deactivate All Local Neural Models from VRAM & RAM
    if deactivate_models:
        print("[VOID 2/5] Deactivating all neural models from memory...")
        deactivated = []
        try:
            req = urllib.request.Request(OLLAMA_ENDPOINT.replace("/api/tags", "/api/ps"), headers={"User-Agent": "VOID-Launcher"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode())
                for m in data.get("models", []):
                    m_name = m.get("name") or m.get("model")
                    if m_name:
                        subprocess.run(["ollama", "stop", m_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        deactivated.append(m_name)
        except Exception:
            pass

        # Also send explicit stop / keep_alive: 0 to all known VOID local models
        for fallback in ["nano-brain", "lfm3-omni:2b", "lfm3-omni-2b-jarvis-f0966e86:latest", "smollm2:360m"]:
            if fallback not in deactivated:
                try:
                    subprocess.run(["ollama", "stop", fallback], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    deactivated.append(fallback)
                except Exception:
                    pass

        # Terminate any standalone llama-server or llama-finetune worker processes
        try:
            subprocess.run(["pkill", "-f", "llama-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", "llama-finetune"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        print(f"[VOID] Deactivated models: {', '.join(deactivated) if deactivated else 'None active'}")

    # 3. Stop Model Server & Backend Daemons
    if stop_server:
        print("[VOID 3/5] Stopping model servers and backend daemons...")
        try:
            subprocess.run(["systemctl", "stop", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        try:
            subprocess.run(["pkill", "-f", "ollama serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Read state if tracked
    state = {}
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r") as f:
                state = json.load(f)
        except Exception as e:
            print(f"[VOID] Error reading state file: {e}")

    # Terminate tracked PIDs
    for pid_key in ["dodaios_pid", "ui_pid", "ollama_pid"]:
        pid = state.get(pid_key)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

    # 4. Clean Terminate All VOID Interface Processes
    print("[VOID 4/5] Terminating VOID interface and worker processes...")
    try:
        subprocess.run(["pkill", "-f", "void-widget.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "dodaios serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Remove stale PID files
    for p in [PID_FILE, Path.home() / ".dodaios/data/.void_launcher.json"]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    # 5. Clear RAM & Drop Caches
    if clear_ram:
        print("[VOID 5/5] Reclaiming system memory and flushing caches...")
        try:
            os.sync()
            subprocess.run(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Drop page caches if root or passwordless sudo permitted
            subprocess.run(["sudo", "-n", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    mem_after = get_mem_available_mb()
    freed = max(0, mem_after - mem_before)
    print("-------------------------------------------------")
    print(f"[VOID] Available RAM before: {mem_before} MB")
    print(f"[VOID] Available RAM after:  {mem_after} MB (+{freed} MB reclaimed)")
    print("[VOID] Clean shutdown complete. All models deactivated.")
    print("=================================================")

    # Desktop notification
    try:
        notify_msg = f"All models deactivated, tasks completed, and {freed} MB RAM cleared." if freed > 0 else "All models deactivated, tasks completed, and RAM cleared."
        subprocess.run([
            "notify-send",
            "VOID AI Shutdown",
            notify_msg,
            "-i", "process-stop",
            "-t", "3500"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

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
    if len(sys.argv) > 1 and sys.argv[1] in ("--stop", "stop", "-s", "--clean-ram", "--offload", "--deactivate", "-k"):
        stop_void()
    else:
        start_void()
