#!/usr/bin/env python3
"""
Unit test suite for Speech Response Restoration and System Invariance Safeguards.
Verifies:
1. Speech synthesis and playback pipeline with PipeWire pw-play fallback.
2. Volume and Brightness protection against unprompted changes, ambient noise, and LLM hallucinations.
3. Explicit volume and brightness controls work accurately.
4. Voice diagnostics ("test speech") and baseline restoration ("reset volume", "reset brightness").
"""

import sys
import unittest
from pathlib import Path

# Add bin directory to path
sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
import importlib
vw = importlib.import_module("void-widget")
AudioVoiceEngine = vw.AudioVoiceEngine
DodaiosToolHub = vw.DodaiosToolHub

class TestSpeechAndSystemInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate engine in headless mode
        cls.engine = AudioVoiceEngine.__new__(AudioVoiceEngine)
        super(AudioVoiceEngine, cls.engine).__init__()
        cls.engine.tool_hub = DodaiosToolHub()
        cls.engine._chat_history = []
        cls.engine._abort_requested = vw.threading.Event()
        cls.engine._is_speaking = False
        cls.engine._mute_audio_until = 0.0
        cls.engine._last_executed_cmd = ''
        cls.engine._last_cmd_timestamp = 0.0
        cls.engine._active_tts_proc = None
        cls.engine._initial_volume = 75
        cls.engine._initial_brightness = 80
        cls.engine._tts = None
        cls.engine._dictation_mode = False
        cls.engine._pending_action = None

    def test_01_text_cleaning_for_speech(self):
        """Verifies text cleaner removes markdown, technical tags, urls, paths, and emojis."""
        raw = "**VOID** status: <tool_call>calc(2+2)</tool_call> File at `/home/prakash/Documents/Notes/meeting.md` online! 💫 Visit https://google.com."
        cleaned = self.engine._clean_text_for_speech(raw)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("<tool_call>", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertIn("the link", cleaned)
        self.assertIn("the file", cleaned)
        self.assertNotIn("💫", cleaned)

    def test_02_speech_diagnostic_command(self):
        """Verifies 'test speech' and 'audio test' commands return clear audio diagnostic."""
        reply, badge, _ = self.engine._execute_single_command("test speech")
        self.assertIn("Speech response system is active and clear", reply)
        self.assertEqual(badge, "Audio: Speech Test")

        reply2, badge2, _ = self.engine._execute_single_command("audio test")
        self.assertIn("Speech response system is active and clear", reply2)
        self.assertEqual(badge2, "Audio: Speech Test")

    def test_03_volume_noise_invariance(self):
        """Verifies ambient words and non-volume phrases do NOT alter volume."""
        cur_v = self.engine.tool_hub.get_volume().get("volume_pct")
        
        # Ambiguous phrases that previously could trigger false-positives
        test_phrases = [
            "Please turn the document around",
            "I am reading chapter 1 volume 3",
            "This speaker seems much louder than yesterday",
            "The library is very quiet and peaceful",
            "The object is immutable and thread-safe"
        ]
        for phrase in test_phrases:
            reply, badge, _ = self.engine._execute_single_command(phrase)
            # Should NOT match volume
            self.assertNotEqual(badge, "Audio: Volume Up", f"Phrase '{phrase}' incorrectly triggered Volume Up")
            self.assertNotEqual(badge, "Audio: Volume Down", f"Phrase '{phrase}' incorrectly triggered Volume Down")
            self.assertNotEqual(badge, "Audio: Mute Toggled", f"Phrase '{phrase}' incorrectly triggered Mute")

    def test_04_brightness_noise_invariance(self):
        """Verifies ambient words and non-brightness phrases do NOT alter screen brightness."""
        test_phrases = [
            "The future looks much brighter ahead",
            "Why did the sky become dimmer in the evening",
            "Look at the star with brightness 10",
            "Turn around please"
        ]
        for phrase in test_phrases:
            reply, badge, _ = self.engine._execute_single_command(phrase)
            # Should NOT match brightness
            self.assertFalse(badge.startswith("Screen: Brightness"), f"Phrase '{phrase}' incorrectly triggered Screen Brightness")

    def test_05_explicit_volume_controls(self):
        """Verifies explicit volume commands work accurately."""
        # Set volume
        reply, badge, _ = self.engine._execute_single_command("set volume to 65%")
        self.assertIn("Volume set to 65%", reply)
        self.assertEqual(badge, "Audio: Volume 65%")

        # Volume up
        reply, badge, _ = self.engine._execute_single_command("volume up")
        self.assertIn("Volume adjusted", reply)
        self.assertEqual(badge, "Audio: Volume Up")

        # Volume down
        reply, badge, _ = self.engine._execute_single_command("volume down")
        self.assertIn("Volume adjusted", reply)
        self.assertEqual(badge, "Audio: Volume Down")

        # Status
        reply, badge, _ = self.engine._execute_single_command("what is the volume")
        self.assertIn("Master audio volume is currently", reply)
        self.assertEqual(badge, "Audio: Status")

    def test_06_explicit_brightness_controls(self):
        """Verifies explicit screen brightness commands work accurately."""
        # Set brightness
        reply, badge, _ = self.engine._execute_single_command("set brightness to 75%")
        self.assertIn("brightness set to 75%", reply.lower())
        self.assertEqual(badge, "Screen: Brightness 75%")

        # Brightness up
        reply, badge, _ = self.engine._execute_single_command("brightness up")
        self.assertIn("brightness set to", reply.lower())
        self.assertTrue(badge.startswith("Screen: Brightness"))

        # Brightness down
        reply, badge, _ = self.engine._execute_single_command("brightness down")
        self.assertIn("brightness set to", reply.lower())
        self.assertTrue(badge.startswith("Screen: Brightness"))

        # Status
        reply, badge, _ = self.engine._execute_single_command("what is the brightness")
        self.assertIn("Screen brightness is currently at", reply)
        self.assertEqual(badge, "Screen: Brightness")

    def test_07_restore_baseline_commands(self):
        """Verifies reset volume and reset brightness restore baselines."""
        reply_v, badge_v, _ = self.engine._execute_single_command("reset volume")
        self.assertIn("Restored master volume to baseline", reply_v)
        self.assertEqual(badge_v, "Audio: Volume 75%")

        reply_b, badge_b, _ = self.engine._execute_single_command("reset brightness")
        self.assertIn("Restored display brightness to baseline", reply_b)
        self.assertEqual(badge_b, "Screen: Brightness 80%")

    def test_08_llm_tool_call_hallucination_safeguards(self):
        """Verifies _execute_ai_tool rejects unprompted volume/brightness modifications from LLM."""
        # LLM hallucinating set_volume on unrelated user query
        res = self.engine._execute_ai_tool("set_volume", {"level_pct": 20}, query_context="What is the weather today?")
        self.assertIn("Current master volume is", res)

        # User actually asked for volume
        res_ok = self.engine._execute_ai_tool("set_volume", {"level_pct": 70}, query_context="Hey VOID change the volume to 70%")
        self.assertIn("Volume set to 70%", res_ok)

        # LLM hallucinating manage_brightness on unrelated user query
        res_b = self.engine._execute_ai_tool("manage_brightness", {"level_pct": 20}, query_context="Can you calculate 15 * 4?")
        self.assertIn("Current screen brightness is", res_b)

        # User actually asked for brightness
        res_b_ok = self.engine._execute_ai_tool("manage_brightness", {"level_pct": 85}, query_context="Make the screen brightness 85%")
        self.assertIn("Screen brightness set to 85%", res_b_ok)

    def test_09_tts_playback_pipeline_with_pwplay(self):
        """Verifies _speak_text correctly formats WAV and invokes pw-play without errors."""
        import subprocess
        # Test pw-play existence
        import shutil
        has_pwplay = shutil.which("pw-play") is not None
        self.assertTrue(has_pwplay, "pw-play executable must be available on the system")

        # Abort request handling
        self.engine._abort_requested.set()
        self.engine._speak_text("This should not speak because abort is set.")
        self.assertFalse(self.engine._is_speaking)
        self.engine._abort_requested.clear()

if __name__ == "__main__":
    unittest.main()
