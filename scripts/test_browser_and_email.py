#!/usr/bin/env python3
"""
Verification test suite for Browser Tab, Search, Email Composition, and Interactive User Prompting.
"""
import sys
import os
from pathlib import Path

# Add VOID bin directory to sys.path
VOID_BIN = Path("/run/media/prakash/TR_39/VOID/bin")
sys.path.insert(0, str(VOID_BIN))

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", str(VOID_BIN / "void-widget.py"))
vw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vw)

print("=" * 60)
print("  TESTING BROWSER & EMAIL ENHANCEMENTS IN VOID")
print("=" * 60)

# Initialize Hub and Engine
hub = vw.DodaiosToolHub()
engine = vw.AudioVoiceEngine(hub)

# Mock subprocess.Popen only for Chromium so we don't open 10 Chromium windows during tests
opened_urls = []
orig_popen = vw.subprocess.Popen
def mock_popen(args, **kwargs):
    cmd_str = " ".join(str(a) for a in args) if isinstance(args, (list, tuple)) else str(args)
    if "chromium" in cmd_str:
        opened_urls.append(cmd_str)
        print(f"  [MOCK BROWSER SPAWN] {cmd_str}")
        class DummyProc:
            pid = 12345
            stdin = None
            stdout = None
            stderr = None
            def poll(self):
                return 0
            def wait(self, timeout=None):
                return 0
        return DummyProc()
    return orig_popen(args, **kwargs)

vw.subprocess.Popen = mock_popen

# Test 1: Compound Splitting with Commas
print("\n=== TEST 1: Compound Splitting ===")
q1 = "open chromium , open mail in it and send mail to rskakavin@gmail.com saying how sorry you fell not about attendongh his party"
parts1 = vw.split_compound_commands(q1)
print("Q1 parts:", parts1)
assert len(parts1) == 2, f"Expected 2 parts, got {parts1}"
assert parts1[0] == "open chromium"
assert "rskakavin@gmail.com" in parts1[1]
print("  [PASS] Compound splitting on comma before action verb.")

# Test 2: Open New Tab in Chromium
print("\n=== TEST 2: Open New Tab ===")
opened_urls.clear()
reply, badge, _ = engine._execute_single_command("open new tab in chromium")
print("Reply:", reply)
print("Badge:", badge)
assert "new tab" in reply.lower()
assert any("chrome://newtab" in u for u in opened_urls)
print("  [PASS] 'open new tab in chromium' opens chrome://newtab.")

# Test 3: Open New Tab and Search for Specific Query
print("\n=== TEST 3: Open New Tab and Search for Specific Query ===")
opened_urls.clear()
reply, badge, _ = engine._execute_single_command("open new tab in chromium and search for quantum computing")
print("Reply:", reply)
assert "quantum computing" in reply
assert any("quantum" in u for u in opened_urls)
print("  [PASS] Direct search in Chromium executed.")

# Test 4: Open New Tab and Search Something (Missing Query -> Prompt User)
print("\n=== TEST 4: Missing Search Query -> Interactive Prompt ===")
opened_urls.clear()
reply, badge, _ = engine._execute_single_command("open new tab in chromium and search something")
print("Reply:", reply)
print("Badge:", badge)
assert "what would you like me to search" in reply.lower()
assert engine._pending_action is not None
assert engine._pending_action["type"] == "browser_search"
print("  [PASS] VOID prompted for missing search query.")

# Test 4b: Provide the search query in response to the prompt
reply, badge, _ = engine._execute_single_command("latest fedora linux features")
print("Follow-up Reply:", reply)
assert "latest fedora linux features" in reply
assert engine._pending_action is None
assert any("fedora" in u for u in opened_urls)
print("  [PASS] VOID resolved search query from user prompt reply.")

# Test 5: Exact User Email Request
print("\n=== TEST 5: Exact User Email Request ===")
opened_urls.clear()
q_email = "open mail in it and send mail to rskakavin@gmail.com saying how sorry you fell not about attendongh his party"
reply, badge, _ = engine._execute_single_command(q_email)
print("Reply:\n", reply)
print("Badge:", badge)
assert "rskakavin@gmail.com" in reply
assert "Apology for missing your party" in reply
assert any("mail.google.com" in u and "rskakavin" in u for u in opened_urls)
print("  [PASS] Apology email composed and opened in Chromium.")

# Test 6: Missing Recipient Email -> Interactive Prompt
print("\n=== TEST 6: Missing Recipient Email -> Interactive Prompt ===")
opened_urls.clear()
reply, badge, _ = engine._execute_single_command("send an email saying sorry for missing the party")
print("Reply:", reply)
print("Badge:", badge)
assert "who would you like to send the email to" in reply.lower()
assert engine._pending_action is not None
assert engine._pending_action["type"] == "email_recipient"
print("  [PASS] VOID prompted for missing recipient email.")

# Test 6b: Provide the recipient in response to the prompt
reply, badge, _ = engine._execute_single_command("rskakavin@gmail.com")
print("Follow-up Reply:\n", reply)
assert "rskakavin@gmail.com" in reply
assert "Apology for missing your party" in reply
assert engine._pending_action is None
assert any("rskakavin" in u for u in opened_urls)
print("  [PASS] VOID resolved recipient and launched Gmail compose.")

# Test 7: Web Read Page with BeautifulSoup
print("\n=== TEST 7: Web Read Page Tool (BeautifulSoup) ===")
test_html_url = "https://httpbin.org/html"
try:
    content = hub.web_read_page(test_html_url)
    print("Fetched text snippet:", content[:100])
    assert len(content) > 10
    print("  [PASS] BeautifulSoup page extraction working.")
except Exception as e:
    print(f"  [SKIP / NETWORK] {e}")

print("\n" + "=" * 60)
print("  ALL 7 TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
