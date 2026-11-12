"""
VOID Agentic OS - Base Agent Class
Provides standardized lifecycle, telemetry, provider access, and tool invocation for all specialized agents.
"""

from typing import Dict, Any, List, Optional
import time
import logging
from agentic.types import AgentRole, AgentTask, TaskStatus, ToolResult
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager

logger = logging.getLogger("VOID.Agentic.Base")


class BaseAgent:
    """Base class for all specialized agents in the VOID Multi-Agent system."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        tools: ToolRegistry,
        provider_manager: AIProviderManager,
    ):
        self.role = role
        self.name = name
        self.description = description
        self.tools = tools
        self.provider_mgr = provider_manager
        self.history: List[Dict[str, Any]] = []

    def get_role(self) -> AgentRole:
        return self.role

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def run_task(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        """
        Executes an assigned task with full execution tracking and safety checks.
        Must be implemented by subclasses.
        """
        start_time = time.time()
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_agent = self.role

        try:
            result = self._execute(task, context)
            task.execution_time_sec = round(time.time() - start_time, 3)
            task.result = result

            if result.success:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
                task.error = result.stderr or result.output

            self.history.append({
                "task_id": task.task_id,
                "role": self.role.value,
                "success": result.success,
                "duration": task.execution_time_sec,
                "timestamp": time.time(),
            })
            return result
        except Exception as e:
            task.execution_time_sec = round(time.time() - start_time, 3)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Agent {self.name} encountered an uncaught error on task {task.task_id}: {e}", exc_info=True)
            return ToolResult(
                tool_name=f"{self.name}.run_task",
                success=False,
                output="",
                error=str(e),
                stderr=str(e),
                exit_code=1,
                execution_time_sec=task.execution_time_sec,
            )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        """Subclasses override this to implement agent-specific logic."""
        raise NotImplementedError("Subclasses must implement _execute")

