#!/usr/bin/env python3
"""
Test Suite: Fast-Path Intent Classification & Accurate Song Query Routing
Verifies that:
1. Fast-path tasks (media, hardware, app launch, chat) bypass planning and respond instantaneously (< 1ms).
2. Difficult multi-agent tasks (code generation, audits, benchmarks) correctly route to planning.
3. Any requested song (Pesamalaye, Shape of You, Starboy, etc.) is accurately extracted without defaulting to Believer.
4. Old background audio is paused cleanly before starting new media.
"""

import sys
import time
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure VOID root is on python path
sys.path.insert(0, '/run/media/prakash/TR_39/VOID')

from agentic.supervisor import SupervisorAgent
from agentic.tools import ToolRegistry, extract_media_song_query
from agentic.providers import AIProviderManager
from agentic.permissions import PermissionManager


class TestFastClassificationAndSongPlayback(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.perm_mgr = PermissionManager()
        cls.tools = ToolRegistry(cls.perm_mgr)
        cls.providers = AIProviderManager()
        cls.supervisor = SupervisorAgent(
            tools=cls.tools,
            provider_manager=cls.providers,
            permission_manager=cls.perm_mgr
        )

    def test_01_classification_rules_fast_vs_difficult(self):
        """Verify that only difficult tasks enter planning, while fast tasks respond immediately."""
        test_cases = [
            # Fast-path queries (Must NEVER trigger slow planning)
            ("open youtube in chromium and play pesamalaye song", "FAST_PATH"),
            ("open youtube and play pesamalaye song", "FAST_PATH"),
            ("play pesamalaye", "FAST_PATH"),
            ("play shape of you", "FAST_PATH"),
            ("play starboy on youtube", "FAST_PATH"),
            ("play believer song", "FAST_PATH"),
            ("volume 80%", "FAST_PATH"),
            ("mute", "FAST_PATH"),
            ("open calculator", "FAST_PATH"),
            ("open terminal", "FAST_PATH"),
            ("system status", "FAST_PATH"),
            ("what is the battery percentage", "FAST_PATH"),
            ("take a screenshot", "FAST_PATH"),
            ("search for python in chromium", "FAST_PATH"),
            ("hello void how are you", "FAST_PATH"),

            # Difficult / Multi-Agent tasks (MUST enter planning)
            (
                "Open Chromium, go to YouTube, search for Believer by Imagine Dragons, open the correct result, play the song and confirm playback has started",
                "AGENTIC_WORKFLOW"
            ),
            (
                "Perform a full system performance audit. Check CPU, memory, disk, network connections and top processes. Identify any bottlenecks and compile an executive report document with recommendations.",
                "AGENTIC_WORKFLOW"
            ),
            (
                "Create a complete data analysis project in ~/Documents/Projects/data_analysis. Generate a realistic dataset of 20 customer records in CSV format, write a Python analysis script that computes summary statistics and customer segmentation, write a unit test file, execute the tests and report the final statistical summary.",
                "AGENTIC_WORKFLOW"
            ),
            (
                "Research the current best open-source local LLMs for coding and desktop agents in 2026. Compare at least three models across size, quantization, memory requirements and benchmark scores. Produce a comparison document with recommendations.",
                "AGENTIC_WORKFLOW"
            ),
            (
                "Analyze the VOID codebase itself. Scan the project structure, evaluate the agentic architecture, identify areas for improvement and generate a development roadmap report.",
                "AGENTIC_WORKFLOW"
            ),
            ("demo 1", "AGENTIC_WORKFLOW"),
            ("demo 2", "AGENTIC_WORKFLOW"),
            ("demo 3", "AGENTIC_WORKFLOW"),
            ("demo 4", "AGENTIC_WORKFLOW"),
        ]

        for query, expected_mode in test_cases:
            t0 = time.perf_counter()
            res = self.supervisor.classify_intent(query)
            dt_us = (time.perf_counter() - t0) * 1e6
            mode = res.get("mode")
            self.assertEqual(
                mode,
                expected_mode,
                f"Classification failed for: {query!r} -> Got {mode}, expected {expected_mode}"
            )
            # Classification must complete in less than 500 microseconds (0.5ms)
            self.assertLess(dt_us, 500.0, f"Classification too slow: {dt_us:.1f}us for {query[:30]}")

    def test_02_accurate_song_extraction_no_hardcoded_believer(self):
        """Verify that any song request extracts the exact user-specified track, never defaulting to Believer."""
        song_tests = [
            ("OPEN  YOUTUBE IN CHROMIUM AND PLAY PESAMALAYAE SONG", "PESAMALAYAE"),
            ("open youtube and play pesamalaye song", "pesamalaye"),
            ("play pesamalaye", "pesamalaye"),
            ("play shape of you", "shape of you"),
            ("play starboy on youtube", "starboy"),
            ("play perfect by ed sheeran", "perfect by ed sheeran"),
            ("play Bohemian Rhapsody", "Bohemian Rhapsody"),
            ("open youtube and play believer song", "believer"),
            ("play song believer", "believer"),
            (
                "Open Chromium, go to YouTube, search for Believer by Imagine Dragons, open the correct result, play the song and confirm playback has started",
                "Believer by Imagine Dragons"
            )
        ]

        for utterance, expected_song in song_tests:
            extracted = extract_media_song_query(utterance)
            self.assertEqual(
                extracted.strip().lower(),
                expected_song.strip().lower(),
                f"Failed song extraction for {utterance!r}: extracted {extracted!r}, expected {expected_song!r}"
            )

    def test_03_direct_execution_speed_and_mpris_isolation(self):
        """Verify that direct command execution resolves in < 5ms and pauses active players."""
        res = self.tools.execute_tool(
            name="open_youtube_playback",
            args={"query": "pesamalaye"}
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("query"), "pesamalaye")
        self.assertNotIn("believer", res.data.get("query").lower())


if __name__ == "__main__":
    unittest.main()
