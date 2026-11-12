#!/usr/bin/env python3
"""
Automated Verification Suite for:
1. Pending Action Inconsistency / Stale Task Repetition Fix
2. Live Voice Dictation (Speech-to-Document) Engine
3. Word (.docx) Professional Document Drafting
4. Excel (.xlsx) Formatted Spreadsheet Drafting
5. Web Research & Report Synthesis
6. WhatsApp Web Direct Launch & Typo Tolerance
7. Capsule Glass Frame Rendering & Dimensions
"""

import sys
import os
import time
import shutil
import subprocess
from pathlib import Path

# Add VOID bin to sys.path
VOID_BIN = Path("/run/media/prakash/TR_39/VOID/bin")
sys.path.insert(0, str(VOID_BIN))

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", str(VOID_BIN / "void-widget.py"))
void_widget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(void_widget)

DodaiosToolHub = void_widget.DodaiosToolHub
AudioVoiceEngine = void_widget.AudioVoiceEngine
VoidMiniWidget = void_widget.VoidMiniWidget
REPORTS_DIR = void_widget.REPORTS_DIR
normalize_voice_intent = void_widget.normalize_voice_intent

passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {name} - {details}")
    else:
        failed += 1
        print(f"[FAIL] {name} - {details}")

print("=================================================")
print("   VOID ENHANCEMENT VERIFICATION SUITE           ")
print("=================================================")

hub = DodaiosToolHub()
engine = AudioVoiceEngine(hub)

# -----------------------------------------------------------------------------
# TEST 1: Stale Task Repetition & Pending Action Discard Fix
# -----------------------------------------------------------------------------
# Simulate pending email prompt
engine._pending_action = {
    "type": "email_recipient",
    "subject": "Missing Party",
    "body": "Sorry I could not attend",
    "awaiting": "recipient"
}

# User says a NEW command instead of answering recipient
reply, badge, _ = engine._execute_single_command("open terminal")
test(
    "Pending Action Discarded on New Command",
    engine._pending_action is None and "Terminal" in badge,
    f"Reply: '{reply[:40]}...', Badge: '{badge}', Pending: {engine._pending_action}"
)

# Test legitimate recipient input works when pending
engine._pending_action = {
    "type": "email_recipient",
    "subject": "Missing Party",
    "body": "Sorry I could not attend",
    "awaiting": "recipient"
}
reply, badge, _ = engine._execute_single_command("rskakavin@gmail.com")
test(
    "Pending Action Accepts Valid Recipient",
    engine._pending_action is None and "rskakavin@gmail.com" in badge,
    f"Reply: '{reply[:40]}...', Badge: '{badge}'"
)

# -----------------------------------------------------------------------------
# TEST 2: Live Voice Dictation (Speech-to-Document) Mode
# -----------------------------------------------------------------------------
reply, badge, _ = engine._execute_single_command("start dictation to note SystemArchitecture")
test(
    "Voice Dictation Start Fast-Path",
    engine._dictation_mode is True and engine._dictation_file is not None and "SystemArchitecture.md" in engine._dictation_file.name,
    f"Badge: '{badge}', File: {engine._dictation_file}"
)

# Simulate spoken transcription stream via _process_task
engine._process_task("The neural voice pipeline operates with Piper local TTS at 160 words per minute.")
engine._process_task("Persistent memory stores user context on NVMe SSD across 1.5 gigabytes.")

# Stop dictation
engine._process_task("stop dictation")
test(
    "Voice Dictation Stop & File Persistence",
    engine._dictation_mode is False and engine._dictation_file.exists(),
    f"Dictation Mode: {engine._dictation_mode}, Exists: {engine._dictation_file.exists()}"
)

content = engine._dictation_file.read_text(encoding="utf-8")
test(
    "Voice Dictation Content Integrity",
    "Piper local TTS" in content and "NVMe SSD" in content,
    f"Length: {len(content)} chars. Preview: {content[:100]}..."
)

# Clean test note
engine._dictation_file.unlink(missing_ok=True)

# -----------------------------------------------------------------------------
# TEST 3: Word Document (.docx) Professional Drafting
# -----------------------------------------------------------------------------
reply, badge, _ = engine._execute_single_command("draft doc on Autonomous Linux Agents")
docx_files = list(REPORTS_DIR.glob("*Autonomous_Linux_Agents*.docx"))
test(
    "Word Document (.docx) Generation",
    len(docx_files) > 0 and docx_files[0].stat().st_size > 5000,
    f"Badge: '{badge}', File: {docx_files[0] if docx_files else 'None'}"
)
if docx_files:
    docx_files[0].unlink(missing_ok=True)

# -----------------------------------------------------------------------------
# TEST 4: Excel Spreadsheet (.xlsx) Professional Drafting
# -----------------------------------------------------------------------------
reply, badge, _ = engine._execute_single_command("draft excel on Cloud Infrastructure Budget")
xlsx_files = list(REPORTS_DIR.glob("*Cloud_Infrastructure_Budget*.xlsx"))
test(
    "Excel Spreadsheet (.xlsx) Generation",
    len(xlsx_files) > 0 and xlsx_files[0].stat().st_size > 4000,
    f"Badge: '{badge}', File: {xlsx_files[0] if xlsx_files else 'None'}"
)
if xlsx_files:
    xlsx_files[0].unlink(missing_ok=True)

# -----------------------------------------------------------------------------
# TEST 5: Web Research & Synthesis into Document
# -----------------------------------------------------------------------------
reply, badge, _ = engine._execute_single_command("research about Open Source AI Models and write in doc")
res_docs = list(REPORTS_DIR.glob("*Open_Source_AI_Models*.docx")) + list(REPORTS_DIR.glob("*Research_Report*.docx"))
test(
    "Web Research & Synthesis to Document",
    len(res_docs) > 0,
    f"Badge: '{badge}', File: {res_docs[0] if res_docs else 'None'}"
)
for f in res_docs:
    f.unlink(missing_ok=True)

# -----------------------------------------------------------------------------
# TEST 6: WhatsApp Web Direct Launch & Typo Tolerance
# -----------------------------------------------------------------------------
reply, badge, _ = engine._execute_single_command("open watsapp web")
test(
    "WhatsApp Web Typo Tolerance ('watsapp web')",
    "WhatsApp Web" in reply and "WhatsApp Web" in badge,
    f"Reply: '{reply}', Badge: '{badge}'"
)

reply, badge, _ = engine._execute_single_command("open whats app web")
test(
    "WhatsApp Web Spaced Typo ('whats app web')",
    "WhatsApp Web" in reply and "WhatsApp Web" in badge,
    f"Reply: '{reply}', Badge: '{badge}'"
)

reply, badge, _ = engine._execute_single_command("whatsapp message see you tomorrow at lunch")
test(
    "WhatsApp Web Pre-filled Message",
    "prepared with your message" in reply,
    f"Reply: '{reply}', Badge: '{badge}'"
)

# -----------------------------------------------------------------------------
# TEST 7: Capsule Glass Dimensions & Background Opacity
# -----------------------------------------------------------------------------
widget = VoidMiniWidget()
test(
    "Widget Capsule Height",
    widget.COLLAPSED_H >= 58,
    f"COLLAPSED_H = {widget.COLLAPSED_H}px"
)

card_style = widget._card.styleSheet()
test(
    "Widget Pure Glass Island Frame",
    isinstance(widget._card, void_widget.GlassIslandFrame),
    f"Card class: {widget._card.__class__.__name__}"
)

test(
    "Quick Chips Dictation & Document Support",
    any("Dictate" in btn.text() for btn in widget._expanded_box.findChildren(void_widget.QPushButton)),
    f"Chips found in expanded container"
)

widget.close()
engine._is_running = False

print("=================================================")
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=================================================")

if failed > 0:
    os._exit(1)
os._exit(0)
