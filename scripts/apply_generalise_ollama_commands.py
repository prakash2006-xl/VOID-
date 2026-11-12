#!/usr/bin/env python3
"""
Generalise Start Ollama and Stop Ollama commands in VOID Desktop Assistant (/run/media/prakash/TR_39/VOID/bin/void-widget.py).
Supports all natural variations of:
- Starting Ollama: start/open/turn on/launch/activate/load/run/boot/wake up ollama/brain/ai/model
- Stopping Ollama: stop/close/turn off/shut down/kill/quit/deactivate/unload/sleep ollama/brain/ai/model
- Restarting Ollama: restart/reboot/reload ollama/brain/ai
- Dynamic model unloading via /api/ps and custom model parameter support
"""

import sys
import re
from pathlib import Path

WIDGET_FILE = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")

def apply_ollama_generalization():
    if not WIDGET_FILE.exists():
        print(f"[ERROR] File not found: {WIDGET_FILE}")
        sys.exit(1)

    content = WIDGET_FILE.read_text(encoding="utf-8")

    # 1. Add Ollama Lifecycle helper functions
    helpers_code = '''
# ---------------------------------------------------------------------------
# Generalized Ollama Brain Lifecycle Management Subsystem
# ---------------------------------------------------------------------------
def start_ollama_service(model_name: str = "") -> tuple[bool, str]:
    """Starts Ollama daemon if needed and loads the requested brain model into VRAM."""
    import httpx
    target_model = model_name or "lfm3-omni:2b"
    started = False
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.0)
        started = (r.status_code == 200)
    except Exception:
        pass

    if not started:
        ollama_env = dict(os.environ, OLLAMA_MODELS=str(MODELS_DIR))
        subprocess.Popen(["ollama", "serve"], env=ollama_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < 6.0:
            try:
                if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=0.8).status_code == 200:
                    started = True
                    break
            except Exception:
                pass
            time.sleep(0.4)

    # Pre-warm / load model into GPU memory
    try:
        httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": target_model, "prompt": "ready", "stream": False}, timeout=12.0)
    except Exception:
        pass

    return True, f"Ollama server started and {target_model} brain is loaded."

def stop_all_ollama_models(kill_server: bool = False, specific_model: str = "") -> list[str]:
    """Queries /api/ps and unloads all active models from memory, optionally killing ollama serve."""
    stopped = []
    if specific_model:
        subprocess.run(["ollama", "stop", specific_model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stopped.append(specific_model)
        return stopped

    try:
        import httpx
        r = httpx.get(f"{OLLAMA_URL}/api/ps", timeout=1.0)
        if r.status_code == 200:
            data = r.json()
            models = data.get("models", [])
            for m in models:
                m_name = m.get("name") or m.get("model")
                if m_name:
                    subprocess.run(["ollama", "stop", m_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    stopped.append(m_name)
    except Exception:
        pass

    for fallback in ["lfm3-omni:2b", "lfm3-omni-2b-jarvis-f0966e86:latest"]:
        if fallback not in stopped:
            subprocess.run(["ollama", "stop", fallback], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            stopped.append(fallback)

    if kill_server:
        subprocess.run(["pkill", "-f", "ollama serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return stopped

def restart_ollama_service(model_name: str = "") -> tuple[bool, str]:
    """Gracefully restarts the Ollama service and reloads the brain."""
    stop_all_ollama_models(kill_server=True)
    time.sleep(0.6)
    return start_ollama_service(model_name)
'''

    if "def start_ollama_service" not in content:
        anchor = "    def _ensure_ollama_started_bg(self) -> None:"
        content = content.replace(anchor, helpers_code + "\n" + anchor, 1)
        print("[APPLIED] Added generalized Ollama lifecycle helpers (start_ollama_service, stop_all_ollama_models, restart_ollama_service).")

    # 2. Replace static start/stop blocks in _execute_single_command
    old_start_stop_block = '''        if any(p in q_lower for p in ["start ollama", "activate brain", "launch ollama", "load brain", "turn on brain", "start ai brain"]):
            try:
                import httpx
                started = False
                try:
                    r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.0)
                    started = (r.status_code == 200)
                except Exception:
                    pass
                if not started:
                    ollama_env = dict(os.environ, OLLAMA_MODELS=str(MODELS_DIR))
                    subprocess.Popen(["ollama", "serve"], env=ollama_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    t0 = time.time()
                    while time.time() - t0 < 6.0:
                        try:
                            if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=0.8).status_code == 200:
                                started = True
                                break
                        except Exception:
                            pass
                        time.sleep(0.4)
                try:
                    httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": "lfm3-omni:2b", "prompt": "ready", "stream": False}, timeout=12.0)
                except Exception:
                    pass
                return ("Ollama server started and lfm3-omni:2b brain is loaded.", "Ollama: Online", "")
            except Exception as e:
                return (f"Could not start Ollama: {e}", "Ollama: Error", "")

        if any(p in q_lower for p in ["stop ollama", "deactivate brain", "unload brain", "kill ollama"]):
            try:
                subprocess.run(["ollama", "stop", "lfm3-omni:2b"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["ollama", "stop", "lfm3-omni-2b-jarvis-f0966e86:latest"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return ("Ollama stopped. Model unloaded and memory freed.", "Ollama: Standby", "")
            except Exception as e:
                return (f"Error stopping Ollama: {e}", "Ollama: Error", "")'''

    new_start_stop_block = '''        # 0d1. Generalized Model Name Extraction (e.g. "start ollama with llama3")
        m_req = re.search(r"(?:with\\s+(?:model\\s+)?|model\\s+)([a-zA-Z0-9_\\-.:]+)", q_clean, re.I)
        target_model = m_req.group(1).strip() if m_req else "lfm3-omni:2b"

        # 0d2. Generalized Restart Ollama
        is_restart_ollama = bool(
            re.search(r"\\b(?:restart|reboot|reload)\\s+(?:the\\s+)?(?:ollama|brain|ai|local\\s+ai|model)\\b", q_lower)
        )
        if is_restart_ollama:
            try:
                ok, msg = restart_ollama_service(target_model)
                return (f"Ollama restarted successfully and {target_model} brain is loaded.", "Ollama: Restarted", "")
            except Exception as e:
                return (f"Error restarting Ollama: {e}", "Ollama: Error", "")

        # 0d3. Generalized Start / Turn On / Launch / Activate Ollama & Brain
        is_start_ollama = bool(
            re.search(r"\\b(?:start|launch|open|turn\\s+on|switch\\s+on|run|boot|activate|load|enable|wake(?:\\s+up)?|spin\\s+up|bring\\s+up|initialize)\\s+(?:the\\s+)?(?:ollama|brain|ai|ai\\s+brain|local\\s+ai|local\\s+model|llm)\\b", q_lower) or
            re.search(r"\\b(?:turn|switch)\\s+(?:the\\s+)?(?:ollama|brain|ai|model)\\s+on\\b", q_lower) or
            re.search(r"\\b(?:ollama|brain|ai)\\s+(?:on|start|up|active|online)\\b", q_lower) or
            re.search(r"\\b(?:load|start|activate)\\s+(?:the\\s+)?(?:model|models)\\b", q_lower) or
            re.search(r"\\bollama\\s+serve\\b", q_lower) or
            q_lower in ["start ollama", "open ollama", "ollama on", "turn on ollama", "brain on", "activate brain", "load brain", "wake brain", "start ai", "turn on brain", "start ai brain", "launch ollama"]
        )
        if is_start_ollama:
            try:
                ok, msg = start_ollama_service(target_model)
                return (f"Ollama server started and {target_model} brain is loaded.", "Ollama: Online", "")
            except Exception as e:
                return (f"Could not start Ollama: {e}", "Ollama: Error", "")

        # 0d4. Generalized Stop / Turn Off / Shut Down / Deactivate / Unload Ollama & Brain
        is_stop_ollama = bool(
            re.search(r"\\b(?:stop|turn\\s+off|switch\\s+off|shut\\s*down|close|kill|quit|exit|deactivate|unload|disable|freeze|terminate)\\s+(?:the\\s+)?(?:ollama|brain|ai|ai\\s+brain|local\\s+ai|local\\s+model|llm|models?)\\b", q_lower) or
            re.search(r"\\b(?:turn|switch)\\s+(?:the\\s+)?(?:ollama|brain|ai|model)\\s+off\\b", q_lower) or
            re.search(r"\\b(?:put\\s+(?:the\\s+)?(?:brain|ollama|ai)\\s+(?:to\\s+sleep|on\\s+standby))\\b", q_lower) or
            re.search(r"\\b(?:sleep|standby)\\s+(?:the\\s+)?(?:brain|ollama|ai)\\b", q_lower) or
            re.search(r"\\b(?:ollama|brain|ai)\\s+(?:off|stop|down|sleep|standby|kill|quit)\\b", q_lower) or
            q_lower in ["stop ollama", "close ollama", "kill ollama", "turn off ollama", "ollama off", "brain off", "deactivate brain", "unload brain", "unload model", "stop brain", "stop ai", "shut down ollama", "shutdown ollama"]
        )
        if is_stop_ollama:
            try:
                kill_srv = any(w in q_lower for w in ["kill", "terminate", "server", "daemon", "service", "shutdown", "shut down"])
                spec_m = m_req.group(1).strip() if ("model" in q_lower and m_req) else ""
                stopped_models = stop_all_ollama_models(kill_server=kill_srv, specific_model=spec_m)
                if kill_srv:
                    return ("Ollama server stopped, all models unloaded, and system memory freed.", "Ollama: Standby", "")
                else:
                    return ("Ollama stopped. Model unloaded and memory freed.", "Ollama: Standby", "")
            except Exception as e:
                return (f"Error stopping Ollama: {e}", "Ollama: Error", "")'''

    if old_start_stop_block in content:
        content = content.replace(old_start_stop_block, new_start_stop_block, 1)
        print("[APPLIED] Replaced static start/stop blocks with Generalized Ollama Intent Matcher.")
    else:
        print("[WARNING] Could not find static start/stop blocks in void-widget.py.")

    WIDGET_FILE.write_text(content, encoding="utf-8")
    print(f"[SUCCESS] Updated: {WIDGET_FILE}")

if __name__ == "__main__":
    apply_ollama_generalization()

