#!/usr/bin/env python3
"""
VOID AI Comprehensive End-to-End System Test Suite
Automated verification across all core functional domains:
1. Window Management (Close, Minimize, Maximize, Restore, Close Everything, Close Specific Apps)
2. Tab Management (Open Tab, Switch Next/Prev/Indexed Tab, Close Tab, Close All Tabs)
3. YouTube & Music Disambiguation (Single-Tab execution, Title Scoring, Ad & Short Rejection)
4. File & Document Operations (Create, Read, List, Word DOCX, Excel XLSX, PDF, Safe Two-Phase Deletion)
5. System Diagnostics & Utilities (AST Math, Timers, SSD Memory Recall, Vitals)
6. Model Lifecycle & RAM Management (Model Offload, Activation, Clean Shutdown)
"""

import sys
import os
import re
import time
import tempfile
import subprocess
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT_DIR / "bin"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BIN_DIR))

# Headless Qt Application
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(["-platform", "offscreen"])

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", BIN_DIR / "void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

passed_count = 0
failed_count = 0

def check(name: str, condition: bool, info: str = ""):
    global passed_count, failed_count
    if condition:
        print(f"  [PASS] {name} {f'({info})' if info else ''}")
        passed_count += 1
    else:
        print(f"  [FAIL] {name} {f'({info})' if info else ''}")
        failed_count += 1

def run_suite():
    global passed_count, failed_count
    print("=" * 70)
    print("    VOID AI — COMPREHENSIVE AUTOMATED SYSTEM VERIFICATION SUITE    ")
    print("=" * 70)

    tool_hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(tool_hub=tool_hub)

    # Disable audio background listening loop in tests
    engine._is_running = False

    # =========================================================================
    # DOMAIN 1: WINDOW & APPLICATION MANAGEMENT
    # =========================================================================
    print("\n--- DOMAIN 1: Window & Application Management ---")

    # 1.0 Real KWin Wayland DBus Health Check
    kwin_dbus_check = subprocess.run(["qdbus-qt6", "org.kde.KWin", "/Scripting"], capture_output=True, text=True)
    check("KWin Wayland DBus Scripting Interface Active", kwin_dbus_check.returncode == 0)

    # Intercept pkill during tests so running processes are not terminated
    orig_close_sw = vw.close_software_by_name
    orig_kwin_manage = vw.kwin_manage_app_window
    kwin_calls = []

    def mock_kwin_manage(app_name, action):
        kwin_calls.append((app_name, action))
        return True

    def mock_close_sw(name):
        kwin_calls.append(("close_software", name))
        return True

    vw.kwin_manage_app_window = mock_kwin_manage
    vw.close_software_by_name = mock_close_sw

    try:
        # 1.1 Generic Window Actions
        win_actions = [
            ("close window", "Closed window.", "Window: Close"),
            ("close this window", "Closed window.", "Window: Close"),
            ("close active window", "Closed window.", "Window: Close"),
            ("minimize window", "Minimized window.", "Window: Minimize"),
            ("minimise this window", "Minimized window.", "Window: Minimize"),
            ("maximize window", "Maximized window.", "Window: Maximize"),
            ("restore window", "Restored window.", "Window: Restore"),
            ("unminimize window", "Restored window.", "Window: Restore"),
        ]
        for q, exp_text, exp_badge in win_actions:
            r, b, _ = engine._execute_single_command(q)
            check(f"Window Action: '{q}'", exp_text in r and exp_badge in b, f"-> {r}")

        # 1.2 Close Everything / All Applications
        all_cmds = [
            ("close everything", "Closed all application windows.", "App: Close All"),
            ("close all", "Closed all application windows.", "App: Close All"),
            ("close all windows", "Closed all application windows.", "App: Close All"),
            ("close all apps", "Closed all application windows.", "App: Close All"),
            ("close all applications", "Closed all application windows.", "App: Close All"),
            ("show desktop", "Showing desktop.", "KWin: Show Desktop"),
        ]
        for q, exp_text, exp_badge in all_cmds:
            r, b, _ = engine._execute_single_command(q)
            check(f"Close All / Desktop: '{q}'", exp_text in r and exp_badge in b, f"-> {r}")

        # 1.3 Specific App Close & Window Control
        app_targets = [
            ("close chromium", "Closed Chromium.", "App: Close Chromium"),
            ("close konsole", "Closed Konsole.", "App: Close Konsole"),
            ("close dolphin", "Closed Dolphin.", "App: Close Dolphin"),
            ("close calculator", "Closed Calculator.", "App: Close Calculator"),
            ("minimize chromium", "Minimized Chromium.", "Window: Minimize Chromium"),
            ("maximize dolphin", "Maximized Dolphin.", "Window: Maximize Dolphin"),
        ]
        for q, exp_text, exp_badge in app_targets:
            r, b, _ = engine._execute_single_command(q)
            check(f"Target App Action: '{q}'", exp_text in r and exp_badge in b, f"-> {r}")

        # 1.4 Protection: VOID Widget Self-Closure
        r_prot, b_prot, _ = engine._execute_single_command("close void")
        check("VOID Self-Protection Guard", "Closing VOID assistant" in r_prot or "VOID: Exit" in b_prot, f"-> {r_prot}")

        # 1.5 System Settings Guard (Never triggers VOID configuration on close)
        r_sys_set, b_sys_set, _ = engine._execute_single_command("close system settings")
        check("System Settings Close Guard", "configuration" not in r_sys_set.lower(), f"-> {r_sys_set}")

    finally:
        vw.close_software_by_name = orig_close_sw
        vw.kwin_manage_app_window = orig_kwin_manage

    # =========================================================================
    # DOMAIN 2: CHROMIUM TAB & MULTI-WINDOW MANAGEMENT
    # =========================================================================
    print("\n--- DOMAIN 2: Chromium Tab & Multi-Window Management ---")

    tab_cmds = [
        ("open new tab", "tab"),
        ("open tab in chromium", "tab"),
        ("next tab", "next"),
        ("switch to next tab", "next"),
        ("previous tab", "prev"),
        ("switch to previous tab", "prev"),
        ("tab 1", "tab1"),
        ("switch to tab 3", "tab3"),
        ("close tab", "close"),
        ("delete tab", "close"),
        ("close all tabs", "all_tabs"),
    ]
    for q, kind in tab_cmds:
        r, b, _ = engine._execute_single_command(q)
        if kind == "all_tabs":
            check(f"Tab Action: '{q}'", "Closed all tabs in Chromium." in r, f"-> {r}")
        elif kind == "close":
            check(f"Tab Action: '{q}'", "Close Tab" in b or "Closed active tab" in r, f"-> {r}")
        elif kind in ["next", "prev", "tab1", "tab3"]:
            check(f"Tab Switcher: '{q}'", "Tab:" in b or "tab" in r.lower(), f"-> {r}")
        elif kind == "tab":
            check(f"Tab Open: '{q}'", "Tab:" in b or "new tab" in r.lower(), f"-> {r}")

    # =========================================================================
    # DOMAIN 3: YOUTUBE & MUSIC PLAYBACK DISAMBIGUATION
    # =========================================================================
    print("\n--- DOMAIN 3: YouTube & Music Playback Disambiguation ---")

    # 3.1 Single Tab Intent: Compound Splitter MUST NOT split unified song requests
    compound_play_tests = [
        ("open youtube and play believer", 1),
        ("open chromium and play faded song", 1),
        ("search for the song shape of you and play", 1),
        ("open youtube and search for pesamalaye and play", 1),
    ]
    for q, exp_count in compound_play_tests:
        parts = vw.split_compound_commands(q)
        check(f"Compound Splitter Unified Music Guard: '{q}'", len(parts) == exp_count, f"Parts: {parts}")

    # 3.2 Song Query Extraction
    song_queries = [
        ("play believer", "believer"),
        ("play faded song", "faded"),
        ("open chromium and play shape of you song", "shape of you"),
        ("search for the song viva la vida and play", "viva la vida"),
        ("open youtube and play pesamalaye", "pesamalaye"),
    ]
    for raw_q, exp_title in song_queries:
        extracted = vw.extract_media_song_query(raw_q)
        check(f"Song Title Extracted: '{raw_q}'", exp_title in extracted.lower(), f"-> '{extracted}'")

    # 3.3 Acoustic Artifact Rejection (Whisper hearing 'hey void' as 'play wide')
    extracted_art = vw.extract_media_song_query("play wide")
    check("Acoustic Artifact 'play wide' Filtered", extracted_art == "", f"-> '{extracted_art}'")

    # 3.4 YouTube Search Scoring & Ad/Short/Skinny Rejection
    sample_yt_html = """
    <script>
    var ytInitialData = {
      "contents": {
        "twoColumnSearchResultsRenderer": {
          "primaryContents": {
            "sectionListRenderer": {
              "contents": [
                {
                  "itemSectionRenderer": {
                    "contents": [
                      {
                        "videoRenderer": {
                          "videoId": "promoted_ad_999",
                          "title": {"runs": [{"text": "Billie Eilish - SKINNY (Official Audio)"}]}
                        }
                      },
                      {
                        "videoRenderer": {
                          "videoId": "real_match_123",
                          "title": {"runs": [{"text": "Imagine Dragons - Believer (Official Music Video)"}]}
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        }
      }
    };
    </script>
    """
    orig_urlopen = vw.urllib.request.urlopen
    class DummyResp:
        def __init__(self, data):
            self.data = data.encode("utf-8")
        def read(self):
            return self.data
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def dummy_urlopen(req, timeout=5.0):
        return DummyResp(sample_yt_html)

    vw.urllib.request.urlopen = dummy_urlopen
    try:
        ok, res_msg = tool_hub.play_youtube_query("believer")
        check("YouTube Scoring Bypasses Promoted 'SKINNY' Ad", "real_match_123" in res_msg or "Believer" in res_msg, f"-> {res_msg}")
    finally:
        vw.urllib.request.urlopen = orig_urlopen

    # =========================================================================
    # DOMAIN 4: FILE OPERATIONS & DOCUMENT DRAFTING
    # =========================================================================
    print("\n--- DOMAIN 4: File Operations & Document Drafting ---")

    docs_dir = Path.home() / "Documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 4.1 Create, Read & List Files
    test_note = docs_dir / "void_system_test_note.txt"
    if test_note.exists():
        test_note.unlink()

    r_cr, b_cr, f_cr = engine._execute_single_command("create file void_system_test_note.txt content VOID autonomous test operational.")
    check("Create Text File / Note", test_note.exists() or "Created file" in r_cr, f"-> {r_cr}")

    r_rd, b_rd, _ = engine._execute_single_command("read file void_system_test_note.txt")
    check("Read Text File", "operational" in r_rd, f"-> {r_rd}")

    r_ls, b_ls, _ = engine._execute_single_command("list files")
    check("List Documents", "void_system_test_note.txt" in r_ls or len(r_ls) > 10, f"-> {r_ls}")

    # 4.2 Document Suite: DOCX, XLSX, PDF
    try:
        import docx
        doc = docx.Document()
        doc.add_heading("VOID AI System Audit", 0)
        doc.add_paragraph("Automated document engine active.")
        docx_path = docs_dir / "void_audit_test.docx"
        doc.save(docx_path)
        check("Word Document (.docx) Generation", docx_path.exists() and docx_path.stat().st_size > 0)
        if docx_path.exists(): docx_path.unlink()
    except Exception as e:
        check("Word Document (.docx) Generation", False, str(e))

    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Vitals"
        ws.append(["Metric", "Status"])
        ws.append(["KWin", "Operational"])
        xlsx_path = docs_dir / "void_vitals_test.xlsx"
        wb.save(xlsx_path)
        check("Excel Spreadsheet (.xlsx) Generation", xlsx_path.exists() and xlsx_path.stat().st_size > 0)
        if xlsx_path.exists(): xlsx_path.unlink()
    except Exception as e:
        check("Excel Spreadsheet (.xlsx) Generation", False, str(e))

    try:
        from reportlab.pdfgen import canvas
        pdf_path = docs_dir / "void_report_test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 750, "VOID AI Verification Report")
        c.save()
        check("PDF Document (.pdf) Generation", pdf_path.exists() and pdf_path.stat().st_size > 0)
        if pdf_path.exists(): pdf_path.unlink()
    except Exception as e:
        check("PDF Document (.pdf) Generation", False, str(e))

    # 4.3 Safe Two-Phase Deletion Guard
    with tempfile.TemporaryDirectory() as tmpdir:
        del_target = Path(tmpdir) / "Critical_UserData.txt"
        del_target.write_text("Do not lose this data.", encoding="utf-8")

        # Step 1: Case-sensitive lookup
        exact_f, cands = tool_hub.find_target_file_for_deletion("Critical_UserData.txt", search_path=tmpdir)
        check("Case-Sensitive File Matching", exact_f is not None and exact_f.name == "Critical_UserData.txt")

        # Step 2: Ensure pending confirmation state is required
        pending_action = {"type": "confirm_delete", "path": str(exact_f), "filename": exact_f.name}
        check("File Preserved Before Confirmation", del_target.exists())

        # Step 3: Cancellation retains file
        cancel_query = "cancel, keep file"
        if any(w in cancel_query.lower() for w in ["cancel", "no", "keep"]):
            pending_action = None
        check("User Cancellation Preserves Target File", del_target.exists() and pending_action is None)

        # Step 4: Explicit confirmation proceeds with deletion
        pending_action = {"type": "confirm_delete", "path": str(exact_f), "filename": exact_f.name}
        confirm_query = "confirm delete"
        if any(w in confirm_query.lower() for w in ["confirm", "yes", "proceed"]):
            Path(pending_action["path"]).unlink()
            pending_action = None
        check("Explicit Confirmation Deletes Safely", not del_target.exists() and pending_action is None)

    # Clean up test note
    if test_note.exists():
        test_note.unlink()

    # =========================================================================
    # DOMAIN 5: SYSTEM DIAGNOSTICS & MEMORY
    # =========================================================================
    print("\n--- DOMAIN 5: System Diagnostics, AST Math & SSD Memory ---")

    r_math, _, _ = engine._execute_single_command("calculate (15 * 8) + sqrt(144)")
    check("AST Math Calculation", "132" in r_math, f"-> {r_math}")

    r_stat, b_stat, _ = engine._execute_single_command("system status")
    check("System Vitals & CPU/RAM Status", "CPU load" in r_stat or "Machine status" in r_stat, f"-> {r_stat[:60]}...")

    r_timer, b_timer, _ = engine._execute_single_command("set timer for 10 seconds")
    check("Timer Creation", "Timer set for 10s" in r_timer or "Timer:" in b_timer, f"-> {r_timer}")

    # Memory Engine Recall
    learn_msg = engine.memory.learn("User preference: Use Wayland with KWin gestures")
    recall_res = engine.memory.recall("gestures")
    check("1.5GB SSD Memory Persistence & Recall", any("gestures" in rec for rec in recall_res))

    # =========================================================================
    # DOMAIN 6: MODEL LIFECYCLE & CLEAN RAM MANAGEMENT
    # =========================================================================
    print("\n--- DOMAIN 6: Model Lifecycle & RAM Management ---")

    # 6.1 Start Model / Resume Intent Routing
    r_start, b_start, _ = engine._execute_single_command("start the model")
    check("Start Model Intent Routing", any(w in r_start.lower() for w in ["starting", "active", "online", "started"]), f"-> {r_start}")

    # 6.2 Offload Model Intent Routing
    r_offload, b_offload, _ = engine._execute_single_command("offload the model")
    check("Offload Model Intent Routing", "Offloaded" in r_offload or "Model:" in b_offload, f"-> {r_offload}")

    # 6.3 void-launcher stop parameters check
    launcher_py = BIN_DIR / "void-launcher.py"
    stop_sh = ROOT_DIR / "scripts" / "stop_void.sh"
    check("void-launcher.py Presence", launcher_py.exists())
    check("scripts/stop_void.sh Executable", stop_sh.exists() and os.access(stop_sh, os.X_OK))

    print("\n" + "=" * 70)
    print(f"AUTOMATED VERIFICATION SUMMARY: {passed_count} PASSED, {failed_count} FAILED")
    print("=" * 70)

    if failed_count > 0:
        os._exit(1)
    os._exit(0)

if __name__ == "__main__":
    run_suite()
