#!/usr/bin/env python3
"""
Test Suite for Universal Content Opener & Search Engine in VOID Desktop Assistant:
- __filename (local files with/without extensions, reports, notes, docs)
- _vedioname (local video files, online YouTube video streaming)
- _photoname (local images/screenshots, Google Images search)
- _appname (desktop applications)
- _browser (Chromium, Firefox, web services, URLs)
- etc (universal fallback web search in Chromium)
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, "/run/media/prakash/TR_39/VOID/bin")
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import importlib
void_widget = None
try:
    import importlib
    spec = importlib.util.spec_from_file_location("void_widget", "/run/media/prakash/TR_39/VOID/bin/void-widget.py")
    void_widget = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(void_widget)
except Exception as e:
    print(f"Error importing void_widget: {e}")


class TestUniversalOpenAndSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test directories and dummy files if needed
        cls.home = Path.home()
        cls.reports_dir = cls.home / "Documents/Reports"
        cls.reports_dir.mkdir(parents=True, exist_ok=True)
        cls.test_doc = cls.reports_dir / "Mothers_Importance.docx"
        if not cls.test_doc.exists():
            cls.test_doc.write_text("Dummy Docx Content", encoding="utf-8")

        cls.notes_dir = cls.home / "Documents/Notes"
        cls.notes_dir.mkdir(parents=True, exist_ok=True)
        cls.test_txt = cls.notes_dir / "test_notes.txt"
        cls.test_txt.write_text("Dummy Note Content", encoding="utf-8")

        cls.videos_dir = cls.home / "Videos"
        cls.videos_dir.mkdir(parents=True, exist_ok=True)
        cls.test_vid = cls.videos_dir / "sample_test_video.mp4"
        cls.test_vid.write_bytes(b"\x00\x00\x00\x18ftypmp42")

        cls.pictures_dir = cls.home / "Pictures"
        cls.pictures_dir.mkdir(parents=True, exist_ok=True)
        cls.test_img = cls.pictures_dir / "test_sample_photo.png"
        cls.test_img.write_bytes(b"\x89PNG\r\n\x1a\n")

        cls.tool_hub = void_widget.DodaiosToolHub()

    def test_01_filename_exact_and_stem(self):
        print("\n--- 1. Testing __filename (Documents, Reports, Notes) ---")
        # 1a. Exact filename with extension
        with patch("subprocess.Popen") as mock_popen:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("Mothers_Importance.docx")
            self.assertTrue(ok)
            self.assertIn("Mothers_Importance.docx", reply)
            self.assertIn("File:", badge)
            mock_popen.assert_called()
            print(f"  [PASS] Exact filename opened: {reply} (Badge: {badge})")

        # 1b. Stem filename without extension
        with patch("subprocess.Popen") as mock_popen:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("Mothers_Importance")
            self.assertTrue(ok)
            self.assertIn("Mothers_Importance", reply)
            mock_popen.assert_called()
            print(f"  [PASS] Stem filename without extension opened: {reply}")

        # 1c. Prefixed filename
        with patch("subprocess.Popen") as mock_popen:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("file test_notes.txt")
            self.assertTrue(ok)
            self.assertIn("test_notes.txt", reply)
            mock_popen.assert_called()
            print(f"  [PASS] Prefixed file opened: {reply}")

        # 1d. Non-existent file reports clean not-found message
        ok, reply, badge, media = self.tool_hub.open_or_search_content("file nonexistent_ghost_file_99.pdf")
        self.assertFalse(ok)
        self.assertIn("not found", reply.lower())
        self.assertEqual(badge, "File: Not Found")
        print(f"  [PASS] Non-existent file handled cleanly: {reply}")

    def test_02_videoname_local_and_youtube(self):
        print("\n--- 2. Testing _vedioname (Local Video & Online YouTube) ---")
        # 2a. Local video file
        with patch("subprocess.Popen") as mock_popen:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("sample_test_video.mp4")
            self.assertTrue(ok)
            self.assertIn("sample_test_video.mp4", reply)
            self.assertIn("Video:", badge)
            mock_popen.assert_called()
            print(f"  [PASS] Local video opened: {reply}")

        # 2b. Online YouTube video
        with patch.object(self.tool_hub, "play_youtube_query", return_value=(True, "Opened YouTube playing Believer.")) as mock_yt:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("believer video")
            self.assertTrue(ok)
            self.assertIn("YouTube", reply)
            self.assertIn("YouTube: Play", badge)
            mock_yt.assert_called_with("believer")
            print(f"  [PASS] Online video routed to YouTube: {reply} (Badge: {badge})")

        # 2c. Online song
        with patch.object(self.tool_hub, "play_youtube_query", return_value=(True, "Opened YouTube playing Bohemian Rhapsody.")) as mock_yt:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("song bohemian rhapsody")
            self.assertTrue(ok)
            self.assertIn("YouTube", reply)
            mock_yt.assert_called_with("bohemian rhapsody")
            print(f"  [PASS] Online song routed to YouTube: {reply}")

    def test_03_photoname_local_and_online(self):
        print("\n--- 3. Testing _photoname (Local Image & Google Images) ---")
        # 3a. Local image
        with patch("subprocess.Popen") as mock_popen:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("test_sample_photo.png")
            self.assertTrue(ok)
            self.assertIn("test_sample_photo.png", reply)
            self.assertIn("Photo:", badge)
            self.assertTrue(bool(media))
            mock_popen.assert_called()
            print(f"  [PASS] Local photo opened with thumbnail: {reply} (Thumbnail: {media})")

        # 3b. Online photo / Google Images search
        with patch.object(self.tool_hub, "open_browser", return_value="Opened Google Images.") as mock_browser:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("photo of aurora borealis")
            self.assertTrue(ok)
            self.assertIn("aurora borealis", reply)
            self.assertIn("Photos:", badge)
            mock_browser.assert_called()
            call_url = mock_browser.call_args[1].get("url", "")
            self.assertIn("tbm=isch", call_url)
            self.assertIn("aurora", call_url)
            print(f"  [PASS] Online photo routed to Google Images: {reply} (URL: {call_url})")

    def test_04_appname_launch(self):
        print("\n--- 4. Testing _appname (Desktop Applications) ---")
        # 4a. Calculator
        with patch.object(void_widget, "spawn_software", return_value=True) as mock_spawn:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("calculator")
            self.assertTrue(ok)
            self.assertIn("Kcalc", reply)
            self.assertIn("App: Open", badge)
            mock_spawn.assert_called_with("/usr/bin/kcalc")
            print(f"  [PASS] Calculator app launched: {reply}")

        # 4b. Terminal
        with patch.object(void_widget, "spawn_software", return_value=True) as mock_spawn:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("terminal")
            self.assertTrue(ok)
            self.assertIn("Konsole", reply)
            mock_spawn.assert_called_with("/usr/bin/konsole")
            print(f"  [PASS] Terminal app launched: {reply}")

    def test_05_browser_and_urls(self):
        print("\n--- 5. Testing _browser & URLs ---")
        # 5a. Browser default
        with patch.object(self.tool_hub, "open_browser", return_value="Opened Chromium.") as mock_b:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("chromium")
            self.assertTrue(ok)
            self.assertEqual(badge, "Browser: Chromium")
            print(f"  [PASS] Browser opened: {reply}")

        # 5b. Web URL
        with patch.object(self.tool_hub, "open_browser", return_value="Opened Google.") as mock_b:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("google.com")
            self.assertTrue(ok)
            self.assertIn("google.com", reply)
            mock_b.assert_called_with(url="https://google.com", new_tab=True)
            print(f"  [PASS] Web URL opened: {reply}")

        # 5c. Web Service (WhatsApp Web)
        with patch.object(self.tool_hub, "open_browser", return_value="Opened WhatsApp Web.") as mock_b:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("whatsapp web")
            self.assertTrue(ok)
            self.assertIn("WhatsApp Web", reply)
            mock_b.assert_called_with(url="https://web.whatsapp.com", new_tab=True)
            print(f"  [PASS] Web service opened: {reply}")

    def test_06_etc_fallback_search(self):
        print("\n--- 6. Testing etc (Fallback Web Search in Chromium) ---")
        with patch.object(self.tool_hub, "browser_search", return_value="Opened Google searching for quantum computing.") as mock_s:
            ok, reply, badge, media = self.tool_hub.open_or_search_content("quantum computing")
            self.assertTrue(ok)
            self.assertIn("quantum computing", reply)
            self.assertIn("Search:", badge)
            mock_s.assert_called_with("quantum computing")
            print(f"  [PASS] Fallback search executed: {reply}")

    def test_07_e2e_voice_engine_queries(self):
        print("\n--- 7. Testing End-to-End Voice Commands via _execute_single_command ---")
        engine = void_widget.AudioVoiceEngine(tool_hub=self.tool_hub)

        # 7a. Document query
        with patch("subprocess.Popen") as mock_popen:
            reply, badge, media = engine._execute_single_command("open Mothers_Importance")
            self.assertIn("Mothers_Importance", reply)
            print(f"  [PASS] Spoken query 'open Mothers_Importance': {reply} (Badge: {badge})")

        # 7b. Video query
        with patch.object(self.tool_hub, "play_youtube_query", return_value=(True, "Playing Believer on YouTube.")) as mock_yt:
            reply, badge, media = engine._execute_single_command("open believer video")
            self.assertIn("YouTube", reply)
            print(f"  [PASS] Spoken query 'open believer video': {reply} (Badge: {badge})")

        # 7c. Photo query
        with patch("subprocess.Popen") as mock_popen:
            reply, badge, media = engine._execute_single_command("open test_sample_photo.png")
            self.assertIn("test_sample_photo.png", reply)
            self.assertTrue(bool(media))
            print(f"  [PASS] Spoken query 'open test_sample_photo.png': {reply} (Media: {media})")

        # 7d. Online photo search
        with patch.object(self.tool_hub, "open_browser", return_value="Opened Google Images.") as mock_b:
            reply, badge, media = engine._execute_single_command("open photo sunset")
            self.assertIn("sunset", reply)
            print(f"  [PASS] Spoken query 'open photo sunset': {reply} (Badge: {badge})")

        # 7e. App launch query
        with patch.object(void_widget, "spawn_software", return_value=True) as mock_spawn:
            reply, badge, media = engine._execute_single_command("open calculator")
            self.assertIn("Kcalc", reply)
            print(f"  [PASS] Spoken query 'open calculator': {reply} (Badge: {badge})")

        # 7f. Fallback search query
        with patch.object(self.tool_hub, "browser_search", return_value="Opened Google search.") as mock_s:
            reply, badge, media = engine._execute_single_command("open quantum computing")
            self.assertIn("quantum computing", reply)
            print(f"  [PASS] Spoken query 'open quantum computing': {reply} (Badge: {badge})")

        # 7g. Search keyword query
        with patch.object(self.tool_hub, "browser_search", return_value="Opened Google search.") as mock_s:
            reply, badge, media = engine._execute_single_command("search python machine learning")
            self.assertIn("python machine learning", reply)
            print(f"  [PASS] Spoken query 'search python machine learning': {reply} (Badge: {badge})")


if __name__ == "__main__":
    unittest.main()
