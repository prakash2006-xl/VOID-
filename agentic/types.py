#!/usr/bin/env python3
"""
VOID Agentic OS — Type Definitions & State Contracts
Core data types, enumerations, and dataclasses for the multi-agent orchestration layer.
Includes robust aliasing to support all specialized agents, planners, and test suites.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    LINUX_INTEL = "linux_intel"
    LINUX_INTELLIGENCE = "linux_intel"
    DEVELOPER = "developer"
    RESEARCH = "research"
    RESEARCH_PRODUCTIVITY = "research"
    TOOL_EXEC = "tool_exec"
    TOOL_EXECUTION = "tool_exec"
    VERIFIER = "verifier"
    RECOVERY = "recovery"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    IN_PROGRESS = "running"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERED = "recovered"


class PermissionLevel(int, Enum):
    LEVEL_1_READONLY = 1         # Read-only inspection, safe to auto-execute
    LEVEL_1_READ_ONLY = 1
    LEVEL_2_REVERSIBLE = 2       # Workspace-bounded reversible actions
    LEVEL_2_REVERSIBLE_USER_ACTION = 2
    LEVEL_3_APPROVAL = 3         # Approval required before execution
    LEVEL_3_APPROVAL_REQUIRED = 3
    LEVEL_4_FORBIDDEN = 4        # Strictly prohibited system modifications


class WorkflowLifecycleState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DELEGATING = "delegating"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: Any = None
    output: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0
    execution_time_sec: float = 0.0
    raw_stdout: str = ""
    raw_stderr: str = ""
    stderr: str = ""
    exit_code: int = 0
    artifacts_created: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.output and self.raw_stdout:
            self.output = self.raw_stdout
        elif not self.raw_stdout and self.output:
            self.raw_stdout = self.output
        if self.data is None and self.output:
            self.data = self.output

        if not self.stderr and self.raw_stderr:
            self.stderr = self.raw_stderr
        elif not self.raw_stderr and self.stderr:
            self.raw_stderr = self.stderr

        if not self.artifacts and self.artifacts_created:
            self.artifacts = list(self.artifacts_created)
        elif not self.artifacts_created and self.artifacts:
            self.artifacts_created = list(self.artifacts)

        if not self.execution_time_sec and self.duration_ms:
            self.execution_time_sec = self.duration_ms / 1000.0
        elif not self.duration_ms and self.execution_time_sec:
            self.duration_ms = self.execution_time_sec * 1000.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": str(self.data) if self.data is not None else None,
            "output": self.output,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "artifacts_created": self.artifacts_created,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    task_id: str = ""
    verified: bool = False
    evidence: str = ""
    checks_performed: list[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "verified": self.verified,
            "evidence": self.evidence,
            "checks_performed": self.checks_performed,
            "failure_reason": self.failure_reason,
            "details": self.details,
        }


@dataclass
class AgentTask:
    id: str = field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    task_id: Optional[str] = None
    parent_id: Optional[str] = None
    goal: str = ""
    description: Optional[str] = None
    agent_role: AgentRole = AgentRole.TOOL_EXEC
    assigned_agent: Optional[AgentRole] = None
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    permission_level: PermissionLevel = PermissionLevel.LEVEL_1_READONLY
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[ToolResult] = None
    verification: Optional[VerificationResult] = None
    verification_result: Optional[VerificationResult] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    timeout_sec: float = 30.0
    execution_time_sec: float = 0.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.task_id and not self.id:
            self.id = self.task_id
        elif self.id and not self.task_id:
            self.task_id = self.id

        if self.description and not self.goal:
            self.goal = self.description
        elif self.goal and not self.description:
            self.description = self.goal

        if self.assigned_agent and not self.agent_role:
            self.agent_role = self.assigned_agent
        elif self.agent_role and not self.assigned_agent:
            self.assigned_agent = self.agent_role

        if self.verification_result and not self.verification:
            self.verification = self.verification_result
        elif self.verification and not self.verification_result:
            self.verification_result = self.verification

    def is_ready(self, completed_task_ids: set[str]) -> bool:
        return self.status == TaskStatus.PENDING and all(dep in completed_task_ids for dep in self.depends_on)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "parent_id": self.parent_id,
            "goal": self.goal,
            "description": self.description,
            "agent_role": self.agent_role.value if self.agent_role else None,
            "assigned_agent": self.assigned_agent.value if self.assigned_agent else None,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "depends_on": self.depends_on,
            "permission_level": self.permission_level.value,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "verification": self.verification.to_dict() if self.verification else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "duration": round(self.completed_at - self.started_at, 2) if (self.completed_at and self.started_at) else None,
        }


@dataclass
class WorkflowPlan:
    plan_id: str = field(default_factory=lambda: f"plan_{uuid4().hex[:8]}")
    user_goal: str = ""
    goal: Optional[str] = None
    tasks: list[AgentTask] = field(default_factory=list)
    state: WorkflowLifecycleState = WorkflowLifecycleState.IDLE
    estimated_duration_sec: float = 0.0
    risks: list[str] = field(default_factory=list)
    requires_approval: bool = False
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.goal and not self.user_goal:
            self.user_goal = self.goal
        elif self.user_goal and not self.goal:
            self.goal = self.user_goal

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        for t in self.tasks:
            if t.id == task_id or t.task_id == task_id:
                return t
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "user_goal": self.user_goal,
            "goal": self.goal,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "task_count": len(self.tasks),
            "tasks": [t.to_dict() for t in self.tasks],
            "estimated_duration_sec": self.estimated_duration_sec,
            "risks": self.risks,
            "requires_approval": self.requires_approval,
        }


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: f"req_{uuid4().hex[:8]}")
    task_id: str = ""
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    action_description: str = ""
    description: Optional[str] = None
    risk_factors: list[str] = field(default_factory=list)
    affected_targets: list[str] = field(default_factory=list)
    requested_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, approved, rejected, expired
    timeout_sec: float = 120.0

    def __post_init__(self):
        if self.description and not self.action_description:
            self.action_description = self.description
        elif self.action_description and not self.description:
            self.description = self.action_description

    def is_expired(self) -> bool:
        return (time.time() - self.requested_at) > self.timeout_sec


@dataclass
class RecoveryAction:
    task_id: str = ""
    strategy: str = "retry"  # retry, alternate_tool, fallback_value, replan, abort
    action_type: str = "RETRY"
    retry_allowed: bool = True
    replan_required: bool = False
    explanation: str = ""
    reason: Optional[str] = None
    target_agent: Optional[AgentRole] = None
    new_task_params: Optional[dict[str, Any]] = None
    fallback_args: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if self.reason and not self.explanation:
            self.explanation = self.reason
        elif self.explanation and not self.reason:
            self.reason = self.explanation

        if self.action_type and self.strategy == "retry":
            self.strategy = self.action_type.lower()
        elif self.strategy and self.action_type == "RETRY":
            self.action_type = self.strategy.upper()
