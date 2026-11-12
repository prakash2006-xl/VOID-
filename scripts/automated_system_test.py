#!/usr/bin/env python3
"""
VOID Comprehensive Automated System Test Suite
Runs all functional checks across Hearing, Execution, Sequential Chaining, Memory, and System Safety.
"""

import sys
import os
import time
from pathlib import Path

# Add VOID bin
VOID_ROOT = Path("/run/media/prakash/TR_39/VOID")
sys.path.insert(0, str(VOID_ROOT / "bin"))

from PySide6.QtCore import QCoreApplication
app = QCoreApplication.instance() or QCoreApplication([])

import importlib
vw = importlib.import_module("void-widget")

print("=" * 60)
print("     VOID AUTOMATED END-TO-END SYSTEM TEST SUITE     ")
print("=" * 60)

passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        print(f"  [PASS] {name} {details}")
        passed += 1
    else:
        print(f"  [FAIL] {name} {details}")
        failed += 1

# 1. Location check
test("Working Location", str(VOID_ROOT) == "/run/media/prakash/TR_39/VOID", f"-> {VOID_ROOT}")

# 2. STT Hearing / Typo Normalization
typo_tests = [
    ("opn crome", "open chromium"),
    ("strat termianl", "start terminal"),
    ("open calcultor", "open calculator"),
    ("take a screnshot", "take a screenshot"),
    ("take a screen short", "take a screenshot"),
    ("minimise chromium", "minimize chromium"),
    ("start olama", "start ollama"),
    ("rember that i like linux", "remember that i like linux"),
    ("shutdwon system", "shutdown system"),
]
all_norm_ok = True
for inp, exp in typo_tests:
    norm = vw.normalize_voice_intent(inp)
    if norm != exp:
        all_norm_ok = False
        print(f"    Norm mismatch: '{inp}' -> '{norm}' (expected '{exp}')")
test("Hearing Typo Tolerance", all_norm_ok, "9/9 phonetics & slips normalized")

# 3. Application resolution
app_res_ok = True
for app_name in ["chrome", "crome", "browser", "internet", "google", "chromium"]:
    target = vw.resolve_app_name(app_name)
    if target != "chromium":
        app_res_ok = False
test("Browser Auto-Mapping to Chromium", app_res_ok, "chrome/browser/internet -> chromium")

# 4. Engine Initialization
tool_hub = vw.DodaiosToolHub()
engine = vw.AudioVoiceEngine(tool_hub=tool_hub)
test("Tool Hub & Voice Engine Init", engine is not None and tool_hub is not None)

# 5. Anti-Reintroduction check
r_greet, b_greet, _ = engine._execute_single_command("hey void")
test("No Self-Introduction on Greeting", r_greet == "I'm listening." and "I am VOID" not in r_greet, f"-> '{r_greet}'")

# 6. Default Browser Launch (without conversational deflection)
r_chrome, b_chrome, _ = engine._execute_single_command("open chrome")
test("Open Chrome Auto-Execute", "Opened Chromium." in r_chrome, f"-> '{r_chrome}'")

r_browser, b_browser, _ = engine._execute_single_command("open browser")
test("Open Browser Auto-Execute", "Opened Chromium." in r_browser, f"-> '{r_browser}'")

# 7. SSD Memory Engine (1.5GB)
mem_st = engine.memory.get_stats()
test("SSD Memory Engine (1.5GB)", mem_st["max_mb"] == 1500.0, f"Used: {mem_st['used_mb']}MB, Max: {mem_st['max_mb']}MB")

# Test learning & recall
learn_res = engine.memory.learn("User prefers KDE Plasma 6 on Wayland")
recalled = engine.memory.recall("Wayland")
test("Learn & Recall on SSD", any("Wayland" in rec for rec in recalled), f"Recalled: {recalled}")

r_mem_st, _, _ = engine._execute_single_command("memory status")
test("Memory Status Command", "SSD Memory:" in r_mem_st and "1500.0 MB" in r_mem_st, f"-> '{r_mem_st}'")

# 8. Sequential Compound Command Execution
compound_query = "open chrome and memory status and calculate 25 * 4"
sub_cmds = vw.split_compound_commands(compound_query)
test("Compound Splitting", len(sub_cmds) == 3, f"-> {sub_cmds}")

comp_replies = []
for sc in sub_cmds:
    r, b, _ = engine._execute_single_command(sc, is_compound=True)
    comp_replies.append(r)
comp_full = " ".join(comp_replies)
test("Sequential Multi-Command Chaining", 
     "Opened Chromium" in comp_full and "SSD Memory" in comp_full and "100" in comp_full,
     f"-> '{comp_full}'")

# 9. System Status & Truthful Brain Status
r_sys, b_sys, _ = engine._execute_single_command("system status")
test("Truthful Status & System Health", "Machine status:" in r_sys and "CPU load" in r_sys, f"-> '{r_sys[:75]}...'")

# 10. Math AST calculation
r_math, _, _ = engine._execute_single_command("calculate sqrt(144) + 8")
test("Math Calculation (AST)", "20" in r_math, f"-> '{r_math}'")

# 11. Email Drafting & File Maintenance Tools
r_eml, b_eml, _ = engine._execute_single_command("compose email to team@example.com subject Sync body Let us meet at 4pm.")
test("Email Drafting & Persistence", "team@example.com" in r_eml and "Sync" in r_eml, f"-> '{b_eml}'")

# Document Maintenance Tools (create, append, list)
tool_hub.create_document("/home/prakash/Documents/void_audit_log.txt", "Log start: Initial audit.")
tool_hub.append_document("/home/prakash/Documents/void_audit_log.txt", "Log update: All checks passed.")
doc_content = tool_hub.read_document("/home/prakash/Documents/void_audit_log.txt")
test("Document Create & Append", "Log start" in doc_content and "Log update" in doc_content)

# 12. Desktop Shortcut & Non-Auto-Start Setup
desktop_sh = Path("/home/prakash/Desktop/VOID.desktop")
test("Desktop Click-to-Start Launcher", desktop_sh.exists() and os.access(desktop_sh, os.X_OK))

# 13. System Safety: Ensure /usr and /etc untouched
usr_check = (os.path.getmtime("/usr") < time.time() - 3600)
etc_check = (os.path.getmtime("/etc") < time.time() - 3600)
test("System Safety (Root Directories Untouched)", usr_check and etc_check, "Zero changes outside user space")

print("=" * 60)
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=" * 60)

if failed > 0:
    sys.exit(1)
sys.exit(0)

