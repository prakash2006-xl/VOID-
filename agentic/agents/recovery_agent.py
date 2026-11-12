"""
VOID Agentic OS - Recovery Agent
Analyzes execution and verification failures, classifies root causes,
formulates structured recovery plans, bounds retries to max 2, and prevents infinite loops.
"""

from typing import Dict, Any, Optional
import logging
from agentic.types import (
    AgentRole,
    AgentTask,
    ToolResult,
    VerificationResult,
    RecoveryAction,
)
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager

logger = logging.getLogger("VOID.Agentic.Recovery")


class RecoveryAgent(BaseAgent):
    """
    Diagnoses failures, selects appropriate recovery strategies (Retry, Replan, Request Approval, Abort),
    and enforces maximum retry limits.
    """

    MAX_RETRIES = 2

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.RECOVERY,
            name="RecoveryAgent",
            description="Diagnoses task failures, computes recovery strategies, and bounds retries.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        """
        Takes a failed task or failed verification and computes a RecoveryAction.
        """
        failed_task: Optional[AgentTask] = context.get("failed_task")
        verification_result: Optional[VerificationResult] = context.get("verification_result")

        if not failed_task:
            return ToolResult(
                tool_name="diagnose_failure",
                success=False,
                output="",
                error="No failed_task provided in context for RecoveryAgent.",
                stderr="Missing failed_task",
                exit_code=1,
            )

        recovery_action = self.diagnose_and_plan_recovery(failed_task, verification_result)

        return ToolResult(
            tool_name="diagnose_failure",
            success=True,
            output=f"Recovery strategy: {recovery_action.action_type.upper()} - {recovery_action.reason}",
            metadata={
                "action_type": recovery_action.action_type,
                "reason": recovery_action.reason,
                "target_agent": recovery_action.target_agent.value if recovery_action.target_agent else None,
                "retry_count": failed_task.retry_count,
            },
        )

    def diagnose_and_plan_recovery(
        self,
        task: AgentTask,
        verification_result: Optional[VerificationResult] = None,
    ) -> RecoveryAction:
        """
        Classifies the failure and determines the safe next step.
        """
        # 1. Enforce Max Retry Bound
        if task.retry_count >= self.MAX_RETRIES:
            logger.warning(f"Task {task.task_id} reached maximum retries ({self.MAX_RETRIES}). Aborting task.")
            return RecoveryAction(
                action_type="ABORT",
                reason=f"Task exceeded maximum retry limit of {self.MAX_RETRIES}. Halting to prevent infinite loop.",
                target_agent=AgentRole.SUPERVISOR,
            )

        error_message = (task.error or "").lower()
        if verification_result and verification_result.failure_reason:
            error_message += " " + verification_result.failure_reason.lower()
        if verification_result and verification_result.evidence:
            error_message += " " + verification_result.evidence.lower()

        # 2. Permission Denied / Authorization needed
        if "permission denied" in error_message or "level 3" in error_message or "forbidden" in error_message:
            if "level 4" in error_message or "system files" in error_message or "root" in error_message:
                return RecoveryAction(
                    action_type="ABORT",
                    reason="Attempted operation violates security policy (Level 4 system boundary). Halting permanently.",
                    target_agent=AgentRole.SUPERVISOR,
                )
            return RecoveryAction(
                action_type="REQUEST_APPROVAL",
                reason="Task requires user approval before proceeding (Level 3 action).",
                target_agent=AgentRole.SUPERVISOR,
                new_task_params={"requires_user_confirmation": True},
            )

        # 3. Python Syntax Error
        if "syntaxerror" in error_message or "invalid syntax" in error_message or "syntax_error" in error_message:
            task.retry_count += 1
            return RecoveryAction(
                action_type="RETRY",
                reason=f"Detected Python syntax error. Requesting DeveloperAgent fix (Attempt {task.retry_count}/{self.MAX_RETRIES}).",
                target_agent=AgentRole.DEVELOPER,
                new_task_params={"diagnostics": "Syntax error identified. Check line numbers and indentation."},
            )

        # 4. Test Failures / Subprocess Non-Zero
        if "tests_failed" in error_message or "assertionerror" in error_message or "failed with exit_code" in error_message:
            task.retry_count += 1
            return RecoveryAction(
                action_type="RETRY",
                reason=f"Test assertion failed. Instructing DeveloperAgent to patch code and re-test (Attempt {task.retry_count}/{self.MAX_RETRIES}).",
                target_agent=AgentRole.DEVELOPER,
                new_task_params={"diagnostics": "Unit test failed. Inspect assertions and test outputs."},
            )

        # 5. File Empty or Missing Output Artifact
        if "empty_file" in error_message or "file_not_found" in error_message:
            task.retry_count += 1
            return RecoveryAction(
                action_type="RETRY",
                reason=f"Expected output file missing or empty. Retrying generation (Attempt {task.retry_count}/{self.MAX_RETRIES}).",
                target_agent=task.assigned_agent or AgentRole.TOOL_EXECUTION,
            )

        # 6. Timeout
        if "timeout" in error_message or "timed out" in error_message:
            task.retry_count += 1
            return RecoveryAction(
                action_type="RETRY",
                reason=f"Execution timed out. Retrying with extended timeout buffer (Attempt {task.retry_count}/{self.MAX_RETRIES}).",
                target_agent=task.assigned_agent or AgentRole.TOOL_EXECUTION,
                new_task_params={"timeout_sec": 60},
            )

        # 7. Unclassified or generic error: attempt 1 retry or abort
        if task.retry_count < 1:
            task.retry_count += 1
            return RecoveryAction(
                action_type="RETRY",
                reason=f"Initial execution failed. Retrying once (Attempt {task.retry_count}/{self.MAX_RETRIES}): {task.error[:100]}",
                target_agent=task.assigned_agent or AgentRole.TOOL_EXECUTION,
            )

        return RecoveryAction(
            action_type="ABORT",
            reason=f"Unable to recover automatically from error: {task.error[:150]}",
            target_agent=AgentRole.SUPERVISOR,
        )

