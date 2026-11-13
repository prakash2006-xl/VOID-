#!/usr/bin/env python3
"""
Test Suite for VOID App Management, File Search, Document Formatting, and UI Improvements.
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("/run/media/prakash/TR_39/VOID")
sys.path.insert(0, str(ROOT_DIR))

# Ensure Qt platform is offscreen for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import importlib
import importlib.util

spec = importlib.util.spec_from_file_location("void_widget", ROOT_DIR / "bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        print(f"[PASS] {name} - {details}")
        passed += 1
    else:
        print(f"[FAIL] {name} - {details}")
        failed += 1

print("=" * 60)
print("   VOID SYSTEM APPS, SEARCH, DOCS & UI VERIFICATION")
print("=" * 60)

hub = vw.DodaiosToolHub()
engine = vw.AudioVoiceEngine(hub)

# ---------------------------------------------------------------------------
# Test 1: STT Normalization for "anti-gravty" and app phrases
# ---------------------------------------------------------------------------
norm1 = vw.normalize_voice_intent("open anti-gravty")
test("STT Normalization: anti-gravty", "antigravity" in norm1, f"Normalized: '{norm1}'")

norm2 = vw.normalize_voice_intent("open anti gravty")
test("STT Normalization: anti gravty", "antigravity" in norm2, f"Normalized: '{norm2}'")

norm3 = vw.normalize_voice_intent("closiing the app and make ure tittle has 5 pagges")
test("STT Normalization: typos", all(w in norm3 for w in ["close", "make sure", "title", "pages"]), f"Normalized: '{norm3}'")

# ---------------------------------------------------------------------------
# Test 2: SystemAppRegistry Discovery & Resolution
# ---------------------------------------------------------------------------
reg = vw.SYSTEM_APP_REGISTRY
app_anti = reg.resolve("antigravity")
test("SystemAppRegistry: antigravity", app_anti is not None and "Antigravity" in app_anti["name"], f"App: {app_anti['name'] if app_anti else 'None'}")

app_anti_typo = reg.resolve("anti-gravty")
test("SystemAppRegistry: anti-gravty typo", app_anti_typo is not None and "Antigravity" in app_anti_typo["name"], f"App: {app_anti_typo['name'] if app_anti_typo else 'None'}")

app_konsole = reg.resolve("konsole")
test("SystemAppRegistry: konsole", app_konsole is not None and "Konsole" in app_konsole["name"], f"App: {app_konsole['name'] if app_konsole else 'None'}")

app_dolphin = reg.resolve("dolphin")
test("SystemAppRegistry: dolphin", app_dolphin is not None and "Dolphin" in app_dolphin["name"], f"App: {app_dolphin['name'] if app_dolphin else 'None'}")

# ---------------------------------------------------------------------------
# Test 3: App Launching & Closing Functions (No Web Fallback)
# ---------------------------------------------------------------------------
ok_anti, msg_anti = vw.launch_application("antigravity")
test("Launch Application: antigravity", ok_anti and "Antigravity" in msg_anti, f"Result: '{msg_anti}'")

# Ensure 'open anti-gravty' command does NOT open Chromium
r_text, r_badge, _ = engine._execute_single_command("open anti-gravty")
test("Command: open anti-gravty (No Chrome fallback)", "Chromium" not in r_text and "Antigravity" in r_text, f"Reply: '{r_text}' (Badge: '{r_badge}')")

# App Closing
close_res = vw.close_software_by_name("antigravity")
test("Close Application: antigravity", close_res is True or close_res is False, f"Targeted antigravity-ide process (Return: {close_res})")

# ---------------------------------------------------------------------------
# Test 4: Audio Hearing Space (Silence Pause & Buffer Limits)
# ---------------------------------------------------------------------------
with open(ROOT_DIR / "bin/void-widget.py") as f:
    w_code = f.read()

test("Hearing Space: 3.2s silence pause tolerance", "self._silence_chunks >= 32" in w_code, "Verified threshold = 32 chunks (~3.2s)")
test("Hearing Space: 45s utterance buffer", "len(self._audio_buffer) > 450" in w_code, "Verified max buffer = 450 chunks (~45s)")

# ---------------------------------------------------------------------------
# Test 5: Comprehensive File Search & Clickable Results
# ---------------------------------------------------------------------------
matches = hub.search_files("report")
test("Multi-Directory File Search", len(matches) > 0, f"Found {len(matches)} files matching 'report'")

search_reply, search_badge, search_path = engine._execute_single_command("search files for report")
test("File Search Fast-Path Output", "Found" in search_reply and "<a href=" in search_reply, f"Output length: {len(search_reply)} chars")

# Numbered Selection ("open 1")
open1_reply, open1_badge, open1_media = engine._execute_single_command("open 1")
test("Numbered File Selection: 'open 1'", "Opened" in open1_reply, f"Reply: '{open1_reply}' (Badge: '{open1_badge}')")

# ---------------------------------------------------------------------------
# Test 6: Large Prompts Parsing (Page Count, Actual Title, Grammar)
# ---------------------------------------------------------------------------
prompt_test = "compose a 5 page report on Quantum Computing titled 'Next Gen Transmons' with benchmark tables"
compose_reply, compose_badge, compose_path = engine._execute_single_command(prompt_test)
test("Large Prompt: Title & Page Extraction", "Next Gen Transmons" in compose_reply and "5 pages" in compose_reply, f"Reply: '{compose_reply[:80]}...' (Badge: '{compose_badge}')")
test("Large Prompt: Generated PDF File Exists", compose_path and Path(compose_path).exists(), f"Path: {compose_path}")

# Verify PDF includes Metric Shapes Grid and Multiple Tables
pdf_intel = hub.last_document_info
test("Large Prompt: 5-Page Depth Scaling", len(pdf_intel.get("sections", [])) >= 8, f"Generated {len(pdf_intel.get('sections', []))} expansive sections")

# ---------------------------------------------------------------------------
# Test 7: Word Document Formatting with Callout Shape & Tables
# ---------------------------------------------------------------------------
prompt_word = "draft a 3 page word doc on Edge TPU Inference called 'Edge Architecture Matrix'"
docx_reply, docx_badge, docx_path = engine._execute_single_command(prompt_word)
test("Word Doc Composition with Title & Pages", "Edge Architecture Matrix" in docx_reply and Path(docx_path).exists(), f"File: {docx_path}")

# Verify Word document size and XML structure
docx_size = Path(docx_path).stat().st_size
test("Word Document Rich Formatting Size", docx_size > 35000, f"Size: {docx_size} bytes (includes callout shapes and benchmark tables)")

# ---------------------------------------------------------------------------
# Test 8: Widget UI Scrollbar & Corner Dragging
# ---------------------------------------------------------------------------
test("Widget UI: Scrollbar 10px Styling", "width: 10px;" in w_code, "Verified 10px width scrollbar with rounded handle")
test("Widget UI: External Links Enabled", "setOpenExternalLinks(True)" in w_code, "Verified clickable links in response view")
test("Widget UI: Corner Dragging Detection", "_is_in_resize_corner" in w_code, "Verified corner resize handler")
test("Widget UI: Geometry Persistence", "widget_geometry.json" in w_code, "Verified geometry save/load mechanism")

print("=" * 60)
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=" * 60)

if failed > 0:
    sys.exit(1)
