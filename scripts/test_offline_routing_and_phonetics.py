#!/usr/bin/env python3
"""
Test Offline Command Routing, Phonetic Normalization, and Local File Management.
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

def test_phonetic_normalization():
    print("--- 1. Testing Phonetic STT Normalization ---")
    test_cases = [
        ("strt ollama in speach to text", "start ollama in speech to text"),
        ("strt olama and spech to txt", "start ollama and speech to text"),
        ("strat o llama and stt", "start ollama and speech to text"),
        ("opn crome and search something", "open chromium and search something"),
        ("watsapp web", "whatsapp web"),
        ("screnshot save it as my_shot", "screenshot save it as my_shot")
    ]
    for inp, expected in test_cases:
        res = vw.normalize_voice_intent(inp)
        assert res == expected, f"Normalization mismatch: '{inp}' -> '{res}', expected '{expected}'"
        print(f"  [PASS] '{inp}' -> '{res}'")

def test_offline_ollama_stt_routing():
    print("--- 2. Testing Offline Ollama & STT Intent Routing ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    
    reply, badge, thumb = engine._execute_single_command("strt ollama in speach to text")
    assert "Ollama AI brain is initializing" in reply or "Ollama" in reply, f"Unexpected reply: {reply}"
    assert "Active" in badge, f"Unexpected badge: {badge}"
    print(f"  [PASS] 'strt ollama in speach to text' routed -> Reply: '{reply}', Badge: '{badge}'")

def test_offline_file_operations():
    print("--- 3. Testing Offline Local File Management ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    
    test_fname = "void_offline_unit_test.txt"
    test_content = "Autonomous offline intelligence verified."
    
    # Create file
    c_cmd = f"create file {test_fname} with content {test_content}"
    reply, badge, thumb = engine._execute_single_command(c_cmd)
    assert f"File '{test_fname}' created successfully" in reply, f"Create failed: {reply}"
    print(f"  [PASS] Create file -> {reply}")
    
    # Read file
    r_cmd = f"read file {test_fname}"
    reply_r, badge_r, thumb_r = engine._execute_single_command(r_cmd)
    assert test_content in reply_r, f"Read failed: {reply_r}"
    print(f"  [PASS] Read file -> {reply_r}")
    
    # Clean up test file
    test_path = Path("/home/prakash/Documents") / test_fname
    if test_path.exists():
        test_path.unlink()
        print(f"  [PASS] Cleaned up temporary test file: {test_path}")

def test_offline_capabilities_and_ip():
    print("--- 4. Testing Offline Capabilities & Network Status ---")
    hub = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(hub)
    
    reply_cap, badge_cap, _ = engine._execute_single_command("what can you do offline")
    assert "launch applications" in reply_cap and "draft Word" in reply_cap, f"Capabilities failed: {reply_cap}"
    print(f"  [PASS] Offline capabilities query verified -> {badge_cap}")
    
    reply_ip, badge_ip, _ = engine._execute_single_command("what is my ip")
    assert "IP" in reply_ip or "address" in reply_ip, f"IP lookup failed: {reply_ip}"
    print(f"  [PASS] IP lookup verified -> {reply_ip}")

if __name__ == "__main__":
    test_phonetic_normalization()
    test_offline_ollama_stt_routing()
    test_offline_file_operations()
    test_offline_capabilities_and_ip()
    print("\nALL OFFLINE ROUTING & PHONETIC TESTS PASSED! (4/4)")

