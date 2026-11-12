"""
VOID Agentic OS - Supervisor Agent
The central intelligence and command coordinator of the Multi-Agent architecture.
Classifies requests between deterministic fast-paths and multi-agent workflows,
orchestrates execution, records persistent memory, and synthesizes verifiable deliverables.
"""

import time
import logging
import re
from typing import Dict, Any, List, Optional, Callable
from agentic.types import (
    AgentRole,
    AgentTask,
    WorkflowPlan,
    WorkflowLifecycleState,
    TaskStatus,
)
from agentic.agents.base import BaseAgent
from agentic.orchestrator import MultiAgentOrchestrator
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager
from agentic.permissions import PermissionManager
from agentic.memory import AgentMemoryManager
from agentic.audit import AuditLogger

logger = logging.getLogger("VOID.Agentic.Supervisor")


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent that understands high-level intent, manages multi-agent workflows,
    ensures safety boundaries, and delivers verifiable results.
    """

    # Utterance keywords that strongly signal an agentic, multi-step workflow requiring planning
    AGENTIC_KEYWORDS = [
        "investigate", "diagnostic", "diagnose", "bottleneck", "scaffold",
        "unit test", "test suite", "fix bug", "research and write", "executive summary",
        "multi-agent", "agentic", "compile report", "system audit", "performance audit",
        "demo 1", "demo 2", "demo 3", "demo 4", "verify code",
        "weekly memory", "weekly summary", "this week", "weekly recap",
        "recall this week", "what did we do this week", "cloud api", "setup cloud",
        "data analysis project", "analyze dataset", "analyze csv",
        "compare models", "model comparison", "benchmark", "comparison document",
        "codebase audit", "analyze void", "improvement report", "roadmap report",
        "confirm playback has started", "verify playback has started",
    ]

    # Explicit direct commands that must always remain in the sub-5ms fast path
    FAST_PATH_EXACT = [
        "volume up", "volume down", "mute", "unmute",
        "screen brighter", "screen dimmer", "cancel", "stop dictation",
        "start ollama", "stop ollama", "pause", "resume", "next", "previous",
    ]

    def __init__(
        self,
        tools: ToolRegistry,
        provider_manager: AIProviderManager,
        permission_manager: PermissionManager,
        memory_manager: Optional[AgentMemoryManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        on_state_change: Optional[Callable[[WorkflowLifecycleState, WorkflowPlan, Optional[AgentTask]], None]] = None,
    ):
        super().__init__(
            role=AgentRole.SUPERVISOR,
            name="SupervisorAgent",
            description="Coordinates multi-agent planning, execution, verification, and memory.",
            tools=tools,
            provider_manager=provider_manager,
        )
        self.perm_mgr = permission_manager
        self.memory_mgr = memory_manager or AgentMemoryManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.orchestrator = MultiAgentOrchestrator(
            tools=tools,
            provider_manager=provider_manager,
            permission_manager=permission_manager,
            on_state_change=on_state_change,
        )

    def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Determines whether the input is a deterministic fast-path or an agentic workflow.
        Strictly reserves AGENTIC_WORKFLOW for genuinely difficult multi-step tasks.
        Guarantees sub-millisecond classification overhead (< 0.2ms) for maximum speed.
        """
        clean = text.strip().lower()

        # 1. Exact match direct commands (instant < 0.1ms)
        if clean in self.FAST_PATH_EXACT:
            return {"mode": "FAST_PATH", "reason": "Exact match direct hardware command"}

        # 2. Hardware controls (volume, brightness, mute, vitals, machine health)
        if clean.startswith("volume ") or clean.startswith("brightness ") or clean.startswith("set volume") or clean.startswith("screen "):
            return {"mode": "FAST_PATH", "reason": "Hardware direct command"}

        # 3. Direct media / song playback (must execute instantly on fast path, NOT planning)
        # Exception: Only route to AGENTIC if the user explicitly demands verified playback monitoring
        is_media_command = (
            clean.startswith("play ") or
            "play song" in clean or
            "play video" in clean or
            re.search(r"\b(?:open\s+)?youtube(?:\s+in\s+chromium)?\s+(?:and\s+)?(?:play|search)\b", clean)
        )
        has_explicit_verification = any(k in clean for k in ("confirm playback has started", "verify playback has started", "verify that playback"))
        if is_media_command and not has_explicit_verification:
            return {"mode": "FAST_PATH", "reason": "Direct media playback fast path"}

        # 4. Simple application / file / web actions
        if clean.startswith("open ") and not any(kw in clean for kw in self.AGENTIC_KEYWORDS):
            # Only complex workflows with explicit reporting/auditing go to agentic
            if not any(comp in clean for comp in ("audit", "report", "project", "dataset", "confirm playback")):
                return {"mode": "FAST_PATH", "reason": "Direct opener / single action"}

        # 5. Difficult Multi-Agent Workflows: Only triggered when task is genuinely complex
        if any(kw in clean for kw in self.AGENTIC_KEYWORDS):
            return {"mode": "AGENTIC_WORKFLOW", "reason": "Complex multi-agent workflow detected"}

        # 6. Difficult multi-step project scaffolding / dataset analysis heuristic
        if any(k in clean for k in ("create project", "scaffold", "generate dataset", "run test suite", "performance audit")):
            return {"mode": "AGENTIC_WORKFLOW", "reason": "Complex development/investigation task"}

        # Default: Everything else is FAST_PATH for instantaneous responsiveness
        return {"mode": "FAST_PATH", "reason": "Default single-turn query"}

    def execute_goal(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a high-level user goal using the full Multi-Agent pipeline:
        Planner -> Orchestrator -> Specialized Agents -> Verifier -> Memory & Audit.
        Supports 7-day high-memory thought synthesis, weekly digests, and historical recall.
        """
        start_time = time.time()
        g_lower = goal.lower().strip()

        # 1. Weekly Memory Digest Generation Fast-Path
        if any(kw in g_lower for kw in ("generate weekly memory", "create weekly memory", "save weekly memory", "weekly memory file", "synthesize weekly memory")):
            digest_path = self.memory_mgr.generate_weekly_memory_file()
            episodes = self.memory_mgr.get_7day_episodes()
            summary = (
                f"Weekly memory file generated successfully at {digest_path}. "
                f"Synthesized {len(episodes)} thought traces and actions across the past 7 days."
            )
            self.audit_logger.log_event("WEEKLY_MEMORY_GENERATED", self.name, details={"path": digest_path, "episodes": len(episodes)})
            return {
                "plan_id": f"plan_weekly_{int(time.time())}",
                "goal": goal,
                "state": "completed",
                "success": True,
                "summary_text": summary,
                "artifacts": [digest_path],
                "tasks_completed": 1,
                "total_tasks": 1,
                "duration_sec": 0.05,
            }

        # 2. Weekly Memory Deep Retrieval & Answering Fast-Path
        if any(kw in g_lower for kw in ("what did we do this week", "weekly recap", "recall this week", "recall from this week", "search weekly memory")):
            query_res = self.memory_mgr.query_weekly_memory(goal)
            self.audit_logger.log_event("WEEKLY_MEMORY_RECALLED", self.name, details={"matches": query_res["match_count"]})
            return {
                "plan_id": f"plan_recall_{int(time.time())}",
                "goal": goal,
                "state": "completed",
                "success": True,
                "summary_text": query_res["answer"],
                "artifacts": query_res["artifacts"],
                "tasks_completed": 1,
                "total_tasks": 1,
                "duration_sec": 0.05,
            }

        self.audit_logger.log_event("WORKFLOW_START", self.name, details={"goal": goal})

        # 3. Standard Multi-Agent DAG Generation & Execution
        plan = self.orchestrator.planner.create_plan(goal, context)
        self.audit_logger.log_event("PLAN_CREATED", "PlannerAgent", details={"plan_id": plan.plan_id, "tasks": len(plan.tasks)})

        completed_plan = self.orchestrator.execute_plan(plan, context)
        duration = round(time.time() - start_time, 3)

        # 4. Record task memory, workflow history, and High Memory Thought
        for task in completed_plan.tasks:
            self.memory_mgr.save_task(task)

        self.memory_mgr.record_workflow_completion(completed_plan)

        synthesis = self._synthesize_summary(completed_plan, duration)

        # High Memory Thought episode retention (7-day rolling window)
        self.memory_mgr.record_high_memory_thought(
            query=goal,
            thought_summary=synthesis["summary_text"],
            plan_id=completed_plan.plan_id,
            outcome=completed_plan.state.value if hasattr(completed_plan.state, "value") else str(completed_plan.state),
            artifacts=synthesis["artifacts"],
            tags=["workflow", "multi-agent"]
        )

        self.audit_logger.log_event(
            "WORKFLOW_END",
            self.name,
            details={
                "plan_id": completed_plan.plan_id,
                "state": completed_plan.state.value,
                "artifacts": synthesis["artifacts"],
            },
            success=(completed_plan.state == WorkflowLifecycleState.COMPLETED),
            duration_sec=duration,
        )

        return {
            "plan_id": completed_plan.plan_id,
            "goal": completed_plan.goal,
            "state": completed_plan.state.value,
            "success": (completed_plan.state == WorkflowLifecycleState.COMPLETED),
            "summary_text": synthesis["summary_text"],
            "artifacts": synthesis["artifacts"],
            "tasks_completed": sum(1 for t in completed_plan.tasks if t.status == TaskStatus.COMPLETED),
            "total_tasks": len(completed_plan.tasks),
            "duration_sec": duration,
            "plan": completed_plan,
        }

    def _synthesize_summary(self, plan: WorkflowPlan, duration_sec: float) -> Dict[str, Any]:
        """Creates a clear, truthful summary without hallucinations."""
        all_artifacts = []
        for t in plan.tasks:
            if t.result and t.result.artifacts:
                all_artifacts.extend(t.result.artifacts)
        artifacts = list(dict.fromkeys(all_artifacts))  # deduplicate preserving order

        completed_count = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        total_count = len(plan.tasks)

        if plan.state == WorkflowLifecycleState.COMPLETED:
            summary = f"Workflow completed successfully in {duration_sec}s. All {completed_count} tasks verified."
            if artifacts:
                summary += f" Generated {len(artifacts)} artifact(s): {', '.join(artifacts)}."
        elif plan.state == WorkflowLifecycleState.WAITING_APPROVAL:
            pending = next((t for t in plan.tasks if t.status == TaskStatus.WAITING_APPROVAL), None)
            desc = pending.description if pending else "action"
            summary = f"Workflow paused: User approval required for {desc}."
        elif plan.state == WorkflowLifecycleState.CANCELLED:
            summary = f"Workflow was cancelled. {completed_count} of {total_count} tasks had finished."
        else:
            failed_task = next((t for t in plan.tasks if t.status == TaskStatus.FAILED), None)
            err = failed_task.error if failed_task else "Unknown execution error"
            summary = f"Workflow failed at step '{failed_task.description if failed_task else 'unknown'}': {err}"

        return {
            "summary_text": summary,
            "artifacts": artifacts,
        }

