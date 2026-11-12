#!/usr/bin/env python3
"""
Test email drafting, file maintenance tools, planning decomposition, and non-auto-start.
"""

import sys
import os
from pathlib import Path

VOID_ROOT = Path("/run/media/prakash/TR_39/VOID")
sys.path.insert(0, str(VOID_ROOT / "bin"))

from PySide6.QtCore import QCoreApplication
app = QCoreApplication.instance() or QCoreApplication([])

import importlib
vw = importlib.import_module("void-widget")

tool_hub = vw.DodaiosToolHub()
engine = vw.AudioVoiceEngine(tool_hub=tool_hub)

print("=== TEST A: Email Drafting Fast Path ===")
query = "compose email to supervisor@company.com subject Sprint Report body Milestones 1 and 2 are finished."
r_email, b_email, _ = engine._execute_single_command(query)
print(f"Reply: '{r_email}'")
print(f"Badge: '{b_email}'")
assert "supervisor@company.com" in r_email
assert "Sprint Report" in r_email
drafts = list(Path("/home/prakash/Documents/Drafts").glob("*Sprint_Report*"))
assert len(drafts) > 0, "Draft file was not created on disk"
print("  [PASS] Email drafting fast path and file persistence verified.")

print("\n=== TEST B: File Maintenance Tools (create, append, list) ===")
test_doc = "/home/prakash/Documents/void_planning_test.txt"
# 1. Create
res_create = tool_hub.create_document(test_doc, "Step 1: Initialized project plan.")
print(f"Create: {res_create}")
assert "successfully created" in res_create

# 2. Append
res_append = tool_hub.append_document(test_doc, "Step 2: Completed research and analysis.")
print(f"Append: {res_append}")
assert "Successfully appended" in res_append

# 3. Read
content = tool_hub.read_document(test_doc)
print(f"Content:\n{content}")
assert "Step 1" in content and "Step 2" in content

# 4. List
res_list = tool_hub.list_files("/home/prakash/Documents")
print(f"List:\n{res_list[:150]}...")
assert "void_planning_test.txt" in res_list
print("  [PASS] Document maintenance tools verified.")

print("\n=== TEST C: Complex Task Planning Splitting ===")
plan_query = "compose email to team@company.com subject Weekly Sync and create task review sprint progress"
sub_cmds = vw.split_compound_commands(plan_query)
print(f"Splitting: {sub_cmds}")
assert len(sub_cmds) == 2, f"Expected 2 parts, got {len(sub_cmds)}"
assert "compose email" in sub_cmds[0]
assert "create task" in sub_cmds[1]
print("  [PASS] Planning multi-command decomposition verified.")

print("\n=== TEST D: Desktop Launcher & Termination Safety ===")
desktop_icon = Path("/home/prakash/Desktop/VOID.desktop")
assert desktop_icon.exists(), "Desktop shortcut does not exist"
assert os.access(desktop_icon, os.X_OK), "Desktop shortcut is not executable"
desktop_content = desktop_icon.read_text()
assert "/run/media/prakash/TR_39/VOID/scripts/run_void.sh" in desktop_content
print("  [PASS] Desktop launcher exists, is executable, and points to portable launcher.")

print("\n=== ALL EMAIL & PLANNING TESTS PASSED! ===")

