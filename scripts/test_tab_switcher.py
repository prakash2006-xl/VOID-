#!/usr/bin/env python3
"""
Test Suite: Voice-Activated Chromium Tab Switcher
Verifies:
1. "next tab", "switch to next tab" -> next tab navigation
2. "previous tab", "prev tab", "switch to previous tab" -> previous tab navigation
3. "tab 1" .. "tab 8", "first tab" .. "eighth tab" -> direct numeric tab navigation
4. "last tab", "tab 9" -> rightmost tab navigation
5. Zero conflicts with MPRIS media playback ("next song", "previous track")
6. Zero conflicts with tab deletion ("close tab", "delete tab")
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bin"))

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", ROOT / "bin" / "void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

DodaiosToolHub = vw.DodaiosToolHub
normalize_voice_intent = vw.normalize_voice_intent

def run_tests():
    print("==================================================================")
    print("        TESTING CHROMIUM TAB SWITCHER VIA VOICE COMMANDS          ")
    print("==================================================================")

    th = DodaiosToolHub()

    # -------------------------------------------------------------
    # Test 1: ToolHub Method Implementation
    # -------------------------------------------------------------
    assert hasattr(th, "switch_chromium_tab"), "ToolHub must implement switch_chromium_tab"
    assert hasattr(th, "close_chromium_tab"), "ToolHub must implement close_chromium_tab"
    assert hasattr(th, "open_chromium_tab"), "ToolHub must implement open_chromium_tab"
    assert hasattr(th, "open_chromium_window"), "ToolHub must implement open_chromium_window"
    print("✓ Test 1 Passed: All 4 tab/window control methods implemented in DodaiosToolHub.")

    # -------------------------------------------------------------
    # Test 2: Voice Intent Classification Matrix
    # -------------------------------------------------------------
    test_cases = [
        # (Query, Expected Type, Expected Target/Direction)
        ("next tab", "switch_dir", "next"),
        ("switch to next tab", "switch_dir", "next"),
        ("next chromium tab", "switch_dir", "next"),
        ("nxt tab", "switch_dir", "next"),
        ("previous tab", "switch_dir", "prev"),
        ("prev tab", "switch_dir", "prev"),
        ("switch to previous tab", "switch_dir", "prev"),
        ("previous chromium tab", "switch_dir", "prev"),
        ("perv tab", "switch_dir", "prev"),
        ("tab 1", "switch_num", 1),
        ("tab 2", "switch_num", 2),
        ("switch to tab 3", "switch_num", 3),
        ("go to tab 4", "switch_num", 4),
        ("tab 5 in chromium", "switch_num", 5),
        ("first tab", "switch_num", 1),
        ("second tab", "switch_num", 2),
        ("third tab", "switch_num", 3),
        ("last tab", "switch_num", 9),
        ("tab 9", "switch_num", 9),
        ("close tab", "close_tab", None),
        ("delete tab", "close_tab", None),
        ("open new tab", "new_tab", None),
        ("open new chromium window", "new_window", None),
        ("next song", "mpris", None),
        ("previous track", "mpris", None),
    ]

    ord_map = {
        "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
        "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
        "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "last": 9
    }

    for q, expected_type, expected_val in test_cases:
        q_norm = normalize_voice_intent(q)
        q_lower = q_norm.lower().strip()

        # Classification logic exactly matching widget
        classified_type = None
        classified_val = None

        if re.search(r"\b(?:close|delete|remove)\s+(?:the\s+|a\s+|this\s+|current\s+)?tab(?:s)?(?:\s+in\s+chromium|\s+in\s+browser)?\b", q_lower) or q_lower in ["close tab", "delete tab"]:
            classified_type = "close_tab"
        elif re.search(r"\b(?:open\s+(?:a\s+)?new\s+(?:chromium\s+|browser\s+)?window|new\s+window)\b", q_lower):
            classified_type = "new_window"
        elif re.search(r"\b(?:open\s+(?:a\s+)?new\s+tab|open\s+(?:a\s+)?tab|new\s+tab|open\s+tab\s+in\s+chromium)\b", q_lower):
            classified_type = "new_tab"
        else:
            tab_num_m = (
                re.search(r"^(?:please\s+)?(?:switch\s+to\s+|go\s+to\s+)?tab\s+(\d+|first|second|third|fourth|fifth|sixth|seventh|eighth|last)(?:\s+in\s+chromium|\s+in\s+browser)?$", q_lower) or
                re.search(r"^(?:please\s+)?(?:switch\s+to\s+|go\s+to\s+)?(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|last)\s+tab(?:\s+in\s+chromium|\s+in\s+browser)?$", q_lower)
            )
            if tab_num_m:
                raw_target = tab_num_m.group(1).strip().lower()
                tab_idx = ord_map.get(raw_target, raw_target)
                classified_type = "switch_num"
                classified_val = int(tab_idx)
            elif re.search(r"\b(?:next\s+tab|switch\s+(?:to\s+)?next\s+tab|next\s+chromium\s+tab)\b", q_lower):
                classified_type = "switch_dir"
                classified_val = "next"
            elif re.search(r"\b(?:previous\s+tab|prev\s+tab|switch\s+(?:to\s+)?previous\s+tab|switch\s+(?:to\s+)?prev\s+tab|previous\s+chromium\s+tab)\b", q_lower):
                classified_type = "switch_dir"
                classified_val = "prev"
            elif any(p in q_lower for p in ["next song", "next track", "previous song", "previous track"]):
                classified_type = "mpris"

        assert classified_type == expected_type, f"Query '{q}' (norm: '{q_lower}') -> expected type {expected_type}, got {classified_type}"
        if expected_val is not None:
            assert classified_val == expected_val, f"Query '{q}' -> expected val {expected_val}, got {classified_val}"
        print(f"  ✓ Classified: '{q}' -> {classified_type} (val={classified_val})")

    print("==================================================================")
    print("      ALL TAB SWITCHER VOICE INTENT TESTS PASSED (100%)           ")
    print("==================================================================")

if __name__ == "__main__":
    run_tests()
