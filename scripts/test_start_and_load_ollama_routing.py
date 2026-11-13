#!/usr/bin/env python3
"""
Test Suite: VOID Ollama & Model Lifecycle Routing Verification
Validates that:
1. "start ollama", "load model", and all alternative phrasing correctly routes to start/load Ollama.
2. "load model" NEVER triggers the "stop ollama" / offload prompt or routes to offload.
3. Mutual exclusivity between start/load and stop/offload commands.
4. Robust Vosk STT normalization for voice commands.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

pkg_root = "/run/media/prakash/TR_39/VOID"
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", f"{pkg_root}/bin/void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

normalize_voice_intent = vw.normalize_voice_intent
DodaiosToolHub = vw.DodaiosToolHub
AudioVoiceEngine = vw.AudioVoiceEngine

class TestModelLifecycleRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = DodaiosToolHub()
        cls.engine = AudioVoiceEngine(tool_hub=cls.hub)
        # Mock internal hardware/systemctl methods so we test pure routing and fast-path dispatch without hanging
        cls.engine._start_and_load_ollama = MagicMock(return_value=(True, "Online"))
        cls.engine._offload_and_stop_ollama = MagicMock(return_value=["lfm3-omni:2b"])

    def setUp(self):
        self.engine._start_and_load_ollama.reset_mock()
        self.engine._offload_and_stop_ollama.reset_mock()

    def test_start_and_load_phrases(self):
        """Verify that all alternative phrasings for starting/loading Ollama trigger _start_and_load_ollama."""
        start_phrases = [
            # Direct commands
            "start ollama",
            "start ollama again",
            "start the ollama",
            "start the ollama server",
            "start ollama server",
            "run ollama",
            "run ollama server",
            "turn on ollama",
            "turn on the ollama",
            "launch ollama",
            "boot ollama",
            "load ollama",
            "load the ollama",
            "load ollama server",
            "load model",
            "load the model",
            "load models",
            "load the models",
            "start model",
            "start the model",
            "start model again",
            "start the model again",
            "start local model",
            "reload model",
            "reload ollama",
            "resume model",
            "resume ollama",
            "turn on model",
            "turn on the model",
            "activate model",
            "activate ollama",
            "boot model",
            "start brain",
            "load brain",
            "wake model",
            "wake brain",
            "reconnect model",
            "reconnect ollama",
            "enable model",
            "enable ollama",
            "word load model",
            "bring model back",
            "bring back model",
            "bring model online",
            "put model online",
            # With wake word prefixes
            "hey void start ollama",
            "void start ollama",
            "hey void load model",
            "void load model",
            "hey void start model again",
            "void reload model"
        ]

        for phrase in start_phrases:
            self.setUp()
            reply, badge, _ = self.engine._execute_single_command(phrase)
            self.assertEqual(badge, "Model: Online", f"Failed for '{phrase}': badge was '{badge}', reply was '{reply}'")
            self.assertTrue(self.engine._start_and_load_ollama.called, f"_start_and_load_ollama NOT called for '{phrase}'")
            self.assertFalse(self.engine._offload_and_stop_ollama.called, f"_offload_and_stop_ollama was FALSELY called for '{phrase}'")
            print(f"  [PASS] Start/Load routing: '{phrase}' -> Badge: '{badge}'")

    def test_offload_and_stop_phrases(self):
        """Verify that all alternative phrasings for stopping/offloading Ollama trigger _offload_and_stop_ollama."""
        offload_phrases = [
            "offload model",
            "off-load model",
            "off load model",
            "offload the model",
            "off-load the model",
            "off load the model",
            "offloading model",
            "off-loading model",
            "off loading model",
            "offload all models",
            "unload model",
            "unload the model",
            "unload all models",
            "stop model",
            "stop the model",
            "stop models",
            "stop ollama",
            "stop the ollama",
            "stop ollama server",
            "kill ollama",
            "shut down ollama",
            "shutdown ollama",
            "turn off ollama",
            "turn off model",
            "turn off the model",
            "deactivate model",
            "deactivate ollama",
            "free ram",
            "free memory",
            "free vram",
            "free system memory",
            "clear ram",
            "release memory",
            "stop offload model",
            "stop and offload model",
            "offload brain",
            "unload brain",
            "stop local model",
            "offload local model",
            "take model offline",
            "off-road model",
            "off road model",
            "offlad model",
            "oad model",
            # With wake word
            "hey void offload model",
            "void stop ollama",
            "hey void free ram"
        ]

        for phrase in offload_phrases:
            self.setUp()
            reply, badge, _ = self.engine._execute_single_command(phrase)
            self.assertEqual(badge, "Model: Offloaded", f"Failed for '{phrase}': badge was '{badge}', reply was '{reply}'")
            self.assertTrue(self.engine._offload_and_stop_ollama.called, f"_offload_and_stop_ollama NOT called for '{phrase}'")
            self.assertFalse(self.engine._start_and_load_ollama.called, f"_start_and_load_ollama was FALSELY called for '{phrase}'")
            print(f"  [PASS] Offload/Stop routing: '{phrase}' -> Badge: '{badge}'")

    def test_critical_edge_case_load_model_not_triggering_offload(self):
        """CRITICAL: Specific regression test verifying 'load model' NEVER triggers 'stop ollama'."""
        self.setUp()
        reply, badge, _ = self.engine._execute_single_command("load model")
        self.assertEqual(badge, "Model: Online")
        self.assertIn("started", reply.lower())
        self.assertNotIn("stopped", reply.lower())
        self.assertNotIn("offload", reply.lower())
        self.assertEqual(self.engine._offload_and_stop_ollama.call_count, 0)
        self.assertEqual(self.engine._start_and_load_ollama.call_count, 1)

if __name__ == "__main__":
    print("=== RUNNING VOID MODEL LIFECYCLE ROUTING TESTS ===")
    unittest.main()
