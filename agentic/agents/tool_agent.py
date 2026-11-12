"""
VOID Agentic OS - Tool Execution Agent
Responsible for executing registered tools with strict argument validation,
permission enforcement, output capturing, and execution telemetry.
"""

from typing import Dict, Any
from agentic.types import AgentRole, AgentTask, ToolResult
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager


class ToolExecutionAgent(BaseAgent):
    """
    Executes approved registered tools, validates arguments and permissions,
    captures outputs and errors, and prevents unauthorized system modifications.
    """

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.TOOL_EXECUTION,
            name="ToolExecutionAgent",
            description="Executes approved tools with permission and parameter validation.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        tool_name = task.tool_name
        tool_args = task.tool_args or {}

        if not tool_name:
            return ToolResult(
                tool_name="unknown",
                success=False,
                output="",
                error="Task specifies no tool_name for ToolExecutionAgent.",
                stderr="Missing tool_name in task definition.",
                exit_code=1,
            )

        if not self.tools.has_tool(tool_name):
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool '{tool_name}' is not registered in ToolRegistry.",
                stderr=f"Unregistered tool: {tool_name}",
                exit_code=1,
            )

        # Execute tool via ToolRegistry which already handles PermissionManager checks
        return self.tools.execute(tool_name, tool_args)

