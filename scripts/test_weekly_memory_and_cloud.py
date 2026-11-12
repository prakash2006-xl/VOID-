"""
Test Suite: VOID 7-Day High Memory Thought Retention & Offline Cloud Onboarding
Tests:
1. 7-Day Rolling Memory Retention (604,800 sec window)
2. Weekly Memory File Synthesis (.json & .md)
3. Deep Contextual Retrieval (query_weekly_memory)
4. Offline Cloud AI Detection & Onboarding Prompting
5. Cloud Credential Parsing and Provider Secret Masking
6. Voice Widget Command Integration
"""

import os
import sys
import time
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add VOID package root
VOID_ROOT = "/run/media/prakash/TR_39/VOID"
if VOID_ROOT not in sys.path:
    sys.path.insert(0, VOID_ROOT)

from agentic.memory import AgentMemoryManager, SEVEN_DAYS_SECONDS
from agentic.providers import (
    AIProviderManager,
    LocalOllamaProvider,
    CloudOpenAICompatibleProvider,
    parse_cloud_credentials,
)
from agentic.supervisor import SupervisorAgent
from agentic.tools import ToolRegistry
from agentic.permissions import PermissionManager
from agentic.audit import AuditLogger


class TestWeeklyMemoryManager(unittest.TestCase):
    """Verifies 7-day rolling memory thoughts, weekly digests, and deep historical queries."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="void_mem_test_")
        self.memory_mgr = AgentMemoryManager(memory_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_record_high_memory_thought(self):
        """Verifies high memory thoughts are stored in weekly_episodes.jsonl with full metadata."""
        rec = self.memory_mgr.record_high_memory_thought(
            query="Analyze Linux network latency and produce graph",
            thought_summary="Pinged gateway, detected 12ms jitter, generated latency_chart.png",
            plan_id="plan_net_001",
            outcome="success",
            artifacts=["/home/prakash/latency_chart.png"],
            tags=["network", "diagnostics"]
        )
        self.assertIsNotNone(rec)
        self.assertEqual(rec["query"], "Analyze Linux network latency and produce graph")
        self.assertIn("latency_chart.png", rec["artifacts"][0])

        episodes = self.memory_mgr.get_7day_episodes()
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["plan_id"], "plan_net_001")

    def test_02_seven_day_rolling_window_filtering(self):
        """Verifies episodes older than 7 days (604,800s) are filtered out from the active pool."""
        now = time.time()

        # Write fresh episode (1 hour old)
        self.memory_mgr.record_high_memory_thought(
            query="Recent task",
            thought_summary="Recent thoughts",
            plan_id="fresh_1"
        )

        # Write older episode (8 days old) directly into file
        old_ep = {
            "episode_id": "old_001",
            "timestamp": now - (8 * 24 * 3600),
            "iso_time": "2026-11-01T00:00:00Z",
            "week_id": "2026_W44",
            "day_name": "Friday",
            "query": "Old task from last week",
            "thought_summary": "Should be filtered out",
            "plan_id": "old_plan",
            "outcome": "completed",
            "artifacts": [],
            "tags": ["legacy"]
        }
        with open(self.memory_mgr.episodes_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(old_ep) + "\n")

        active_episodes = self.memory_mgr.get_7day_episodes()
        self.assertEqual(len(active_episodes), 1)
        self.assertEqual(active_episodes[0]["plan_id"], "fresh_1")

    def test_03_generate_weekly_memory_file(self):
        """Verifies weekly memory file synthesis generates both JSON and Markdown digests."""
        self.memory_mgr.record_high_memory_thought(
            query="Compile quarterly systems audit",
            thought_summary="Collected KDE Plasma DBus metrics and battery health",
            plan_id="audit_q4",
            artifacts=["/home/prakash/Documents/Reports/audit_q4.docx"],
            tags=["audit", "system"]
        )
        self.memory_mgr.record_high_memory_thought(
            query="Automate backup script",
            thought_summary="Wrote rsync bash pipeline and cron job",
            plan_id="backup_job",
            artifacts=["/home/prakash/backup.sh"],
            tags=["automation"]
        )

        md_path = self.memory_mgr.generate_weekly_memory_file()
        self.assertTrue(os.path.exists(md_path), f"File {md_path} was not created")
        self.assertTrue(md_path.endswith(".md"))

        # Verify corresponding JSON exists
        json_path = md_path.replace(".md", ".json")
        self.assertTrue(os.path.exists(json_path), f"JSON digest {json_path} was not created")

        # Read markdown contents
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("VOID Weekly Memory Digest", content)
        self.assertIn("**Total Interactions & Thought Traces:** 2", content)
        self.assertIn("audit_q4.docx", content)
        self.assertIn("backup.sh", content)

        # Read JSON digest
        with open(json_path, "r", encoding="utf-8") as f:
            j_data = json.load(f)
        self.assertEqual(j_data["total_episodes"], 2)
        self.assertEqual(len(j_data["artifacts_created"]), 2)

    def test_04_query_weekly_memory_retrieval(self):
        """Verifies deep retrieval from 7-day memory traces and answering questions."""
        self.memory_mgr.record_high_memory_thought(
            query="Setup WirePlumber audio fallback",
            thought_summary="Configured pw-play fallback pipeline to prevent audio collision",
            plan_id="audio_fix",
            artifacts=["/home/prakash/wireplumber_patch.py"],
            tags=["audio", "pipewire"]
        )

        res = self.memory_mgr.query_weekly_memory("What did we do regarding audio and WirePlumber?")
        self.assertGreater(res["match_count"], 0)
        self.assertTrue(any("wireplumber_patch.py" in a for a in res["artifacts"]))
        self.assertIn("audio", res["answer"].lower())


class TestCloudProviderAndCredentialParsing(unittest.TestCase):
    """Verifies credential parsing, provider configuration, and secret protection."""

    def test_01_parse_cloud_credentials(self):
        """Verifies natural parsing of free-form user speech/text for models and keys."""
        # Case 1: Standard model and key
        m, k, b = parse_cloud_credentials("gpt-4o sk-proj-1234567890abcdef1234")
        self.assertEqual(m, "gpt-4o")
        self.assertEqual(k, "sk-proj-1234567890abcdef1234")

        # Case 2: Natural spoken English
        m2, k2, b2 = parse_cloud_credentials("please connect to claude-3-5-sonnet with api key sk-ant-api03-abcdef1234567890")
        self.assertEqual(m2, "claude-3-5-sonnet")
        self.assertEqual(k2, "sk-ant-api03-abcdef1234567890")

        # Case 3: Only API key provided (should default to gpt-4o-mini)
        m3, k3, b3 = parse_cloud_credentials("sk-proj-11112222333344445555")
        self.assertEqual(m3, "gpt-4o-mini")
        self.assertEqual(k3, "sk-proj-11112222333344445555")

    def test_02_configure_cloud_provider(self):
        """Verifies cloud provider configuration and masked secret output."""
        mgr = AIProviderManager()
        res = mgr.configure_cloud(
            api_key="sk-test9999888877776666",
            model="gpt-4o-mini"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["model"], "gpt-4o-mini")
        self.assertTrue(res["masked_key"].startswith("sk-"))
        self.assertTrue(res["masked_key"].endswith("6666"))
        self.assertNotIn("99998888", res["masked_key"])
        self.assertTrue(mgr.is_cloud_configured())


class TestSupervisorIntegration(unittest.TestCase):
    """Verifies supervisor weekly memory and cloud workflows."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="void_sup_test_")
        self.perms = PermissionManager()
        self.tools = ToolRegistry(self.perms)
        self.providers = AIProviderManager()
        self.memory = AgentMemoryManager(memory_dir=self.test_dir)
        self.audit = AuditLogger(log_path=os.path.join(self.test_dir, "audit.jsonl"))
        self.supervisor = SupervisorAgent(
            tools=self.tools,
            provider_manager=self.providers,
            permission_manager=self.perms,
            memory_manager=self.memory,
            audit_logger=self.audit
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_supervisor_weekly_memory_fast_path(self):
        """Verifies supervisor generates weekly memory digest and answers recap requests."""
        # Seed an episode
        self.memory.record_high_memory_thought(
            query="Analyze KDE Plasma memory usage",
            thought_summary="Checked system monitor and cleaned caches",
            plan_id="kde_opt",
            artifacts=["/home/prakash/Documents/Reports/plasma_report.docx"],
            tags=["desktop", "optimization"]
        )

        # 1. Generate weekly memory via supervisor
        gen_res = self.supervisor.execute_goal("generate weekly memory")
        self.assertTrue(gen_res["success"])
        self.assertIn("weekly memory file generated successfully", gen_res["summary_text"].lower())
        self.assertTrue(os.path.exists(gen_res["artifacts"][0]))

        # 2. Query weekly memory via supervisor
        recap_res = self.supervisor.execute_goal("what did we do this week")
        self.assertTrue(recap_res["success"])
        self.assertIn("plasma_report.docx", recap_res["summary_text"])


class TestVoiceWidgetIntegration(unittest.TestCase):
    """Verifies AudioVoiceEngine direct command execution and interactive pending action flow."""

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        import importlib.util
        bin_path = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")
        spec = importlib.util.spec_from_file_location("void_widget", str(bin_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls.hub = mod.DodaiosToolHub()
        cls.engine = mod.AudioVoiceEngine(cls.hub)

    def test_01_widget_weekly_memory_commands(self):
        """Verifies generate and recap commands via widget engine."""
        # Record a test memory trace
        if hasattr(self.engine, "_agent_memory") and self.engine._agent_memory:
            self.engine._agent_memory.record_high_memory_thought(
                query="Build test harness for Fedora",
                thought_summary="Verified pytest execution and pipewire checks",
                plan_id="fedora_test",
                artifacts=["/home/prakash/test_results.log"],
                tags=["testing"]
            )

        # Generate weekly memory command
        reply, badge, thumb = self.engine._execute_single_command("generate weekly memory")
        self.assertEqual(badge, "Memory: Weekly File")
        self.assertIn("weekly memory file generated", reply.lower())

        # Recap weekly memory command
        reply_recap, badge_recap, _ = self.engine._execute_single_command("what did we do this week")
        self.assertEqual(badge_recap, "Memory: Weekly Recap")
        self.assertIn("Fedora", reply_recap)

    def test_02_widget_cloud_status_and_onboarding(self):
        """Verifies cloud status inspection, onboarding prompt, and interactive response."""
        # 1. Cloud status check
        reply, badge, _ = self.engine._execute_single_command("cloud status")
        self.assertEqual(badge, "AI Status")
        self.assertIn("Local Ollama:", reply)

        # 2. Connect cloud command triggers interactive prompt
        reply_prompt, badge_prompt, _ = self.engine._execute_single_command("connect cloud api")
        self.assertEqual(badge_prompt, "Prompt: Cloud Setup")
        self.assertIsNotNone(self.engine._pending_action)
        self.assertEqual(self.engine._pending_action.get("type"), "cloud_setup")

        # 3. User responds to prompt with credentials
        reply_conf, badge_conf, _ = self.engine._execute_single_command("gpt-4o sk-proj-1234567890abcdef1234")
        self.assertIn("Cloud AI connected successfully", reply_conf)
        self.assertEqual(badge_conf, "Cloud: Configured (gpt-4o)")
        self.assertIsNone(self.engine._pending_action)
        self.assertTrue(self.engine._agent_providers.is_cloud_configured())


if __name__ == "__main__":
    unittest.main()
