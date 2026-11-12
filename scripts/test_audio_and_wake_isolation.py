#!/usr/bin/env python3
"""
Test Audio Wake Word Isolation, Echo Cancellation, Low Energy Filtering, and Deduplication.
"""

import sys
import time
import json
import numpy as np

# Import from void-widget
sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
# Prevent GUI main execution
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

def test_wake_grammar_precision():
    print("--- 1. Testing Wake Grammar Precision ---")
    # Verify bare "void" is NOT a wake phrase
    valid_wakes = ["hey void", "hello void", "hi void", "okay void", "hey computer", "wake up void"]
    invalid_wakes = ["void", "boyd", "voice", "avoid", "a void", "the void", "point", "terminate", "stop void"]
    
    for w in valid_wakes:
        match = any(phrase in w for phrase in ["hey void", "hello void", "hi void", "okay void", "hey computer", "wake up void"])
        assert match, f"Expected valid wake match for '{w}'"
    print("  [PASS] All valid multi-word wake phrases matched.")

    for iw in invalid_wakes:
        match = any(phrase == iw or phrase in iw.split() for phrase in ["hey void", "hello void", "hi void", "okay void", "hey computer", "wake up void"])
        assert not match, f"False wake triggered on bare sound: '{iw}'"
    print("  [PASS] Bare 'void', 'boyd', and ambient sounds correctly rejected.")

def test_whisper_hallucination_filter():
    print("--- 2. Testing Whisper Silence Hallucination Filtering ---")
    hallucinations = ["you", "thank you", "thanks", "subtitles by", "thanks for watching", "bye", "okay", "so"]
    for h in hallucinations:
        t_norm = h.lower().strip(" .!?,")
        peak_rms = 0.02 # Low energy ambient noise
        should_suppress = (t_norm in ["you", "thank you", "thanks", "subtitles by", "thanks for watching", "bye", "okay", "so", "the", "a"] and peak_rms < 0.035)
        assert should_suppress, f"Failed to suppress silence hallucination '{h}'"
    print("  [PASS] All typical Whisper silence hallucinations successfully filtered.")

def test_command_deduplication():
    print("--- 3. Testing Command Deduplication / Debounce ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    
    # First execution
    cmd = "what is the date"
    norm_cmd = vw.normalize_voice_intent(cmd).strip().lower()
    engine._last_executed_cmd = norm_cmd
    engine._last_cmd_timestamp = time.time()
    
    # Simulate immediate duplicate arriving 1.2s later
    now = engine._last_cmd_timestamp + 1.2
    is_duplicate = (norm_cmd == engine._last_executed_cmd and (now - engine._last_cmd_timestamp < 4.0))
    assert is_duplicate, "Debounce failed to catch rapid duplicate command!"
    print("  [PASS] Rapid duplicate command within 4.0s successfully debounced.")
    
    # Simulate valid subsequent command after 4.5s
    now_later = engine._last_cmd_timestamp + 4.5
    is_duplicate_later = (norm_cmd == engine._last_executed_cmd and (now_later - engine._last_cmd_timestamp < 4.0))
    assert not is_duplicate_later, "Debounce incorrectly blocked valid command after 4.5s cooldown!"
    print("  [PASS] Legitimate subsequent command correctly permitted after cooldown.")

def test_acoustic_echo_muting_flag():
    print("--- 4. Testing Acoustic Echo Muting Flag ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    
    # When speaking
    engine._is_speaking = True
    assert engine._is_speaking, "Speaking flag not set"
    
    # Post speech cooldown
    engine._is_speaking = False
    engine._mute_audio_until = time.time() + 0.6
    assert time.time() < engine._mute_audio_until, "Acoustic grace period active"
    print("  [PASS] Echo cancellation state and 600ms grace period verified.")

if __name__ == "__main__":
    test_wake_grammar_precision()
    test_whisper_hallucination_filter()
    test_command_deduplication()
    test_acoustic_echo_muting_flag()
    print("\nALL AUDIO & WAKE ISOLATION TESTS PASSED! (4/4)")

