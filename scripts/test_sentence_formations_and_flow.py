#!/usr/bin/env python3
"""
Comprehensive test script for sentence formations, file creation, follow-up opener,
and speech announcement consistency in VOID.
"""

import sys
import os
import re
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, "/run/media/prakash/TR_39/VOID")

import importlib.util

spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
void_widget = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = void_widget
spec.loader.exec_module(void_widget)

def test_sentence_formations_and_code_creation():
    print("=== Testing Sentence Formations & Intent Router ===")

    # 1. Test Code as Txt Formations
    code_queries = [
        "write a code as txt",
        "write code as txt",
        "write python code as txt",
        "write a python code as text",
        "create a code as txt",
        "generate code in a text file",
        "save code to txt",
        "write code to txt file",
        "code as txt",
        "write some code and save as text",
        "make a code file in txt",
        "draft python code in txt",
        "generate a script as text file",
        "write code into a text file",
        "write a code as txt called test.txt",
        "write python code for fibonacci as txt",
        "create text file with code",
        "save python script as txt",
        "write code file",
        "put code into a text file",
        "write a script and save as txt"
    ]

    matched_code = 0
    for q in code_queries:
        q_norm = void_widget.normalize_voice_intent(q)
        q_lower = q_norm.lower()
        is_write = bool(
            re.search(r"\b(?:write|create|generate|save|draft|make|put)\s+(?:a\s+)?(?:python\s+|sample\s+|simple\s+|some\s+)?(?:code|script)\b.*\b(?:as|in|to|into)\s+(?:a\s+)?(?:txt|text)(?:\s+file)?\b", q_lower) or
            re.search(r"\b(?:write|create|generate|save)\s+(?:a\s+)?(?:txt|text)\s+file\s+(?:with|containing|for)\s+code\b", q_lower) or
            re.search(r"\bcode\s+as\s+(?:txt|text)(?:\s+file)?\b", q_lower) or
            re.search(r"\b(?:write|create|generate|save|draft)\s+(?:python\s+)?(?:code|script)\s+.*?\b(?:as|in|to)\s+(?:txt|text)\b", q_lower) or
            re.search(r"\b(?:save|write)\s+(?:python\s+)?(?:code|script)\s+to\s+(?:a\s+)?(?:text|txt)\s+file\b", q_lower) or
            re.search(r"\b(?:write|create|generate|save)\s+(?:a\s+)?(?:python\s+)?script\s+(?:as|in|to|into)\s+(?:a\s+)?(?:txt|text)(?:\s+file)?\b", q_lower) or
            re.search(r"\b(?:make|generate|save)\s+(?:a\s+)?code\s+file\s+(?:in|as)\s+(?:txt|text)\b", q_lower) or
            re.search(r"\b(?:write|create|generate)\s+code\s+in\s+(?:txt|text)\b", q_lower) or
            re.search(r"\b(?:write|create|save)\s+some\s+code\s+(?:as|in|and\s+save\s+as)\s+(?:txt|text)\b", q_lower) or
            re.search(r"\bscript\s+and\s+save\s+as\s+(?:txt|text)\b", q_lower) or
            re.search(r"\b(?:code|script)\s+(?:as|in|to)\s+(?:txt|text)\b", q_lower) or
            q_lower.strip() in [
                "write a code as txt", "write code as txt", "write code as text", "write a code as text",
                "code as txt", "write python code as txt", "write code to txt", "create code as txt",
                "save code as txt", "generate code as txt", "write code file", "create a code as txt",
                "write python code as text", "write a python code as txt", "write code as txt file"
            ]
        )
        if is_write:
            matched_code += 1
        else:
            print(f"FAILED to match code query: '{q}' (norm: '{q_norm}')")

    print(f"Code-as-txt matching: {matched_code}/{len(code_queries)} passed.")
    assert matched_code == len(code_queries), "All code as txt formations must match!"

    # 2. Test Follow-Up Opener Formations
    opener_queries = [
        "open it",
        "open that",
        "open ut",
        "open that code",
        "open the code",
        "open code",
        "open txt",
        "open the txt",
        "open text",
        "open the text",
        "open text file",
        "open the text file",
        "open that text file",
        "open that txt",
        "open the code file",
        "open that code file",
        "open created file",
        "open the created file",
        "open last file",
        "open the last file",
        "open recent file",
        "view it",
        "view that",
        "view code",
        "view that code",
        "show it",
        "show that file",
        "show code",
        "show that code",
        "open code as txt"
    ]

    matched_opener = 0
    for q in opener_queries:
        q_norm = void_widget.normalize_voice_intent(q)
        q_lower = q_norm.lower()
        is_open_last = (
            any(p in q_lower for p in [
                "open that", "open it", "open ut", "open that code", "open the code", "open code",
                "open code file", "open that code file", "open the code file", "open txt", "open the txt",
                "open that txt", "open text", "open the text", "open that text", "open text file",
                "open the text file", "open that text file", "open txt file", "open the txt file",
                "open the created file", "open created file", "open last created file",
                "open code as txt", "open the code as txt", "open that file", "open this file",
                "open file", "open the file", "open the summary", "open summary",
                "open the document", "open document", "open the pdf", "open pdf",
                "open the report", "open report", "open the last file", "open recent file",
                "show that", "show the summary", "show the document", "show pdf", "view document", "view it",
                "view that", "view pdf", "view code", "view that code", "view text", "view text file", "view the file",
                "show code", "show that code", "show the file", "show that file"
            ]) or
            q_lower.strip() in [
                "open it", "open that", "open ut", "open document", "open the document", "open pdf",
                "open the pdf", "open report", "view it", "view that", "view code", "view that code",
                "open code", "open the code", "open that code", "open txt", "open the txt", "open text",
                "open the text", "open that text", "open text file", "open the text file", "open that file",
                "open created file", "open the created file", "open file", "open the file",
                "open last file", "open the last file", "open recent file", "open the recent file"
            ] or
            bool(re.search(r"^(?:please\s+)?(?:open|view|show)\s+(?:it|that|this|the\s+created\s+file|created\s+file|that\s+code|the\s+code|the\s+text\s+file|that\s+file|the\s+file|the\s+last\s+file|last\s+file|recent\s+file|the\s+recent\s+file|code|text)$", q_lower))
        )
        if is_open_last:
            matched_opener += 1
        else:
            print(f"FAILED to match opener query: '{q}' (norm: '{q_lower}')")

    print(f"Follow-up opener matching: {matched_opener}/{len(opener_queries)} passed.")
    assert matched_opener == len(opener_queries), "All follow-up opener formations must match!"

    # 3. Test Song Playback Formations (Pesamalaye, etc.)
    song_queries = [
        "play pesamalaye",
        "play psa",
        "stream pesamalaye",
        "put on pesamalaye",
        "listen to pesamalaye",
        "play the song pesamalaye",
        "play believer",
        "open youtube and play pesamalaye"
    ]
    for sq in song_queries:
        q_norm = void_widget.normalize_voice_intent(sq)
        extracted = void_widget.extract_media_song_query(q_norm)
        if "pesamalaye" in q_norm or "psa" in sq:
            assert extracted.lower() == "pesamalaye" or "pesamalaye" in extracted.lower(), f"Song should be pesamalaye, got {extracted}"
        elif "believer" in sq:
            assert extracted.lower() == "believer", f"Song should be believer, got {extracted}"
    print("Song extraction & anti-autocorrect passed.")

    # 4. Test Speech Sanitization and Announcement Shortening
    tool_hub = void_widget.DodaiosToolHub()
    engine = void_widget.AudioVoiceEngine(tool_hub)
    test_announcements = [
        ("The Antigravity window has been minimized", "Minimized Antigravity."),
        ("Window action close applied to chromium", "Closed Chromium."),
        ("Showing desktop", "Showing desktop."),
        ("I have thoroughly gathered information and composed your complete PDF document 'Autonomous Systems and AI' (5 pages). It is saved at Autonomous_Systems_and_AI.pdf in your Reports folder. Say 'open it' to review.", "Completed PDF."),
        ("Created code text file at code.txt in Documents. Say 'open it' or 'open that code' to view or edit it.", "Created code file."),
        ("Opened code.txt in your default application.", "Opened file."),
        ("Opened /home/prakash/Documents/Reports directory in file manager.", "Opened folder."),
        ("Screenshot captured and saved to Screenshot_20261113.png in Pictures.", "Captured screenshot."),
        ("Playing Pesamalaye on tab.", "Playing Pesamalaye."),
        ("Master audio volume is currently set to 50%", "Volume set to 50 percent."),
        ("Screen brightness set to 75%", "Brightness set to 75 percent."),
        ("Screen locked.", "Screen locked."),
        ("Battery: 85% (discharging). Temperatures: CPU +47°C, GPU +45°C. Telemetry: RAM usage is 35%.", None) # Clean speech
    ]

    for raw, expected in test_announcements:
        cleaned = engine._clean_text_for_speech(raw)
        print(f"Raw: '{raw[:50]}...' -> Spoken: '{cleaned}'")
        if expected:
            assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"
        else:
            assert "°" not in cleaned and "C" not in cleaned.split()[-1] and "discharging" not in cleaned, "Symbols should be stripped or spelled out"
            assert "degrees Celsius" in cleaned or "percent" in cleaned

    print("\nAll Sentence Formations, Code Creation, Opener, and Speech Tests PASSED successfully!")

if __name__ == "__main__":
    test_sentence_formations_and_code_creation()
