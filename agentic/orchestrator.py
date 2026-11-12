"""
VOID Agentic OS - Multi-Agent Orchestrator
Coordinates DAG dependency resolution, agent task dispatch, real-time lifecycle transitions,
independent verification checkpoints, and recovery loop integration.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from agentic.types import (
    AgentRole,
    AgentTask,
    WorkflowPlan,
    WorkflowLifecycleState,
    TaskStatus,
    ToolResult,
    VerificationResult,
    PermissionLevel,
)
from agentic.agents.base import BaseAgent
from agentic.agents.linux_agent import LinuxIntelligenceAgent
from agentic.agents.dev_agent import DeveloperAgent
from agentic.agents.research_agent import ResearchProductivityAgent
from agentic.agents.tool_agent import ToolExecutionAgent
from agentic.agents.verifier_agent import VerificationAgent
from agentic.agents.recovery_agent import RecoveryAgent
from agentic.planner import PlannerAgent
from agentic.permissions import PermissionManager
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager

logger = logging.getLogger("VOID.Agentic.Orchestrator")


class MultiAgentOrchestrator:
    """
    Central execution engine that coordinates multiple specialized agents
    over a validated DAG workflow plan.
    """

    def __init__(
        self,
        tools: ToolRegistry,
        provider_manager: AIProviderManager,
        permission_manager: PermissionManager,
        on_state_change: Optional[Callable[[WorkflowLifecycleState, WorkflowPlan, Optional[AgentTask]], None]] = None,
    ):
        self.tools = tools
        self.provider_mgr = provider_manager
        self.perm_mgr = permission_manager
        self.on_state_change = on_state_change

        # Initialize specialized agents
        self.planner = PlannerAgent(tools, provider_manager)
        self.linux_agent = LinuxIntelligenceAgent(tools, provider_manager)
        self.dev_agent = DeveloperAgent(tools, provider_manager)
        self.research_agent = ResearchProductivityAgent(tools, provider_manager)
        self.tool_agent = ToolExecutionAgent(tools, provider_manager)
        self.verifier = VerificationAgent(tools, provider_manager)
        self.recovery = RecoveryAgent(tools, provider_manager)

        self._agents: Dict[AgentRole, BaseAgent] = {
            AgentRole.PLANNER: self.planner,
            AgentRole.LINUX_INTELLIGENCE: self.linux_agent,
            AgentRole.DEVELOPER: self.dev_agent,
            AgentRole.RESEARCH_PRODUCTIVITY: self.research_agent,
            AgentRole.TOOL_EXECUTION: self.tool_agent,
            AgentRole.VERIFIER: self.verifier,
            AgentRole.RECOVERY: self.recovery,
        }

        self.active_plan: Optional[WorkflowPlan] = None
        self._is_cancelled = False

    def get_agent(self, role: AgentRole) -> Optional[BaseAgent]:
        return self._agents.get(role)

    def cancel(self):
        """Signals abort to active execution."""
        self._is_cancelled = True
        if self.active_plan:
            self.active_plan.state = WorkflowLifecycleState.CANCELLED
            self._notify_state(WorkflowLifecycleState.CANCELLED, self.active_plan, None)

    def execute_plan(self, plan: WorkflowPlan, initial_context: Optional[Dict[str, Any]] = None) -> WorkflowPlan:
        """
        Executes a WorkflowPlan to completion or failure, resolving DAG dependencies.
        """
        self.active_plan = plan
        if self._is_cancelled:
            plan.state = WorkflowLifecycleState.CANCELLED
            return plan
        self._is_cancelled = False
        context: Dict[str, Any] = initial_context or {}
        context["artifacts"] = []

        plan.state = WorkflowLifecycleState.EXECUTING
        self._notify_state(WorkflowLifecycleState.EXECUTING, plan, None)

        task_map = {t.task_id: t for t in plan.tasks}
        max_iterations = len(plan.tasks) * 4  # Prevent infinite execution loops
        iterations = 0

        while iterations < max_iterations:
            iterations += 1

            if self._is_cancelled:
                plan.state = WorkflowLifecycleState.CANCELLED
                return plan

            # Find next ready task
            ready_task = None
            all_completed = True

            for task in plan.tasks:
                if task.status in (TaskStatus.PENDING, TaskStatus.READY):
                    # Check if all dependencies are satisfied
                    deps_satisfied = True
                    for dep_id in task.depends_on:
                        dep_task = task_map.get(dep_id)
                        if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                            deps_satisfied = False
                            break

                    if deps_satisfied:
                        ready_task = task
                        all_completed = False
                        break
                    else:
                        all_completed = False

                elif task.status in (TaskStatus.IN_PROGRESS, TaskStatus.WAITING_APPROVAL):
                    all_completed = False
                elif task.status == TaskStatus.FAILED:
                    all_completed = False

            if all_completed:
                # All tasks in the plan are completed
                plan.state = WorkflowLifecycleState.COMPLETED
                self._notify_state(WorkflowLifecycleState.COMPLETED, plan, None)
                return plan

            if not ready_task:
                # No tasks are ready, but not all completed. Check for blocked/failed state
                failed_tasks = [t for t in plan.tasks if t.status == TaskStatus.FAILED]
                if failed_tasks:
                    plan.state = WorkflowLifecycleState.FAILED
                    self._notify_state(WorkflowLifecycleState.FAILED, plan, failed_tasks[0])
                    return plan
                else:
                    # Stalled or pending approval
                    break

            # Execute the ready task
            success = self._run_single_task(ready_task, context, plan)

            if not success:
                # Attempt recovery
                recovery_handled = self._handle_task_failure(ready_task, context, plan)
                if not recovery_handled:
                    plan.state = WorkflowLifecycleState.FAILED
                    self._notify_state(WorkflowLifecycleState.FAILED, plan, ready_task)
                    return plan

        return plan

    def _run_single_task(self, task: AgentTask, context: Dict[str, Any], plan: WorkflowPlan) -> bool:
        """Executes an individual task with telemetry, lifecycle notification, and artifact wiring."""
        agent = self._agents.get(task.assigned_agent)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = f"No agent registered for role: {task.assigned_agent}"
            return False

        # Prepare context inputs: auto-fill target_path for verifier from prior artifacts
        if task.assigned_agent == AgentRole.VERIFIER:
            self._notify_state(WorkflowLifecycleState.VERIFYING, plan, task)
            if not task.tool_args.get("target_path") and context.get("artifacts"):
                task.tool_args["target_path"] = context["artifacts"][-1]
        else:
            self._notify_state(WorkflowLifecycleState.EXECUTING, plan, task)

        # Check permissions before invoking tool agent
        if task.permission_level == PermissionLevel.LEVEL_3_APPROVAL_REQUIRED:
            approval_req = self.perm_mgr.request_approval(
                tool_name=task.tool_name,
                arguments=task.tool_args,
                description=task.description,
            )
            # If not yet approved, put task in WAITING_APPROVAL
            task.status = TaskStatus.WAITING_APPROVAL
            plan.state = WorkflowLifecycleState.WAITING_APPROVAL
            self._notify_state(WorkflowLifecycleState.WAITING_APPROVAL, plan, task)
            return False

        logger.info(f"Orchestrator dispatching task {task.task_id} to {agent.name} ({task.tool_name})")
        result = agent.run_task(task, context)

        # Update context with results and artifacts
        if result.success:
            context["previous_result"] = result
            if result.artifacts:
                context["artifacts"].extend(result.artifacts)
                context["last_artifact"] = result.artifacts[-1]
            return True
        else:
            return False

    def _handle_task_failure(self, task: AgentTask, context: Dict[str, Any], plan: WorkflowPlan) -> bool:
        """Invokes RecoveryAgent to determine retry, replan, approval, or abort."""
        self._notify_state(WorkflowLifecycleState.RECOVERING, plan, task)

        rec_action = self.recovery.diagnose_and_plan_recovery(
            task=task,
            verification_result=task.verification_result,
        )

        logger.info(f"RecoveryAction for {task.task_id}: {rec_action.action_type} - {rec_action.reason}")

        if rec_action.action_type == "RETRY":
            if rec_action.new_task_params:
                task.tool_args.update(rec_action.new_task_params)
            task.status = TaskStatus.PENDING
            task.error = None
            return True

        elif rec_action.action_type == "REQUEST_APPROVAL":
            task.status = TaskStatus.WAITING_APPROVAL
            plan.state = WorkflowLifecycleState.WAITING_APPROVAL
            self._notify_state(WorkflowLifecycleState.WAITING_APPROVAL, plan, task)
            return False

        elif rec_action.action_type == "REPLAN":
            self._notify_state(WorkflowLifecycleState.PLANNING, plan, task)
            self.planner.replan(plan, task, rec_action.reason)
            return True

        elif rec_action.action_type == "ABORT":
            task.status = TaskStatus.FAILED
            return False

        return False

    def _notify_state(self, state: WorkflowLifecycleState, plan: WorkflowPlan, task: Optional[AgentTask]):
        """Notifies external observers (UI, logs, audio feedback) of state transition."""
        if self.on_state_change:
            try:
                self.on_state_change(state, plan, task)
            except Exception as e:
                logger.error(f"Error in on_state_change callback: {e}")

