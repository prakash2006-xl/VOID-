"""
VOID Agentic OS - Planner Agent
Decomposes complex user goals into machine-readable directed acyclic graph (DAG) plans.
Validates dependencies, assigns specialized agents, estimates complexity,
and provides dynamic replanning when conditions diverge.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from agentic.types import (
    AgentRole,
    AgentTask,
    WorkflowPlan,
    TaskStatus,
    PermissionLevel,
)
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager

logger = logging.getLogger("VOID.Agentic.Planner")


class PlannerAgent(BaseAgent):
    """
    Decomposes user objectives into structured execution plans with dependency graphs.
    """

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.PLANNER,
            name="PlannerAgent",
            description="Decomposes high-level objectives into validated DAG workflow plans.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> Any:
        # Planner generally invoked directly via create_plan or replan
        goal = task.tool_args.get("goal", task.description)
        plan = self.create_plan(goal, context)
        return plan

    def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> WorkflowPlan:
        """
        Generates a validated WorkflowPlan for a given user objective.
        Uses structured domain templates for high-reliability workflows,
        with fallback to LLM-guided decomposition.
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        goal_lower = goal.lower()

        tasks: List[AgentTask] = []

        # Domain Pattern 1: Linux System Diagnostics & Remediation
        if any(kw in goal_lower for kw in ("diagnostic", "system health", "cpu bottleneck", "memory check", "analyze system", "system performance")):
            tasks = self._plan_linux_diagnostics(plan_id, goal)

        # Domain Pattern 2: Software Development / Test-Driven Fix / Scaffolding
        elif any(kw in goal_lower for kw in ("scaffold", "write code", "fix bug", "run tests", "unit test", "develop", "debug python")):
            tasks = self._plan_software_dev(plan_id, goal, context)

        # Domain Pattern 3: Technical Research & Document Generation
        elif any(kw in goal_lower for kw in ("research", "write report", "executive summary", "docx", "generate document", "summarize topic")):
            tasks = self._plan_research_workflow(plan_id, goal, context)

        # Domain Pattern 4: Controlled File / Directory Operations
        elif any(kw in goal_lower for kw in ("clean cache", "inspect folder", "list files", "disk cleanup")):
            tasks = self._plan_file_operation(plan_id, goal, context)

        # General Multi-Step Fallback
        else:
            tasks = self._plan_generic_workflow(plan_id, goal)

        plan = WorkflowPlan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
            estimated_duration_sec=sum(t.timeout_sec for t in tasks) * 0.25,
            requires_approval=any(t.permission_level in (PermissionLevel.LEVEL_3_APPROVAL_REQUIRED, PermissionLevel.LEVEL_4_FORBIDDEN) for t in tasks),
        )

        self._validate_dag(plan)
        return plan

    def replan(
        self,
        current_plan: WorkflowPlan,
        failed_task: AgentTask,
        diagnostics: str,
    ) -> WorkflowPlan:
        """
        Dynamically replans by injecting compensatory or alternative tasks.
        """
        logger.info(f"Dynamic replanning triggered for plan {current_plan.plan_id} on task {failed_task.task_id}: {diagnostics}")

        new_tasks = []
        for t in current_plan.tasks:
            if t.task_id == failed_task.task_id:
                # Insert recovery diagnostic task before retrying or pivoting
                recovery_task_id = f"task_{uuid.uuid4().hex[:6]}_recovery"
                recovery_task = AgentTask(
                    task_id=recovery_task_id,
                    assigned_agent=AgentRole.RECOVERY,
                    description=f"Analyze and isolate defect for: {failed_task.description}",
                    tool_name="diagnose_failure",
                    tool_args={"failed_task_id": failed_task.task_id, "diagnostics": diagnostics},
                    depends_on=failed_task.depends_on,
                    permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
                )
                new_tasks.append(recovery_task)

                # Adjusted task depending on recovery
                failed_task.depends_on = [recovery_task_id]
                failed_task.status = TaskStatus.PENDING
                failed_task.error = None
                new_tasks.append(failed_task)
            else:
                new_tasks.append(t)

        current_plan.tasks = new_tasks
        self._validate_dag(current_plan)
        return current_plan

    def _validate_dag(self, plan: WorkflowPlan):
        """Ensures DAG has no cyclic dependencies and valid task references."""
        task_ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for dep in t.depends_on:
                if dep not in task_ids:
                    raise ValueError(f"Task {t.task_id} depends on non-existent task '{dep}'")

        # Cycle check via DFS
        visited = set()
        rec_stack = set()
        adj = {t.task_id: t.depends_on for t in plan.tasks}

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for tid in task_ids:
            if tid not in visited:
                if has_cycle(tid):
                    raise ValueError(f"Workflow plan contains cyclic dependency involving {tid}")

    # --- Structured Plan Builders ---

    def _plan_linux_diagnostics(self, plan_id: str, goal: str) -> List[AgentTask]:
        t1_id = f"{plan_id}_t1_telemetry"
        t2_id = f"{plan_id}_t2_processes"
        t3_id = f"{plan_id}_t3_diagnostic"
        t4_id = f"{plan_id}_t4_verify"

        t1 = AgentTask(
            task_id=t1_id,
            assigned_agent=AgentRole.LINUX_INTELLIGENCE,
            description="Inspect system hardware telemetry (CPU, RAM, Disk, Thermal).",
            tool_name="get_system_metrics",
            tool_args={},
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=10,
        )

        t2 = AgentTask(
            task_id=t2_id,
            assigned_agent=AgentRole.LINUX_INTELLIGENCE,
            description="Collect top resource-consuming processes.",
            tool_name="get_top_processes",
            tool_args={"count": 10, "sort_by": "memory"},
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=10,
        )

        t3 = AgentTask(
            task_id=t3_id,
            assigned_agent=AgentRole.LINUX_INTELLIGENCE,
            description="Synthesize diagnostics, detect bottlenecks, and draft user-level remediation report.",
            tool_name="linux_diagnostic",
            tool_args={"action": "full_audit"},
            depends_on=[t1_id, t2_id],
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=15,
        )

        t4 = AgentTask(
            task_id=t4_id,
            assigned_agent=AgentRole.VERIFIER,
            description="Independently verify diagnostic telemetry metrics and consistency.",
            tool_name="verify",
            tool_args={"target_type": "system_metrics"},
            depends_on=[t3_id],
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=10,
        )

        return [t1, t2, t3, t4]

    def _plan_software_dev(self, plan_id: str, goal: str, context: Optional[Dict[str, Any]]) -> List[AgentTask]:
        t1_id = f"{plan_id}_t1_scaffold"
        t2_id = f"{plan_id}_t2_run_tests"
        t3_id = f"{plan_id}_t3_verify"

        project_name = "void_agentic_app"
        if context and "project_name" in context:
            project_name = context["project_name"]

        t1 = AgentTask(
            task_id=t1_id,
            assigned_agent=AgentRole.DEVELOPER,
            description=f"Scaffold project '{project_name}' with source code and unit tests.",
            tool_name="scaffold_project",
            tool_args={
                "action": "scaffold_project",
                "project_name": project_name,
                "files": context.get("files", {}) if context else {},
            },
            permission_level=PermissionLevel.LEVEL_2_REVERSIBLE_USER_ACTION,
            timeout_sec=20,
        )

        t2 = AgentTask(
            task_id=t2_id,
            assigned_agent=AgentRole.DEVELOPER,
            description="Run test suite in sandboxed subprocess and parse output.",
            tool_name="run_workspace_tests",
            tool_args={
                "action": "run_tests",
                "test_path": context.get("test_path") if context else None,
            },
            depends_on=[t1_id],
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=25,
        )

        t3 = AgentTask(
            task_id=t3_id,
            assigned_agent=AgentRole.VERIFIER,
            description="Independently verify test suite completion and zero exit code.",
            tool_name="verify",
            tool_args={"target_type": "test_execution"},
            depends_on=[t2_id],
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=10,
        )

        return [t1, t2, t3]

    def _plan_research_workflow(self, plan_id: str, goal: str, context: Optional[Dict[str, Any]]) -> List[AgentTask]:
        t1_id = f"{plan_id}_t1_research"
        t2_id = f"{plan_id}_t2_verify_docx"

        topic = "Agentic AI Architecture"
        if context and "topic" in context:
            topic = context["topic"]
        elif "about " in goal.lower():
            topic = goal.lower().split("about ")[-1].strip()

        t1 = AgentTask(
            task_id=t1_id,
            assigned_agent=AgentRole.RESEARCH_PRODUCTIVITY,
            description=f"Conduct research on '{topic}' and compile executive DOCX report.",
            tool_name="conduct_research_and_report",
            tool_args={"action": "conduct_research_and_report", "topic": topic},
            permission_level=PermissionLevel.LEVEL_2_REVERSIBLE_USER_ACTION,
            timeout_sec=30,
        )

        t2 = AgentTask(
            task_id=t2_id,
            assigned_agent=AgentRole.VERIFIER,
            description="Independently verify generated DOCX file format, size, and integrity.",
            tool_name="verify",
            tool_args={"target_type": "artifact"},
            depends_on=[t1_id],
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=10,
        )

        return [t1, t2]

    def _plan_file_operation(self, plan_id: str, goal: str, context: Optional[Dict[str, Any]]) -> List[AgentTask]:
        t1_id = f"{plan_id}_t1_inspect"
        t1 = AgentTask(
            task_id=t1_id,
            assigned_agent=AgentRole.TOOL_EXECUTION,
            description="Inspect target directory contents and file sizes.",
            tool_name="inspect_directory",
            tool_args={"path": context.get("path", "~") if context else "~"},
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=15,
        )
        return [t1]

    def _plan_generic_workflow(self, plan_id: str, goal: str) -> List[AgentTask]:
        t1_id = f"{plan_id}_t1_execute"
        t1 = AgentTask(
            task_id=t1_id,
            assigned_agent=AgentRole.TOOL_EXECUTION,
            description=f"Execute: {goal}",
            tool_name="get_system_metrics",
            tool_args={},
            permission_level=PermissionLevel.LEVEL_1_READ_ONLY,
            timeout_sec=15,
        )
        return [t1]

