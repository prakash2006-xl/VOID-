#!/usr/bin/env python3
"""
Test YouTube Search & Play, Dictation Stop/Cancel, File Memory Traceback,
Quick Chips cleanup, and False 'Open' suppression.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

from PySide6 import QtWidgets

def test_1_youtube_search_and_play():
    print("--- 1. Testing YouTube Search & Direct Play ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    engine._speak_text = lambda text: None

    # 1. Phonetic normalization
    raw_query = "open youtube in chromium and search for beliver snag and play it"
    norm = vw.normalize_voice_intent(raw_query)
    assert "believer" in norm, f"Phonetic typo 'beliver' not fixed: {norm}"
    assert "song" in norm, f"Phonetic typo 'snag' not fixed: {norm}"
    print(f"  [PASS] Typo normalization: '{raw_query}' -> '{norm}'")

    # 2. Command execution
    reply, badge, thumb = engine._execute_single_command(norm)
    assert "YouTube" in badge, f"Badge missing YouTube: {badge}"
    assert "Believer" in reply or "believer" in reply, f"Reply missing believer: {reply}"
    print(f"  [PASS] YouTube search & play routed: Reply: '{reply}', Badge: '{badge}'")

def test_2_dictation_cancellation():
    print("--- 2. Testing Dictation Mode Exit & Cancel Phrases ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    engine._speak_text = lambda text: None

    # Start dictation
    start_reply, _, _ = engine._execute_single_command("start dictation to note TestDictationCancel")
    assert engine._dictation_mode is True, "Dictation mode failed to start"
    print(f"  [PASS] Dictation started: {start_reply}")

    # Process task with "cancel dictate"
    engine._process_task("cancel dictate")
    assert engine._dictation_mode is False, "Dictation mode failed to cancel on 'cancel dictate'"
    print("  [PASS] Dictation cancelled via 'cancel dictate'")

    # Start dictation again and test "stop dictate"
    engine._execute_single_command("start dictation")
    assert engine._dictation_mode is True
    engine._process_task("stop dictate")
    assert engine._dictation_mode is False
    print("  [PASS] Dictation stopped via 'stop dictate'")

def test_3_summary_exact_name_and_traceback():
    print("--- 3. Testing Summary Exact Naming & 'Open That' Memory Traceback ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    engine._speak_text = lambda text: None

    # Create summary with exact custom name
    summary_query = "create me a document which says the summary of a mother's importance in a human life called Mothers_Importance"
    reply, badge, _ = engine._execute_single_command(summary_query)
    assert "Mothers_Importance.docx" in reply, f"Custom filename not used: {reply}"
    assert engine.last_generated_file is not None, "engine.last_generated_file was not tracked"
    target_path = Path(engine.last_generated_file)
    assert target_path.exists(), f"Target file does not exist: {target_path}"
    print(f"  [PASS] Created summary with exact custom name: {target_path.name}")

    # Test "open that"
    open_reply, open_badge, _ = engine._execute_single_command("open that")
    assert "Mothers_Importance.docx" in open_reply, f"'open that' failed to open correct file: {open_reply}"
    assert "Opened:" in open_badge, f"Unexpected badge: {open_badge}"
    print(f"  [PASS] 'open that' successfully traced back and opened: {open_reply}")

    # Test "open the summary that you have just given"
    open_reply2, open_badge2, _ = engine._execute_single_command("open the summary that you have just given")
    assert "Mothers_Importance.docx" in open_reply2, f"Failed on 'open the summary that you have just given': {open_reply2}"
    print(f"  [PASS] 'open the summary that you have just given' successfully opened file.")

def test_4_quick_chips_and_stop_button():
    print("--- 4. Testing Quick Chips & Stop Dictation Button ---")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(["--platform", "offscreen"])
    widget = vw.VoidMiniWidget()
    widget._engine._speak_text = lambda text: None

    # Check quick chips in expanded box
    chip_texts = [btn.text() for btn in widget._expanded_box.findChildren(QtWidgets.QPushButton)]
    assert any("Start Ollama" in t for t in chip_texts), f"Start Ollama missing: {chip_texts}"
    assert any("Open Chrome" in t for t in chip_texts), f"Open Chrome missing: {chip_texts}"
    assert not any("Draft Doc" in t for t in chip_texts), f"Draft Doc should be removed: {chip_texts}"
    assert not any("Draft Excel" in t for t in chip_texts), f"Draft Excel should be removed: {chip_texts}"
    print("  [PASS] Quick chips verified: Start Ollama and Open Chrome present, Draft Doc/Excel removed.")

    # Check Stop Dictation button
    assert hasattr(widget, "_dict_stop_btn"), "_dict_stop_btn not found on widget"
    # When dictation is inactive, button should be hidden
    widget._engine._dictation_mode = False
    widget._on_state_changed("idle")
    assert widget._dict_stop_btn.isHidden() is True, "Dictation stop button should be hidden when idle"

    # When dictation is active, button should be visible
    widget._engine._dictation_mode = True
    widget._on_state_changed("listening")
    assert widget._dict_stop_btn.isHidden() is False, "Dictation stop button should be visible when dictating"
    print("  [PASS] Dedicated Stop Dictation button dynamic visibility confirmed.")

    # Click stop dictation button
    widget._on_stop_dictation_clicked()
    assert widget._engine._dictation_mode is False, "Clicking stop button failed to stop dictation"
    assert widget._dict_stop_btn.isHidden() is True, "Stop button remained visible after click"
    print("  [PASS] Stop Dictation button click cleanly stops dictation mode.")

def test_5_false_open_suppression():
    print("--- 5. Testing False 'Open' Trigger Suppression ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    engine._speak_text = lambda text: None

    # 1. "open that" must NOT open WhatsApp or Gmail
    reply1, badge1, _ = engine._execute_single_command("open that")
    assert "WhatsApp" not in badge1 and "Webmail" not in badge1, f"False trigger on 'open that': {badge1}"
    print(f"  [PASS] 'open that' correctly did not trigger WhatsApp/Gmail (Badge: {badge1})")

    # 2. "what is a mother's importance" must NOT trigger WhatsApp
    norm_w = vw.normalize_voice_intent("what is a mother's importance")
    assert "whatsapp" not in norm_w, f"False normalization to whatsapp: {norm_w}"
    print("  [PASS] 'what is a...' does not falsely trigger WhatsApp")

    # 3. Explicit "open whatsapp web" DOES open WhatsApp
    reply_wa, badge_wa, _ = engine._execute_single_command("open whatsapp web")
    assert "WhatsApp" in badge_wa, f"Explicit WhatsApp failed: {badge_wa}"
    print(f"  [PASS] Explicit 'open whatsapp web' works correctly (Badge: {badge_wa})")

if __name__ == "__main__":
    test_1_youtube_search_and_play()
    test_2_dictation_cancellation()
    test_3_summary_exact_name_and_traceback()
    test_4_quick_chips_and_stop_button()
    test_5_false_open_suppression()
    print("\nALL YOUTUBE, DICTATION & MEMORY FIXES PASSED! (5/5)")
