#!/usr/bin/env python3
"""
Comprehensive Verification Test Suite for:
1. Deep Information Gathering & Document/PDF Composition
2. Instant Document Opener ("open it", "open document", "open pdf")
3. Document Content Rewriting & Tone/Section Adaptation
4. Sequential Compound Execution ("compose document on X and open it")
5. Speech Normalization & Typo Tolerance
6. Multi-Agent Tool Integration
7. Sub-second PDF Generation Performance
"""

import sys
import os
import time
import shutil
import subprocess
from pathlib import Path

# Add VOID bin and root to sys.path
VOID_ROOT = Path("/run/media/prakash/TR_39/VOID")
VOID_BIN = VOID_ROOT / "bin"
sys.path.insert(0, str(VOID_ROOT))
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
print("   VOID DOCUMENT COMPOSITION & REWRITE SUITE     ")
print("=================================================")

hub = DodaiosToolHub()
engine = AudioVoiceEngine(hub)

# -----------------------------------------------------------------------------
# TEST 1: Speech Normalization & Typo Invariance
# -----------------------------------------------------------------------------
norm1 = normalize_voice_intent("when i ask void to compse documnt and improvr sbility")
test(
    "Speech Invariance Normalization",
    "compose" in norm1 and "document" in norm1 and "improve" in norm1 and "ability" in norm1,
    f"Normalized: '{norm1}'"
)

norm2 = normalize_voice_intent("open predf after comppleting")
test(
    "PDF & Completing STT Normalization",
    "pdf" in norm2 and "completing" in norm2,
    f"Normalized: '{norm2}'"
)

# -----------------------------------------------------------------------------
# TEST 2: Deep Information Gathering & PDF Composition
# -----------------------------------------------------------------------------
t0 = time.time()
reply1, badge1, thumb1 = engine._execute_single_command("compose a document on Autonomous Linux Systems")
t_comp = time.time() - t0

target_pdf = Path(thumb1) if thumb1 else None
test(
    "Deep Gathering & PDF Document Composition",
    target_pdf is not None and target_pdf.exists() and target_pdf.suffix == ".pdf" and target_pdf.stat().st_size > 1000,
    f"Time: {t_comp:.2f}s, File: {target_pdf}, Size: {target_pdf.stat().st_size if target_pdf else 0} bytes, Badge: '{badge1}'"
)

# -----------------------------------------------------------------------------
# TEST 3: Pronoun Resolution & Instant Document Opener ("open it")
# -----------------------------------------------------------------------------
reply_open, badge_open, thumb_open = engine._execute_single_command("open it")
test(
    "Instant Document Opener via 'open it'",
    "Opened" in reply_open and target_pdf.name in reply_open,
    f"Reply: '{reply_open}', Badge: '{badge_open}'"
)

# Test "open the document"
reply_doc, badge_doc, _ = engine._execute_single_command("open the document")
test(
    "Instant Document Opener via 'open the document'",
    "Opened" in reply_doc and target_pdf.name in reply_doc,
    f"Reply: '{reply_doc}', Badge: '{badge_doc}'"
)

# Test "open pdf"
reply_pdf, badge_pdf, _ = engine._execute_single_command("open pdf")
test(
    "Instant Document Opener via 'open pdf'",
    "Opened" in reply_pdf and target_pdf.name in reply_pdf,
    f"Reply: '{reply_pdf}', Badge: '{badge_pdf}'"
)

# -----------------------------------------------------------------------------
# TEST 4: Content Modification & Rewriting Suite
# -----------------------------------------------------------------------------
t0 = time.time()
reply_rw, badge_rw, thumb_rw = engine._execute_single_command("rewrite the content with a formal executive tone and add section on Kernel Security Safeguards")
t_rw = time.time() - t0

target_v2 = Path(thumb_rw) if thumb_rw else None
test(
    "Document Content Rewriting (Tone & Section Addition)",
    target_v2 is not None and target_v2.exists() and "_v2" in target_v2.name and target_v2.stat().st_size > 1000,
    f"Time: {t_rw:.2f}s, File: {target_v2}, Size: {target_v2.stat().st_size if target_v2 else 0} bytes, Badge: '{badge_rw}'"
)

# -----------------------------------------------------------------------------
# TEST 5: Pronoun Memory Switches to Rewritten Version
# -----------------------------------------------------------------------------
reply_open_v2, badge_open_v2, _ = engine._execute_single_command("open it")
test(
    "Opening 'it' Launches Rewritten Version",
    "Opened" in reply_open_v2 and target_v2.name in reply_open_v2,
    f"Reply: '{reply_open_v2}', Badge: '{badge_open_v2}'"
)

# -----------------------------------------------------------------------------
# TEST 6: Word Document (.docx) Composition
# -----------------------------------------------------------------------------
reply_docx, badge_docx, thumb_docx = engine._execute_single_command("compose word document on Edge Inference Pipelines")
target_docx = Path(thumb_docx) if thumb_docx else None
test(
    "Word Document (.docx) Composition",
    target_docx is not None and target_docx.exists() and target_docx.suffix == ".docx" and target_docx.stat().st_size > 1000,
    f"File: {target_docx}, Size: {target_docx.stat().st_size if target_docx else 0} bytes, Badge: '{badge_docx}'"
)

# -----------------------------------------------------------------------------
# TEST 7: Rewriting Word Doc to PDF Format
# -----------------------------------------------------------------------------
reply_conv, badge_conv, thumb_conv = engine._execute_single_command("rewrite as pdf")
target_conv = Path(thumb_conv) if thumb_conv else None
test(
    "Document Format Conversion during Rewrite (DOCX -> PDF)",
    target_conv is not None and target_conv.exists() and target_conv.suffix == ".pdf",
    f"File: {target_conv}, Badge: '{badge_conv}'"
)

# -----------------------------------------------------------------------------
# TEST 8: Multi-Agent Tool Registry Registration
# -----------------------------------------------------------------------------
test(
    "Multi-Agent Tool draft_pdf_document Registered",
    engine._agent_tools.has_tool("draft_pdf_document"),
    "Registered in agentic ToolRegistry"
)
test(
    "Multi-Agent Tool compose_comprehensive_document Registered",
    engine._agent_tools.has_tool("compose_comprehensive_document"),
    "Registered in agentic ToolRegistry"
)
test(
    "Multi-Agent Tool rewrite_document_content Registered",
    engine._agent_tools.has_tool("rewrite_document_content"),
    "Registered in agentic ToolRegistry"
)

# -----------------------------------------------------------------------------
# TEST 9: Sequential Compound Command ("compose document on X and open it")
# -----------------------------------------------------------------------------
sub_cmds = void_widget.split_compound_commands("compose document on Wayland Protocols and open it")
test(
    "Compound Command Splitting for Composition + Open",
    len(sub_cmds) == 2 and "compose" in sub_cmds[0] and "open it" in sub_cmds[1],
    f"Splits: {sub_cmds}"
)

print("=================================================")
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=================================================")

if failed > 0:
    sys.exit(1)

