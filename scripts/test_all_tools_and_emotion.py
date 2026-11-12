import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set up paths
VOID_BIN = Path("/run/media/prakash/TR_39/VOID/bin")
sys.path.insert(0, str(VOID_BIN))

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", str(VOID_BIN / "void-widget.py"))
vw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vw)

class TestAllToolsAndEmotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hub = vw.DodaiosToolHub()
        cls.engine = vw.AudioVoiceEngine(cls.hub)
        cls.engine._tts = None  # prevent actual audio hardware speech output in automated tests

    def setUp(self):
        # Clear abort flag before each test
        self.engine._abort_requested.clear()

    def test_01_volume_controls(self):
        """Test master volume setting, adjustment, and mute toggle."""
        # 1. Set volume
        reply, badge, _ = self.engine._execute_single_command("set volume to 65%")
        self.assertIn("65%", reply)
        self.assertEqual(badge, "Audio: Volume 65%")

        # 2. Volume up
        reply, badge, _ = self.engine._execute_single_command("volume up")
        self.assertIn("Volume", reply)
        self.assertEqual(badge, "Audio: Volume Up")

        # 3. Volume down
        reply, badge, _ = self.engine._execute_single_command("volume down")
        self.assertIn("Volume", reply)
        self.assertEqual(badge, "Audio: Volume Down")

        # 4. Toggle mute
        reply, badge, _ = self.engine._execute_single_command("mute audio")
        self.assertIn("Audio is now", reply)
        self.assertEqual(badge, "Audio: Mute Toggled")

        # 5. Check volume
        reply, badge, _ = self.engine._execute_single_command("what is the volume")
        self.assertIn("Master audio volume is currently", reply)
        self.assertEqual(badge, "Audio: Status")

    def test_02_media_controls(self):
        """Test media controls via MPRIS DBus."""
        # Pause
        reply, badge, _ = self.engine._execute_single_command("pause music")
        self.assertIn("media", reply.lower())
        self.assertEqual(badge, "Media: Pause")

        # Play
        reply, badge, _ = self.engine._execute_single_command("play music")
        self.assertIn("media", reply.lower())
        self.assertEqual(badge, "Media: Play")

        # Next
        reply, badge, _ = self.engine._execute_single_command("next track")
        self.assertIn("media", reply.lower())
        self.assertEqual(badge, "Media: Next")

        # Previous
        reply, badge, _ = self.engine._execute_single_command("previous song")
        self.assertIn("media", reply.lower())
        self.assertEqual(badge, "Media: Previous")

        # Stop
        reply, badge, _ = self.engine._execute_single_command("stop music")
        self.assertIn("media", reply.lower())
        self.assertEqual(badge, "Media: Stop")

    def test_03_screen_brightness(self):
        """Test screen brightness control via KDE DBus."""
        # Set brightness
        reply, badge, _ = self.engine._execute_single_command("set brightness to 70%")
        self.assertIn("70%", reply)
        self.assertEqual(badge, "Screen: Brightness 70%")

        # Brightness up
        reply, badge, _ = self.engine._execute_single_command("brightness up")
        self.assertIn("brightness set to", reply.lower())
        self.assertIn("Screen: Brightness", badge)

        # Brightness down
        reply, badge, _ = self.engine._execute_single_command("screen dimmer")
        self.assertIn("brightness set to", reply.lower())
        self.assertIn("Screen: Brightness", badge)

        # Check brightness
        reply, badge, _ = self.engine._execute_single_command("what is the brightness")
        self.assertIn("Screen brightness is currently at", reply)
        self.assertEqual(badge, "Screen: Brightness")

    def test_04_clipboard_operations(self):
        """Test Wayland clipboard copy and read."""
        test_text = "VOID Agent Automated Test 2026"
        reply, badge, _ = self.engine._execute_single_command(f"copy {test_text} to clipboard")
        self.assertIn("Copied to clipboard", reply)
        self.assertEqual(badge, "Clipboard: Copied")

        reply, badge, _ = self.engine._execute_single_command("read clipboard")
        self.assertIn("Clipboard content:", reply)
        self.assertEqual(badge, "Clipboard: Content")

    def test_05_live_weather(self):
        """Test live weather fetching."""
        reply, badge, _ = self.engine._execute_single_command("weather in Paris")
        self.assertIn("Paris", reply)
        self.assertEqual(badge, "Weather: Paris")

        reply, badge, _ = self.engine._execute_single_command("what is the weather")
        self.assertIn("weather", reply.lower())
        self.assertEqual(badge, "Weather: Local")

    def test_06_hardware_vitals(self):
        """Test hardware vitals inspection (battery, temperatures)."""
        reply, badge, _ = self.engine._execute_single_command("hardware vitals")
        self.assertIn("Battery:", reply)
        self.assertIn("CPU", reply)
        self.assertEqual(badge, "Hardware Vitals")

        reply2, badge2, _ = self.engine._execute_single_command("battery status")
        self.assertIn("Battery:", reply2)
        self.assertEqual(badge2, "Hardware Vitals")

    def test_07_quick_notes(self):
        """Test saving and reading notes in ~/Documents/Notes."""
        reply, badge, _ = self.engine._execute_single_command(
            "take a note titled SystemCheck content All 32 tools are verified and operational."
        )
        self.assertIn("saved to", reply)
        self.assertEqual(badge, "Note: Saved (SystemCheck)")

        reply, badge, _ = self.engine._execute_single_command("read my note SystemCheck")
        self.assertIn("All 32 tools are verified and operational.", reply)
        self.assertEqual(badge, "Note: SystemCheck")

    def test_08_emotional_companion_chit_chat(self):
        """Test empathetic, celebratory, grateful, and greeting chit-chat."""
        # 1. Empathy state
        states_received = []
        self.engine.state_changed.connect(lambda s: states_received.append(s))

        reply, badge, _ = self.engine._execute_single_command("I'm feeling really stressed and exhausted today")
        self.assertIn("empathy", states_received)
        self.assertIn("Prakash", reply)
        self.assertEqual(badge, "Companion • Empathy 💙")

        # 2. Celebration state
        reply, badge, _ = self.engine._execute_single_command("We won and it worked! Celebrate!")
        self.assertIn("celebrate", states_received)
        self.assertIn("Prakash", reply)
        self.assertEqual(badge, "Companion • Celebration 🎉")

        # 3. Gratitude
        reply, badge, _ = self.engine._execute_single_command("Thank you so much VOID")
        self.assertIn("Prakash", reply)
        self.assertEqual(badge, "Companion • Gratitude 💫")

        # 4. Check-in
        reply, badge, _ = self.engine._execute_single_command("How are you doing today?")
        self.assertIn("Prakash", reply)
        self.assertIn("battery is at", reply)
        self.assertEqual(badge, "Companion • Check-in 💫")

        # 5. Morning greeting
        reply, badge, _ = self.engine._execute_single_command("Good morning VOID")
        self.assertIn("Good morning, Prakash", reply)
        self.assertEqual(badge, "Companion • Morning ☀️")

        # 6. Night greeting
        reply, badge, _ = self.engine._execute_single_command("Good night VOID")
        self.assertIn("Good night, Prakash", reply)
        self.assertEqual(badge, "Companion • Night 🌙")

    def test_09_stop_thinking_command(self):
        """Test stop thinking voice command aborts tasks."""
        reply, badge, _ = self.engine._execute_single_command("stop thinking")
        self.assertEqual(reply, "Stopped.")
        self.assertEqual(badge, "Cancelled")

    def test_10_interactive_email_prompting(self):
        """Test interactive prompting when user request lacks details."""
        orig_popen = vw.subprocess.Popen
        def mock_popen(args, **kwargs):
            if any("chromium" in str(a) for a in args):
                mock = MagicMock()
                mock.poll.return_value = None
                return mock
            return orig_popen(args, **kwargs)

        with patch("subprocess.Popen", side_effect=mock_popen):
            # Missing recipient triggers prompt
            reply1, badge1, _ = self.engine._execute_single_command("open chromium, open mail and compose email saying sorry for not attending party")
            self.assertIn("recipient", reply1.lower())
            self.assertEqual(badge1, "Prompt: Recipient")
            self.assertIsNotNone(self.engine._pending_action)

            # Providing recipient completes task
            reply2, badge2, _ = self.engine._execute_single_command("rskakavin@gmail.com")
            self.assertIn("rskakavin@gmail.com", reply2)
            self.assertIn("Webmail: Compose", badge2)
            self.assertIsNone(self.engine._pending_action)

if __name__ == "__main__":
    unittest.main(verbosity=2)
