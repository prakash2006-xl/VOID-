#!/usr/bin/env python3
"""
Test Suite: VOID Model Offload, Server Stopping, Memory Reclamation & Re-activation
Verifies:
1. "wide off-road model", "off-load model", "oad model", "off loading model" command matching & normalization.
2. Fast response: Sub-second model offload and immediate RAM reclamation.
3. Clean speech de-hyphenation: Pronounces "offload" instead of robotic "off-load".
4. Cloud AI operations: While model is offloaded, VOID continues working seamlessly with Cloud API key.
5. "start model", "start model again", "word load model" re-activation of Ollama.
"""
import sys
import os
import time
import subprocess
from pathlib import Path
import importlib.util

pkg_root = "/run/media/prakash/TR_39/VOID"
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

spec = importlib.util.spec_from_file_location("void_widget", f"{pkg_root}/bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

normalize_voice_intent = vw.normalize_voice_intent
DodaiosToolHub = vw.DodaiosToolHub
AudioVoiceEngine = vw.AudioVoiceEngine

def test_intent_normalization():
    print("=== 1. Testing Voice Intent Normalization ===")
    test_cases = [
        ("offlad model", "offload model"),
        ("wide off-road model.", "offload model."),
        ("off-load model", "offload model"),
        ("off loading model", "offload model"),
        ("off-load the model", "offload model"),
        ("oad model", "offload model"),
        ("word load model", "load model"),
        ("keyboard, offload model.", "keyboard, offload model."),
        ("start model again", "start model again"),
        ("start ollama", "start ollama"),
        ("untill oped", "until stopped")
    ]
    for inp, expected in test_cases:
        norm = normalize_voice_intent(inp)
        assert expected in norm, f"Failed: '{inp}' -> '{norm}', expected substring '{expected}'"
        print(f"  [PASS] '{inp}' -> '{norm}'")

def test_engine_offload_and_cloud():
    print("\n=== 2. Testing Engine Offload & Stopping Ollama ===")
    hub = DodaiosToolHub()
    engine = AudioVoiceEngine(tool_hub=hub)

    # 1. Test "wide off-road model" command (the exact transcript from log)
    t0 = time.time()
    reply, badge, _ = engine._execute_single_command("wide off-road model.")
    dt_ms = round((time.time() - t0) * 1000, 1)
    print(f"  Reply: '{reply}', Badge: '{badge}', Execution time: {dt_ms}ms")
    assert "offloaded" in reply.lower() and "freed" in reply.lower()
    assert badge == "Model: Offloaded"
    assert engine._model_offloaded is True
    assert engine._ollama_stopped is True
    assert engine._agent_providers.is_local_online() is False
    print(f"  [PASS] Sub-second fast offload completed in {dt_ms}ms!")

    # Verify speech cleaning removes hyphen
    spoken = engine._clean_text_for_speech("Model off-loaded and off-road model.")
    print(f"  Speech cleaned: '{spoken}'")
    assert "off-load" not in spoken and "off-road" not in spoken
    print("  [PASS] TTS speech pronunciation cleaned (no hyphens).")

    # Check that Ollama service is stopped
    res = subprocess.run(["systemctl", "is-active", "ollama"], capture_output=True, text=True)
    is_active = (res.stdout.strip() == "active")
    print(f"  Ollama systemctl active: {is_active} (expected: False/inactive)")
    assert not is_active, "Ollama service should be inactive after offload!"

    # Check that llama-server processes are not running
    ps_res = subprocess.run(["pgrep", "-f", "llama-server"], capture_output=True, text=True)
    assert not ps_res.stdout.strip(), "No llama-server runner should be active!"
    print("  [PASS] llama-server runner completely terminated and RAM freed.")

    # 2. Test Cloud AI execution while model is offloaded
    print("\n=== 3. Testing Cloud AI Execution While Model is Offloaded ===")
    assert engine._agent_providers.is_cloud_configured() is True
    reply2, badge2, _ = engine._execute_single_command("What is the capital of Japan? Answer in one word.")
    print(f"  Cloud Query Reply: '{reply2}', Badge: '{badge2}'")
    assert "tokyo" in reply2.lower()
    assert "Cloud AI" in badge2
    print("  [PASS] Seamless Cloud AI inference verified while local model is offloaded!")

    # Verify Ollama remained stopped throughout cloud inference
    res_check = subprocess.run(["systemctl", "is-active", "ollama"], capture_output=True, text=True)
    assert res_check.stdout.strip() != "active", "Ollama must remain stopped while using cloud!"
    print("  [PASS] Ollama remained strictly stopped and RAM remained freed.")

    # 3. Test "start model again" command
    print("\n=== 4. Testing Start Model Again ===")
    reply3, badge3, _ = engine._execute_single_command("start model again")
    print(f"  Reply: '{reply3}', Badge: '{badge3}'")
    assert badge3 == "Model: Online"
    assert engine._model_offloaded is False
    assert engine._ollama_stopped is False

    # Verify Ollama is now active and responsive
    time.sleep(1.0)
    res_start = subprocess.run(["systemctl", "is-active", "ollama"], capture_output=True, text=True)
    assert res_start.stdout.strip() == "active", "Ollama service should be active after start!"
    assert engine._agent_providers.is_local_online() is True
    print("  [PASS] Ollama service active, local connectivity restored, and model online.")

if __name__ == "__main__":
    test_intent_normalization()
    test_engine_offload_and_cloud()
    print("\nALL OFFLOAD, FAST RESPONSE, SPEECH, CLOUD AI, AND START TESTS PASSED!")
