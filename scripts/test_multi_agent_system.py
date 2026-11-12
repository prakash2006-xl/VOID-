#!/usr/bin/env python3
"""
VOID Agentic OS - Comprehensive Multi-Agent Test Suite
Tests all layers of the Agentic Architecture:
1. Permissions (4-Tier Governance, Approvals, Sandbox Isolation)
2. Tools & Schema Validation (Dodaios & Linux adapters)
3. Planner & DAG Resolution (Dependency graphs, Cycle prevention)
4. Specialized Agents (Linux Intel, Developer, Research & Productivity, Tool Exec)
5. Independent Evidence Verification (File integrity, AST syntax, Test runners)
6. Recovery & Bounded Retries (Failure classification, Max 2 retries, Replanning)
7. Supervisor Intent Classification (Fast path vs Agentic workflow)
8. Competition Demos 1, 2, 3, and 4
"""

import os
import sys
import unittest
import shutil

# Guarantee path access
PKG_ROOT = "/run/media/prakash/TR_39/VOID"
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from agentic import (
    AgentRole,
    TaskStatus,
    PermissionLevel,
    WorkflowLifecycleState,
    PermissionManager,
    AIProviderManager,
    ToolRegistry,
    PlannerAgent,
    MultiAgentOrchestrator,
    SupervisorAgent,
    AgentMemoryManager,
    AuditLogger,
    CompetitionDemos,
    AgentActivityCard,
)
from agentic.agents import (
    LinuxIntelligenceAgent,
    DeveloperAgent,
    ResearchProductivityAgent,
    ToolExecutionAgent,
    VerificationAgent,
    RecoveryAgent,
)


class TestAgenticSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.perm_mgr = PermissionManager()
        cls.tools = ToolRegistry(cls.perm_mgr)
        cls.providers = AIProviderManager()
        cls.memory = AgentMemoryManager()
        cls.audit = AuditLogger()
        cls.supervisor = SupervisorAgent(
            tools=cls.tools,
            provider_manager=cls.providers,
            permission_manager=cls.perm_mgr,
            memory_manager=cls.memory,
            audit_logger=cls.audit,
        )
        cls.demos = CompetitionDemos(cls.supervisor)

    # -----------------------------------------------------------------------
    # 1. Permission Governance Tests
    # -----------------------------------------------------------------------
    def test_01_permission_levels(self):
        # Level 1 Read-only: get_system_metrics should be LEVEL_1
        check_res = self.perm_mgr.check_tool_permission("get_system_metrics", {})
        self.assertEqual(check_res["level"], PermissionLevel.LEVEL_1_READONLY)
        self.assertTrue(check_res["allowed"])

        # Level 4 Forbidden: /etc/passwd or root system paths
        check_forbidden = self.perm_mgr.check_tool_permission(
            "write_workspace_file", {"path": "/etc/shadow", "content": "bad"}
        )
        self.assertEqual(check_forbidden["level"], PermissionLevel.LEVEL_4_FORBIDDEN)
        self.assertFalse(check_forbidden["allowed"])

    def test_02_approval_queue(self):
        req = self.perm_mgr.request_approval("delete_cache", {"path": "~/.cache"}, "Clean cache")
        self.assertEqual(req.status.upper(), "PENDING")
        self.assertIsNotNone(self.perm_mgr.get_pending_request(req.request_id))

        # Confirm approval
        confirmed = self.perm_mgr.confirm_approval(req.request_id)
        self.assertTrue(confirmed)
        self.assertEqual(req.status.upper(), "APPROVED")

    # -----------------------------------------------------------------------
    # 2. Tool Registry Tests
    # -----------------------------------------------------------------------
    def test_03_tool_registry_execution(self):
        # Inspect system metrics
        res = self.tools.execute("get_system_metrics", {})
        self.assertTrue(res.success)
        self.assertIn("cpu_percent", res.metadata)
        self.assertIn("memory", res.metadata)

        # Inspect directory
        dir_res = self.tools.execute("inspect_directory", {"path": PKG_ROOT})
        self.assertTrue(dir_res.success)
        self.assertIn("file_count", dir_res.metadata)

    # -----------------------------------------------------------------------
    # 3. Planner & DAG Tests
    # -----------------------------------------------------------------------
    def test_04_planner_dag_construction(self):
        planner = self.supervisor.orchestrator.planner
        plan = planner.create_plan("Investigate system health and detect bottlenecks")
        self.assertIsNotNone(plan.plan_id)
        self.assertGreater(len(plan.tasks), 1)

        # Confirm DAG dependency integrity
        task_ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for dep in t.depends_on:
                self.assertIn(dep, task_ids)

    # -----------------------------------------------------------------------
    # 4. Specialized Agents Tests
    # -----------------------------------------------------------------------
    def test_05_linux_intelligence_agent(self):
        linux_agent = self.supervisor.orchestrator.linux_agent
        plan = self.supervisor.orchestrator.planner.create_plan("system health audit")
        task = plan.tasks[2]  # Diagnostic synthesis task
        result = linux_agent.perform_full_diagnostic(task)
        self.assertTrue(result.success)
        self.assertIn("=== VOID Linux Diagnostic Report ===", result.output)
        self.assertIn("cpu_percent", result.metadata)

    def test_06_developer_agent_scaffold_and_test(self):
        dev_agent = self.supervisor.orchestrator.dev_agent
        test_dir = os.path.expanduser("~/Documents/Projects/test_unit_run")
        files = {
            "app.py": "def greet(name):\n    return f'Hello, {name}!'\n",
            "test_app.py": (
                "import unittest\nfrom app import greet\n\n"
                "class TestApp(unittest.TestCase):\n"
                "    def test_greet(self):\n        self.assertEqual(greet('VOID'), 'Hello, VOID!')\n\n"
                "if __name__ == '__main__':\n    unittest.main()\n"
            ),
        }
        scaffold_res = dev_agent.scaffold_project("test_unit_run", test_dir, files)
        self.assertTrue(scaffold_res.success)

        test_path = os.path.join(test_dir, "test_app.py")
        test_res = dev_agent.tools.execute("run_workspace_tests", {
            "test_path": test_path,
            "project_dir": test_dir,
        })
        self.assertTrue(test_res.success)
        self.assertEqual(test_res.exit_code, 0)
        self.assertIn("OK", test_res.output)

    def test_07_research_agent_docx_generation(self):
        res_agent = self.supervisor.orchestrator.research_agent
        plan = self.supervisor.orchestrator.planner.create_plan("research Edge AI in Linux")
        task = plan.tasks[0]
        res = res_agent.conduct_full_research_workflow(task)
        self.assertTrue(res.success)
        self.assertTrue(len(res.artifacts) > 0)
        docx_path = res.artifacts[0]
        self.assertTrue(os.path.exists(docx_path))
        self.assertTrue(docx_path.endswith(".docx"))

    # -----------------------------------------------------------------------
    # 5. Independent Verification Agent Tests
    # -----------------------------------------------------------------------
    def test_08_verifier_evidence_checking(self):
        verifier = self.supervisor.orchestrator.verifier

        # A. Verify DOCX artifact
        reports_dir = os.path.expanduser("~/Documents/Reports")
        docx_files = [os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.endswith(".docx")]
        self.assertTrue(len(docx_files) > 0)
        v_res = verifier.verify("artifact", docx_files[0])
        self.assertTrue(v_res.verified)
        self.assertIn("File verified:", v_res.evidence)
        self.assertTrue(v_res.details.get("office_container_valid", False))

        # B. Verify Python syntax
        valid_py = os.path.join(PKG_ROOT, "agentic/types.py")
        v_syntax = verifier.verify("python_syntax", valid_py)
        self.assertTrue(v_syntax.verified)
        self.assertIn("Python syntax valid", v_syntax.evidence)

        # C. Non-existent file must fail verification
        v_fail = verifier.verify("artifact", "/tmp/non_existent_fake_file.xyz")
        self.assertFalse(v_fail.verified)
        self.assertEqual(v_fail.failure_reason, "FILE_NOT_FOUND")

    # -----------------------------------------------------------------------
    # 6. Recovery Agent & Bounded Retries Tests
    # -----------------------------------------------------------------------
    def test_09_recovery_agent_bounds(self):
        recovery = self.supervisor.orchestrator.recovery
        planner = self.supervisor.orchestrator.planner
        plan = planner.create_plan("test failure recovery")
        task = plan.tasks[0]

        # Case 1: First retry on syntax error
        task.error = "SyntaxError: invalid syntax"
        act1 = recovery.diagnose_and_plan_recovery(task)
        self.assertEqual(act1.action_type, "RETRY")
        self.assertEqual(task.retry_count, 1)

        # Case 2: Second retry
        act2 = recovery.diagnose_and_plan_recovery(task)
        self.assertEqual(act2.action_type, "RETRY")
        self.assertEqual(task.retry_count, 2)

        # Case 3: Reached max limit (MAX_RETRIES = 2) -> Must ABORT
        act3 = recovery.diagnose_and_plan_recovery(task)
        self.assertEqual(act3.action_type, "ABORT")
        self.assertIn("exceeded maximum retry limit", act3.reason)

    # -----------------------------------------------------------------------
    # 7. Supervisor Intent Classification Tests
    # -----------------------------------------------------------------------
    def test_10_supervisor_intent_classification(self):
        # Direct hardware actions -> FAST_PATH (sub-5ms)
        self.assertEqual(self.supervisor.classify_intent("volume 50%")["mode"], "FAST_PATH")
        self.assertEqual(self.supervisor.classify_intent("mute")["mode"], "FAST_PATH")
        self.assertEqual(self.supervisor.classify_intent("screen brighter")["mode"], "FAST_PATH")
        self.assertEqual(self.supervisor.classify_intent("open chromium")["mode"], "FAST_PATH")

        # Multi-agent requests -> AGENTIC_WORKFLOW
        self.assertEqual(self.supervisor.classify_intent("run system diagnostic and find bottlenecks")["mode"], "AGENTIC_WORKFLOW")
        self.assertEqual(self.supervisor.classify_intent("scaffold a python app with unit tests and verify")["mode"], "AGENTIC_WORKFLOW")
        self.assertEqual(self.supervisor.classify_intent("research edge ai in linux and write docx report")["mode"], "AGENTIC_WORKFLOW")
        self.assertEqual(self.supervisor.classify_intent("run agentic demo 1")["mode"], "AGENTIC_WORKFLOW")

    # -----------------------------------------------------------------------
    # 8. Competition Demonstrations 1, 2, 3, 4
    # -----------------------------------------------------------------------
    def test_11_demo_1_linux_diagnostics(self):
        res = self.demos.run_demo_1_linux_diagnostics()
        self.assertTrue(res["success"])
        self.assertEqual(res["state"], "completed")
        self.assertIn("Workflow completed successfully", res["summary_text"])

    def test_12_demo_2_test_driven_development(self):
        res = self.demos.run_demo_2_test_driven_development()
        self.assertTrue(res["success"])
        self.assertTrue(res["initial_failure_caught"])
        self.assertTrue(res["fix_applied"])
        self.assertTrue(res["verified"])
        self.assertIn("100% test pass", res["summary_text"])

    def test_13_demo_3_research_and_docx(self):
        res = self.demos.run_demo_3_research_and_docx("Edge AI Architectures in Linux")
        self.assertTrue(res["success"])
        self.assertTrue(len(res["artifacts"]) > 0)
        docx_file = res["artifacts"][0]
        self.assertTrue(os.path.exists(docx_file))
        self.assertGreater(os.path.getsize(docx_file), 5000)

    def test_14_demo_4_permission_gated_execution(self):
        res = self.demos.run_demo_4_permission_gated_execution()
        self.assertTrue(res["success"])
        self.assertEqual(res["after_confirmation_status"], "APPROVED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
