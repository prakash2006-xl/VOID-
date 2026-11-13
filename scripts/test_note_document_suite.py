#!/usr/bin/env python3
"""
Comprehensive Verification Test Suite for the VOID Note Document Feature:
1. Note Document Creation (save_note / take note)
2. Note Document Appending (append_note / add to note)
3. Note Document Reading (read_note / read note)
4. Note Listing (list_notes / list my notes)
5. Note Content Search (search_notes / search notes for)
6. Note Directory Maintenance & Auto-Indexing (maintain_notes / maintain notes)
7. Note to PDF Compilation & Export (export_note_to_pdf / convert note to pdf)
8. Instant Opener & Pronoun Continuity ('open it')
9. Agentic Multi-Agent Tool Integration
"""

import sys
import os
import time
import shutil
from pathlib import Path

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
NOTES_DIR = void_widget.NOTES_DIR
REPORTS_DIR = void_widget.REPORTS_DIR

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
print("   VOID NOTE DOCUMENT FEATURE TEST SUITE         ")
print("=================================================")

hub = DodaiosToolHub()
engine = AudioVoiceEngine(hub)

# -----------------------------------------------------------------------------
# TEST 1: Note Document Creation (Fast-Path & Metadata)
# -----------------------------------------------------------------------------
test_title = "Quantum Architecture Notes"
test_content = "Superconducting transmons maintain coherence at 15 millikelvin. Error syndrome decoding executes via FPGA."
reply1, badge1, thumb1 = engine._execute_single_command(f"take note {test_title}: {test_content}")

note_file = NOTES_DIR / "Quantum_Architecture_Notes.md"
test(
    "Note Document Creation",
    note_file.exists() and "saved" in reply1.lower(),
    f"File: {note_file.name}, Badge: '{badge1}', Reply: '{reply1[:50]}...'"
)

note_text = note_file.read_text(encoding="utf-8")
test(
    "Note Document Formatting & Metadata",
    f"# {test_title}" in note_text and "Category:" in note_text and "Author: Prakash" in note_text,
    f"Header verified in {note_file.name}"
)

# -----------------------------------------------------------------------------
# TEST 2: Appending to Existing Note Document
# -----------------------------------------------------------------------------
append_text = "Surface code lattice parameter d=5 achieves logical error rate below 10^-6."
reply2, badge2, thumb2 = engine._execute_single_command(f"append to note {test_title} that {append_text}")

updated_text = note_file.read_text(encoding="utf-8")
test(
    "Appending to Note Document",
    append_text in updated_text and "Added:" in updated_text,
    f"Reply: '{reply2[:50]}...', Badge: '{badge2}'"
)

# -----------------------------------------------------------------------------
# TEST 3: Reading Note Documents
# -----------------------------------------------------------------------------
reply3, badge3, _ = engine._execute_single_command(f"read note {test_title}")
test(
    "Reading Note Document Content",
    "Superconducting transmons" in reply3 and "Surface code lattice" in reply3,
    f"Badge: '{badge3}', Preview: '{reply3[:60]}...'"
)

# -----------------------------------------------------------------------------
# TEST 4: Listing Note Documents
# -----------------------------------------------------------------------------
reply4, badge4, _ = engine._execute_single_command("list my notes")
test(
    "Listing Note Documents",
    "Quantum_Architecture_Notes.md" in reply4 and "saved note documents" in reply4,
    f"Badge: '{badge4}', Sample: '{reply4.splitlines()[0]}'"
)

# -----------------------------------------------------------------------------
# TEST 5: Searching Inside Note Documents
# -----------------------------------------------------------------------------
reply5, badge5, _ = engine._execute_single_command("search notes for transmons")
test(
    "Searching Note Documents Content",
    "Quantum Architecture Notes" in reply5 and "millikelvin" in reply5,
    f"Badge: '{badge5}', Match excerpt: '{reply5[:70]}...'"
)

# -----------------------------------------------------------------------------
# TEST 6: Note Directory Maintenance & Auto-Indexing
# -----------------------------------------------------------------------------
reply6, badge6, thumb6 = engine._execute_single_command("maintain notes")
index_file = NOTES_DIR / "INDEX.md"
test(
    "Note Maintenance & INDEX Catalog Generation",
    index_file.exists() and "cataloged" in reply6,
    f"Reply: '{reply6}', Index size: {index_file.stat().st_size} bytes"
)

index_text = index_file.read_text(encoding="utf-8")
test(
    "INDEX Catalog Contains Active Notes Table",
    "| Note Title | File Name | Size | Last Updated |" in index_text and "Quantum Architecture Notes" in index_text,
    "INDEX.md markdown table verified"
)

# -----------------------------------------------------------------------------
# TEST 7: Compiling Note Document into Publication PDF
# -----------------------------------------------------------------------------
reply7, badge7, thumb7 = engine._execute_single_command(f"convert note {test_title} to pdf")
pdf_export = Path(thumb7) if thumb7 else None
test(
    "Compiling Note Document to PDF",
    pdf_export is not None and pdf_export.exists() and pdf_export.suffix == ".pdf" and pdf_export.stat().st_size > 1000,
    f"File: {pdf_export}, Size: {pdf_export.stat().st_size if pdf_export else 0} bytes, Badge: '{badge7}'"
)

# -----------------------------------------------------------------------------
# TEST 8: Instant Opening of Exported Note PDF via 'open it'
# -----------------------------------------------------------------------------
reply8, badge8, _ = engine._execute_single_command("open it")
test(
    "Instant Opener Opens Exported Note PDF",
    "Opened" in reply8 and pdf_export.name in reply8,
    f"Reply: '{reply8}', Badge: '{badge8}'"
)

# -----------------------------------------------------------------------------
# TEST 9: Multi-Agent Tool Integration
# -----------------------------------------------------------------------------
test("Agentic Tool append_note", engine._agent_tools.has_tool("append_note"), "Registered")
test("Agentic Tool list_notes", engine._agent_tools.has_tool("list_notes"), "Registered")
test("Agentic Tool search_notes", engine._agent_tools.has_tool("search_notes"), "Registered")
test("Agentic Tool export_note_to_pdf", engine._agent_tools.has_tool("export_note_to_pdf"), "Registered")
test("Agentic Tool maintain_notes", engine._agent_tools.has_tool("maintain_notes"), "Registered")

# Clean test files
if note_file.exists():
    note_file.unlink()
if pdf_export and pdf_export.exists():
    pdf_export.unlink()

print("=================================================")
print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
print("=================================================")

if failed > 0:
    sys.exit(1)
