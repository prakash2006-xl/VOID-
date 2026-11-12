"""
VOID Agentic OS - Multi-Agent Autonomous Operating System
Package root providing agents, permissions, orchestrator, planner, supervisor, tools, demos, and UI.
"""

from agentic.types import (
    AgentRole,
    TaskStatus,
    VALID_TASK_TRANSITIONS,
    PermissionLevel,
    WorkflowLifecycleState,
    ToolResult,
    VerificationResult,
    AgentTask,
    WorkflowPlan,
    ApprovalRequest,
    RecoveryAction,
)
from agentic.permissions import PermissionManager
from agentic.providers import AIProviderManager, parse_cloud_credentials
from agentic.tools import ToolRegistry
from agentic.planner import PlannerAgent
from agentic.orchestrator import MultiAgentOrchestrator
from agentic.supervisor import SupervisorAgent
from agentic.memory import AgentMemoryManager
from agentic.audit import AuditLogger
from agentic.demos import CompetitionDemos
from agentic.ui_components import AgentActivityCard, CompactExecutionPopup, SystemInfoPopup

__all__ = [
    "AgentRole",
    "TaskStatus",
    "VALID_TASK_TRANSITIONS",
    "PermissionLevel",
    "WorkflowLifecycleState",
    "ToolResult",
    "VerificationResult",
    "AgentTask",
    "WorkflowPlan",
    "ApprovalRequest",
    "RecoveryAction",
    "PermissionManager",
    "AIProviderManager",
    "parse_cloud_credentials",
    "ToolRegistry",
    "PlannerAgent",
    "MultiAgentOrchestrator",
    "SupervisorAgent",
    "AgentMemoryManager",
    "AuditLogger",
    "CompetitionDemos",
    "AgentActivityCard",
    "CompactExecutionPopup",
    "SystemInfoPopup",
]
