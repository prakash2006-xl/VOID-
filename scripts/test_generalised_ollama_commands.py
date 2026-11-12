#!/usr/bin/env python3
"""
Unit test suite for Generalized Start/Stop Ollama Commands in VOID Desktop Assistant.
Verifies all natural variations of starting, stopping, restarting, and unloading the brain.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
void_widget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(void_widget)


class TestGeneralisedOllamaCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool_hub = void_widget.DodaiosToolHub()
        cls.engine = void_widget.AudioVoiceEngine(tool_hub=cls.tool_hub)

    def test_01_start_ollama_variations(self):
        print("\n--- 1. Testing Generalized Start Ollama Commands ---")
        start_phrases = [
            "start ollama",
            "open ollama",
            "turn on ollama",
            "turn ollama on",
            "run ollama",
            "launch ollama",
            "activate brain",
            "load brain",
            "wake up the brain",
            "start local ai",
            "ollama on",
            "brain on",
            "load model",
            "start ai brain",
        ]
        with patch.object(void_widget, "start_ollama_service", return_value=(True, "Ollama server started and lfm3-omni:2b brain is loaded.")) as mock_start:
            for phrase in start_phrases:
                reply, badge, _ = self.engine._execute_single_command(phrase)
                self.assertIn("brain is loaded", reply, f"Failed phrase: '{phrase}'")
                self.assertEqual(badge, "Ollama: Online", f"Failed badge for: '{phrase}'")
                print(f"  [PASS] Start phrase: '{phrase}' -> {badge}")

    def test_02_stop_ollama_variations(self):
        print("\n--- 2. Testing Generalized Stop Ollama Commands ---")
        stop_phrases = [
            "stop ollama",
            "close ollama",
            "turn off ollama",
            "turn ollama off",
            "shut down ollama",
            "shutdown ollama",
            "kill ollama",
            "quit ollama",
            "exit ollama",
            "deactivate brain",
            "unload brain",
            "unload model",
            "put brain to sleep",
            "put brain on standby",
            "stop ai",
            "ollama off",
            "brain off",
            "sleep brain",
        ]
        with patch.object(void_widget, "stop_all_ollama_models", return_value=["lfm3-omni:2b"]) as mock_stop:
            for phrase in stop_phrases:
                reply, badge, _ = self.engine._execute_single_command(phrase)
                self.assertIn("Ollama stopped", reply, f"Failed phrase: '{phrase}'")
                self.assertEqual(badge, "Ollama: Standby", f"Failed badge for: '{phrase}'")
                print(f"  [PASS] Stop phrase: '{phrase}' -> {badge}")

    def test_03_restart_ollama(self):
        print("\n--- 3. Testing Restart Ollama Commands ---")
        restart_phrases = [
            "restart ollama",
            "reboot ollama",
            "reload ollama",
            "restart brain",
        ]
        with patch.object(void_widget, "restart_ollama_service", return_value=(True, "Ollama restarted successfully and lfm3-omni:2b brain is loaded.")) as mock_restart:
            for phrase in restart_phrases:
                reply, badge, _ = self.engine._execute_single_command(phrase)
                self.assertIn("Ollama restarted successfully", reply, f"Failed phrase: '{phrase}'")
                self.assertEqual(badge, "Ollama: Restarted", f"Failed badge for: '{phrase}'")
                print(f"  [PASS] Restart phrase: '{phrase}' -> {badge}")

    def test_04_custom_model_start(self):
        print("\n--- 4. Testing Custom Model Parameter Parsing ---")
        with patch.object(void_widget, "start_ollama_service", return_value=(True, "Ollama server started and llama3 brain is loaded.")) as mock_start:
            reply, badge, _ = self.engine._execute_single_command("start ollama with model llama3")
            self.assertIn("llama3", reply)
            mock_start.assert_called_with("llama3")
            print(f"  [PASS] Custom model 'llama3' parsed and started: {reply}")


if __name__ == "__main__":
    unittest.main()

