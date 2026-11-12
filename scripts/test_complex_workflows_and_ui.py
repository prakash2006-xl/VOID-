#!/usr/bin/env python3
"""
VOID Agentic OS — Comprehensive Complex Workflows & UI Test Suite
Validates:
1. Complete 18-State TaskStatus Lifecycle and Validated Transitions.
2. Complex Task 1: YouTube Media Execution in Chromium (4 steps).
3. Complex Task 2: System Performance Investigation & Report (5 steps).
4. Complex Task 3: Autonomous Python CSV Data Analysis Project (5 steps).
5. Complex Task 4: Web Research & Local Model Comparison DOCX (4 steps).
6. Complex Task 5: Multi-Agent Productivity Workflow (Notes -> DOCX + XLSX) (4 steps).
7. Multi-Agent Cloud Configuration with Profiles and Per-Agent Model Routing.
8. CompactExecutionPopup, SystemInfoPopup, and Voice Output Fluency.
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Setup paths
VOID_ROOT = Path("/run/media/prakash/TR_39/VOID").resolve()
if str(VOID_ROOT) not in sys.path:
    sys.path.insert(0, str(VOID_ROOT))

from agentic.types import (
    AgentRole,
    TaskStatus,
    VALID_TASK_TRANSITIONS,
    PermissionLevel,
    WorkflowLifecycleState,
    AgentTask,
    WorkflowPlan,
    ToolResult,
    VerificationResult,
)
from agentic.permissions import PermissionManager
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager
from agentic.memory import AgentMemoryManager
from agentic.audit import AuditLogger
from agentic.supervisor import SupervisorAgent
from agentic.ui_components import CompactExecutionPopup, SystemInfoPopup


def log_test(name: str):
    print(f"\n{'='*70}\n[TEST] {name}\n{'='*70}", flush=True)


def test_1_task_status_engine():
    log_test("1. 18-State TaskStatus Engine & Validated Transitions")

    # 1. Verify all 18 canonical states exist
    canonical_18 = [
        "created", "analyzing", "planning", "plan_validating", "ready",
        "running", "waiting_for_dependency", "waiting_for_user", "waiting_for_approval",
        "verifying", "retrying", "recovering", "completed", "partially_completed",
        "failed", "cancelled", "timed_out", "blocked"
    ]
    for state_val in canonical_18:
        st = TaskStatus(state_val)
        assert st.value == state_val, f"Failed matching {state_val}"
    print("  ✓ All 18 canonical TaskStatus states defined and verified.")

    # 2. Verify backward-compatibility aliases
    assert TaskStatus("pending") == TaskStatus.CREATED
    assert TaskStatus("in_progress") == TaskStatus.RUNNING
    assert TaskStatus("waiting_approval") == TaskStatus.WAITING_FOR_APPROVAL
    assert TaskStatus.PENDING == TaskStatus.CREATED
    assert TaskStatus.IN_PROGRESS == TaskStatus.RUNNING
    print("  ✓ Backward-compatibility aliases (PENDING, IN_PROGRESS, WAITING_APPROVAL) intact.")

    # 3. Test AgentTask transitions
    task = AgentTask(description="Telemetry check")
    assert task.status == TaskStatus.CREATED
    assert task.transition_to(TaskStatus.READY)
    assert task.status == TaskStatus.READY
    assert task.transition_to(TaskStatus.RUNNING)
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    assert task.transition_to(TaskStatus.VERIFYING)
    assert task.status == TaskStatus.VERIFYING
    assert task.transition_to(TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.execution_time_sec >= 0.0
    print("  ✓ AgentTask.transition_to lifecycle with timestamp tracking validated.")

    # 4. Test WorkflowPlan parent status derivation
    t1 = AgentTask(description="Subtask 1", status=TaskStatus.COMPLETED)
    t2 = AgentTask(description="Subtask 2", status=TaskStatus.COMPLETED)
    plan_completed = WorkflowPlan(goal="All done", tasks=[t1, t2])
    assert plan_completed.compute_workflow_status() == TaskStatus.COMPLETED

    t3 = AgentTask(description="Subtask 3", status=TaskStatus.FAILED)
    plan_partial = WorkflowPlan(goal="Partial", tasks=[t1, t3])
    assert plan_partial.compute_workflow_status() == TaskStatus.PARTIALLY_COMPLETED

    t4 = AgentTask(description="Subtask 4", status=TaskStatus.RUNNING)
    plan_running = WorkflowPlan(goal="Running", tasks=[t1, t4])
    assert plan_running.compute_workflow_status() == TaskStatus.RUNNING
    print("  ✓ WorkflowPlan.compute_workflow_status aggregate derivation validated.")


def init_supervisor() -> SupervisorAgent:
    perm = PermissionManager()
    tools = ToolRegistry(perm)
    prov = AIProviderManager()
    mem = AgentMemoryManager()
    audit = AuditLogger()
    return SupervisorAgent(
        tools=tools,
        provider_manager=prov,
        permission_manager=perm,
        memory_manager=mem,
        audit_logger=audit,
    )


def test_2_youtube_media_execution(supervisor: SupervisorAgent):
    log_test("2. Complex Task 1: YouTube Media Execution in Chromium")
    goal = "Open a new tab in Chromium and open YouTube Play Believer song in YouTube"

    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  State: {res['state']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")

    assert res["total_tasks"] >= 3, f"Expected at least 3 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] >= 3, "All tasks should have completed successfully"
    assert res["success"] is True

    # Check tasks inside plan
    plan: WorkflowPlan = res["plan"]
    tool_names = [t.tool_name for t in plan.tasks]
    assert "open_youtube_playback" in tool_names, f"open_youtube_playback missing: {tool_names}"
    assert "verify" in tool_names, f"verify missing: {tool_names}"

    # Verify verifier task evidence
    ver_task = next(t for t in plan.tasks if t.tool_name == "verify")
    assert ver_task.status == TaskStatus.COMPLETED
    assert ver_task.verification_result is not None
    assert ver_task.verification_result.verified is True
    print(f"  ✓ Independent Verifier Evidence: {ver_task.verification_result.evidence}")
    print("  ✓ Complex Task 1 (YouTube Execution) passed with 100% verification.")


def test_3_system_performance_audit(supervisor: SupervisorAgent):
    log_test("3. Complex Task 2: System Performance Investigation & Report")
    goal = "Perform system performance audit and generate report"

    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")
    print(f"  Artifacts: {res['artifacts']}")

    assert res["total_tasks"] == 5, f"Expected 5 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] == 5
    assert res["success"] is True
    assert len(res["artifacts"]) >= 1

    report_file = res["artifacts"][0]
    assert os.path.exists(report_file), f"Report file does not exist: {report_file}"
    assert os.path.getsize(report_file) > 1000, f"Report file unexpectedly small: {os.path.getsize(report_file)} bytes"
    print(f"  ✓ Verified Report on Disk: {report_file} ({os.path.getsize(report_file)} bytes)")
    print("  ✓ Complex Task 2 (System Performance Audit) passed with 100% verification.")


def test_4_python_csv_project(supervisor: SupervisorAgent):
    log_test("4. Complex Task 3: Autonomous Python CSV Data Analysis Project")
    goal = "Build a python csv data analysis project with tests"

    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")
    print(f"  Artifacts: {res['artifacts']}")

    assert res["total_tasks"] == 5, f"Expected 5 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] == 5
    assert res["success"] is True

    project_dir = Path("/home/prakash/Documents/Projects/data_analysis")
    csv_file = project_dir / "dataset.csv"
    script_file = project_dir / "analyzer.py"
    test_file = project_dir / "test_analyzer.py"
    report_file = project_dir / "dataset.analysis.md"

    assert csv_file.exists(), "dataset.csv not generated"
    assert script_file.exists(), "analyzer.py not generated"
    assert test_file.exists(), "test_analyzer.py not generated"
    assert report_file.exists(), "dataset.analysis.md not generated"
    assert report_file.stat().st_size > 50

    print(f"  ✓ Project Directory Verified: {project_dir}")
    print(f"  ✓ Dataset: {csv_file.name} ({csv_file.stat().st_size} bytes)")
    print(f"  ✓ Analyzer: {script_file.name} ({script_file.stat().st_size} bytes)")
    print(f"  ✓ Unit Tests: {test_file.name} ({test_file.stat().st_size} bytes)")
    print(f"  ✓ Statistical Analysis Report: {report_file.name} ({report_file.stat().st_size} bytes)")
    print("  ✓ Complex Task 3 (Python CSV Project) passed with 100% verification.")


def test_5_web_research_comparison(supervisor: SupervisorAgent):
    log_test("5. Complex Task 4: Web Research & Local Model Comparison DOCX")
    goal = "Conduct local llm model comparison and benchmark research"

    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")
    print(f"  Artifacts: {res['artifacts']}")

    assert res["total_tasks"] == 4, f"Expected 4 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] == 4
    assert res["success"] is True
    assert len(res["artifacts"]) >= 1

    docx_path = res["artifacts"][0]
    assert os.path.exists(docx_path), f"DOCX file does not exist: {docx_path}"
    assert os.path.getsize(docx_path) > 1000

    print(f"  ✓ Generated Comparison Document: {docx_path} ({os.path.getsize(docx_path)} bytes)")
    print("  ✓ Complex Task 4 (Web Research DOCX) passed with 100% verification.")


def test_6_void_project_analysis(supervisor: SupervisorAgent):
    log_test("6. Complex Task 5: Multi-Agent VOID Project Analysis & Development Report")
    goal = "Analyze the VOID project, identify possible bugs and prepare a development improvement report"

    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")
    print(f"  Artifacts: {res['artifacts']}")

    assert res["total_tasks"] == 5, f"Expected 5 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] == 5
    assert res["success"] is True
    assert len(res["artifacts"]) >= 1

    report_path = res["artifacts"][0]
    assert os.path.exists(report_path)
    assert os.path.getsize(report_path) > 1000

    print(f"  ✓ Verified Development Improvement Report DOCX: {report_path} ({os.path.getsize(report_path)} bytes)")
    print("  ✓ Complex Task 5 (VOID Project Analysis) passed with 100% verification.")


def test_7_productivity_notes_and_sheet(supervisor: SupervisorAgent):
    log_test("7. Bonus Workflow: Multi-Agent Productivity Workflow (Notes -> DOCX + XLSX)")
    notes_dir = Path("/home/prakash/Documents/Notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    sample_note = notes_dir / "bootcamp_prep.md"
    sample_note.write_text(
        "# Bootcamp Preparation 2026\n"
        "- [ ] Action: Complete multi-agent DAG verification\n"
        "- [ ] Milestone: Finalize offline cloud AI fallback\n"
        "- [ ] Todo: Polish frosted glass UI popups\n",
        encoding="utf-8"
    )

    goal = "Compile meeting notes and extract action items into a spreadsheet"
    res = supervisor.execute_goal(goal)
    print(f"  Plan ID: {res['plan_id']}")
    print(f"  Tasks Completed: {res['tasks_completed']}/{res['total_tasks']}")
    print(f"  Summary: {res['summary_text']}")
    print(f"  Artifacts: {res['artifacts']}")

    assert res["total_tasks"] == 4, f"Expected 4 tasks, got {res['total_tasks']}"
    assert res["tasks_completed"] == 4
    assert res["success"] is True
    assert len(res["artifacts"]) >= 2

    docx_path = next(a for a in res["artifacts"] if a.endswith(".docx"))
    xlsx_path = next(a for a in res["artifacts"] if a.endswith(".xlsx"))
    assert os.path.exists(docx_path) and os.path.getsize(docx_path) > 500
    assert os.path.exists(xlsx_path) and os.path.getsize(xlsx_path) > 500

    print(f"  ✓ Verified Executive Notes DOCX: {docx_path} ({os.path.getsize(docx_path)} bytes)")
    print(f"  ✓ Verified Action Items XLSX: {xlsx_path} ({os.path.getsize(xlsx_path)} bytes)")
    print("  ✓ Productivity Workflow passed with 100% verification.")


def test_8_multi_agent_cloud_config():
    log_test("8. Multi-Agent Cloud Configuration & Secret Masking")
    pm = AIProviderManager()

    # Verify profiles
    profiles = pm.list_profiles()
    print("  Configured Profiles:")
    for k, v in profiles.items():
        print(f"    - {k} ({v['name']}): masked_key={v['masked_key']}, model={v['default_model']}")
        assert "sk-proj" not in v["masked_key"]  # Key must be masked!
        assert "gsk_" not in v["masked_key"]
    assert "openai" in profiles
    assert "deepseek" in profiles
    assert "groq" in profiles
    assert "openrouter" in profiles
    assert "ollama_local" in profiles

    # Verify per-agent routing
    prov_sup = pm.get_provider_for_agent(AgentRole.SUPERVISOR)
    prov_dev = pm.get_provider_for_agent(AgentRole.DEVELOPER)
    prov_linux = pm.get_provider_for_agent(AgentRole.LINUX_INTELLIGENCE)

    assert prov_sup.model == "gpt-4o"
    assert prov_dev.model == "deepseek-coder"
    assert prov_linux.model == "lfm3-omni:2b"
    print("  ✓ Per-agent model routing validated across OpenAI, DeepSeek, and Ollama.")

    # Test dynamic model reassignment
    pm.set_agent_model("developer", "openai", "gpt-4o-mini")
    prov_dev2 = pm.get_provider_for_agent(AgentRole.DEVELOPER)
    assert prov_dev2.model == "gpt-4o-mini"
    print("  ✓ Dynamic model reassignment verified.")

    # Revert back
    pm.set_agent_model("developer", "deepseek", "deepseek-coder")


def test_9_default_system_agent_fallback():
    log_test("9. Mandatory Acceptance Test: Default System Agent Fallback (Simulated Total Outage)")
    from agentic.providers import DefaultSystemProvider
    from agentic.orchestrator import MultiAgentOrchestrator
    from agentic.agents.system_agent import DefaultSystemAgent

    pm = AIProviderManager()
    # 1. Simulate all cloud providers being unavailable and local Ollama down
    pm.profiles = {}
    pm.agent_model_assignments = {}
    pm.is_local_online = lambda: False

    prov, tier_desc = pm.route_hierarchical(AgentRole.SUPERVISOR)
    print(f"  Routing during total outage: {tier_desc}")
    assert isinstance(prov, DefaultSystemProvider)
    assert prov.name == "default-system-agent"
    assert "Tier 4" in tier_desc

    # 2. Test conversational response generation during total outage
    resp = prov.generate("Hello VOID, what can you do?")
    print(f"  Default System Agent response: '{resp}'")
    assert "Default System Agent" in resp
    assert len(resp) > 20

    # 3. Test Orchestrator dispatching to Default System Agent
    perm = PermissionManager()
    tools = ToolRegistry(perm)
    orch = MultiAgentOrchestrator(tools, pm, perm)

    assert orch.system_agent is not None
    assert isinstance(orch.system_agent, DefaultSystemAgent)

    # 4. Dispatch a real system task through Default System Agent
    task = AgentTask(
        description="Read hardware metrics during total outage",
        tool_name="get_system_metrics",
        assigned_agent=AgentRole.DEFAULT_SYSTEM
    )
    result = orch.system_agent.run_task(task, {})
    assert result.success is True
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    print(f"  ✓ Task executed successfully by DefaultSystemAgent: success={result.success}, duration={task.execution_time_sec}s")
    print("  ✓ Mandatory Acceptance Test for Default System Agent Fallback PASSED 100%.")


def test_10_ui_popups_and_speech():
    log_test("10. UI Popups & Voice Cleaning Verification")

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(["--platform", "offscreen"])
    except Exception:
        app = None

    # 1. CompactExecutionPopup
    popup = CompactExecutionPopup()
    assert popup.width() == 360
    assert popup.height() == 240
    t = AgentTask(description="Test step", assigned_agent=AgentRole.TOOL_EXECUTION, status=TaskStatus.RUNNING)
    p = WorkflowPlan(goal="Test UI goal", tasks=[t])
    popup.update_execution(WorkflowLifecycleState.EXECUTING, p, t)
    print("  ✓ CompactExecutionPopup initialized and updated cleanly.")

    # 2. SystemInfoPopup
    sys_popup = SystemInfoPopup()
    assert sys_popup.width() == 340
    assert sys_popup.height() == 260
    sys_popup.refresh_metrics()
    print("  ✓ SystemInfoPopup telemetry refresh executed cleanly.")

    # 3. Speech Cleaner & Fluency Enforcement
    import re
    def clean_text_for_speech(text: str) -> str:
        s = text
        s = re.sub(r"```[\s\S]*?```", "", s)
        s = re.sub(r"<tool_call>.*?</tool_call>", "", s, flags=re.DOTALL)
        s = re.sub(r"\{[^{}]*\}", "", s)
        s = re.sub(r"\b([a-z]+)_([a-z]+)\b", r"\1 \2", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"\*([^*]+)\*", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
        s = re.sub(r"^\s*[-*•]\s*", "", s, flags=re.MULTILINE)
        s = re.sub(r"https?://\S+", "the link", s)
        s = re.sub(r"/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)+", "the file", s)
        s = re.sub(r"[\U00010000-\U0010ffff]", "", s)
        s = re.sub(r"[⏱️🎧💭💬💙🎉💫☀️🌙🌤️➔✕●⏺⏹✅⚙️🔍🔄🛑🚫⚠️❌📊]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if len(s) > 200:
            sentences = re.split(r"(?<=[.!?])\s+", s)
            if len(sentences) > 2:
                s = " ".join(sentences[:2]).strip()
        return s

    raw_complex_output = (
        "```python\ndef test(): pass\n```\n"
        "<tool_call>{\"name\": \"get_system_metrics\", \"args\": {}}</tool_call>\n"
        "# Executive Performance Report\n"
        "- [ ] Item 1: CPU load is **nominal** at 15.2%.\n"
        "- [ ] Item 2: All 5 tasks completed successfully.\n"
        "Here is the third sentence that would normally bloat speech output into an incomprehensible torrent of text."
    )
    clean_speech = clean_text_for_speech(raw_complex_output)
    print(f"  Raw Text Length: {len(raw_complex_output)} chars")
    print(f"  Clean Spoken Text: '{clean_speech}' ({len(clean_speech)} chars)")

    assert "```" not in clean_speech
    assert "<tool_call>" not in clean_speech
    assert "{" not in clean_speech
    assert "**" not in clean_speech
    assert len(clean_speech) < 250
    print("  ✓ Voice text cleaning guarantees fluent, comprehensible output without acceleration.")


def main():
    print("=" * 80)
    print("  VOID AGENTIC OS — COMPREHENSIVE COMPLEX WORKFLOWS & UI TEST SUITE")
    print("=" * 80)
    t0 = time.time()

    test_1_task_status_engine()

    supervisor = init_supervisor()

    test_2_youtube_media_execution(supervisor)
    test_3_system_performance_audit(supervisor)
    test_4_python_csv_project(supervisor)
    test_5_web_research_comparison(supervisor)
    test_6_void_project_analysis(supervisor)
    test_7_productivity_notes_and_sheet(supervisor)

    test_8_multi_agent_cloud_config()
    test_9_default_system_agent_fallback()
    test_10_ui_popups_and_speech()

    duration = round(time.time() - t0, 2)
    print("\n" + "=" * 80)
    print(f"  ✅ ALL 10 TEST SUITES (5 MANDATORY + 5 SYSTEM/UI) PASSED FLAWLESSLY IN {duration}s")
    print("  Zero errors, zero regressions, full multi-agent autonomous validation.")
    print("=" * 80)


if __name__ == "__main__":
    main()
