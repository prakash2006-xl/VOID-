#!/usr/bin/env python3
"""
VOID Agentic OS — Autonomy & 4-Tier Permission Manager
Enforces strict security boundaries, approval queues, and workspace isolation.
"""

from __future__ import annotations
import os
import re
import time
from pathlib import Path
from typing import Any, Optional
from agentic.types import PermissionLevel, ApprovalRequest

# Explicitly Approved Workspaces (User-Level Only)
APPROVED_WORKSPACES = [
    Path(os.path.expanduser("~/Documents")),
    Path(os.path.expanduser("~/Documents/Reports")),
    Path(os.path.expanduser("~/Documents/Notes")),
    Path(os.path.expanduser("~/Documents/Projects")),
    Path("/run/media/prakash/TR_39/VOID/memory"),
    Path("/run/media/prakash/TR_39/VOID/logs"),
    Path("/tmp/void_sandbox"),
]

# Forbidden Patterns (Level 4: Strictly Prohibited)
FORBIDDEN_COMMANDS = [
    "sudo", "su", "pkexec", "doas",
    "rm -rf /", "mkfs", "dd", "fdisk", "parted",
    "chmod -R 777 /", "chown -R", "setenforce", "iptables",
    "grub", "systemctl poweroff", "reboot", "init 0"
]

FORBIDDEN_PATHS = [
    "/etc", "/boot", "/sys", "/proc", "/root",
    "/usr/bin", "/usr/sbin", "/lib", "/lib64", "/var/log"
]


class PermissionManager:
    """4-Tier Autonomous Permission & Approval Manager."""

    def __init__(self) -> None:
        self.pending_approvals: dict[str, ApprovalRequest] = {}
        self.approval_history: list[dict[str, Any]] = []
        # Ensure approved directories exist
        for ws in APPROVED_WORKSPACES:
            try:
                ws.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    def is_path_in_approved_workspace(self, target_path: str | Path) -> bool:
        """Verifies if target path is strictly contained inside approved user workspaces."""
        try:
            resolved = Path(target_path).resolve()
            # Special exemption for user Documents subfolders
            user_docs = Path(os.path.expanduser("~/Documents")).resolve()
            if resolved == user_docs or user_docs in resolved.parents:
                return True
            for ws in APPROVED_WORKSPACES:
                ws_res = ws.resolve()
                if resolved == ws_res or ws_res in resolved.parents:
                    return True
            return False
        except Exception:
            return False

    def evaluate_tool_permission(
        self,
        tool_name: str,
        args: dict[str, Any],
        declared_level: PermissionLevel = PermissionLevel.LEVEL_1_READONLY
    ) -> tuple[PermissionLevel, bool, str]:
        """
        Evaluates tool execution against 4-tier security doctrine.
        Returns: (PermissionLevel, is_allowed_autonomously, reason)
        """
        # 1. Level 4 Forbidden Check: Commands and Paths
        # Check command arguments against dangerous commands using word boundaries
        cmd_args = [v for k, v in args.items() if k in ("test_command", "cmd", "command", "exec") and isinstance(v, str)]
        for cmd_str in cmd_args:
            cmd_lower = cmd_str.lower()
            for forb_cmd in FORBIDDEN_COMMANDS:
                if re.search(r"\b" + re.escape(forb_cmd) + r"\b", cmd_lower) or forb_cmd in cmd_lower:
                    return (
                        PermissionLevel.LEVEL_4_FORBIDDEN,
                        False,
                        f"Forbidden operation: Detected dangerous command '{forb_cmd}' in command arguments."
                    )

        # Check path arguments against privileged system root paths
        path_args = [v for k, v in args.items() if k in ("path", "filepath", "target_path", "directory", "working_dir", "project_dir") and isinstance(v, str)]
        for p_str in path_args:
            resolved_p = str(Path(os.path.expanduser(p_str)).resolve())
            for forb_path in FORBIDDEN_PATHS:
                if resolved_p == forb_path or resolved_p.startswith(forb_path + "/"):
                    return (
                        PermissionLevel.LEVEL_4_FORBIDDEN,
                        False,
                        f"Forbidden operation: Attempted access to privileged system root path '{p_str}'."
                    )

        # 2. Level 3 Approval Checks: Deletions, overwriting non-workspace files, external messages, package changes
        is_deletion = any(act in str(args.get("action", "")).lower() for act in ["delete", "remove", "drop"])
        target_file = args.get("filepath") or args.get("filename") or args.get("path")
        file_exists = bool(Path(os.path.expanduser(target_file)).exists()) if target_file else False
        is_overwrite_existing = file_exists and bool(args.get("overwrite", False))

        # Overwrites within project workspaces with backups are Level 2; outside project space requires Level 3
        is_high_risk_overwrite = False
        if is_overwrite_existing and target_file:
            resolved_target = str(Path(os.path.expanduser(target_file)).resolve())
            if not any(p in resolved_target for p in ["/Documents/Projects", "/tmp/void_sandbox", "/Documents/Notes"]):
                is_high_risk_overwrite = True

        is_external_comm = tool_name in ["send_email", "post_message", "publish_content"]
        is_config_change = "config" in tool_name or tool_name == "set_api_key"

        if is_deletion or is_high_risk_overwrite or is_external_comm or is_config_change or declared_level == PermissionLevel.LEVEL_3_APPROVAL:
            return (
                PermissionLevel.LEVEL_3_APPROVAL,
                False,
                f"Approval Required: Operation '{tool_name}' performs destructive, external, or security-sensitive actions."
            )

        # 3. Level 2 Reversible User-Level Actions (Workspace check)
        if declared_level == PermissionLevel.LEVEL_2_REVERSIBLE:
            if target_file:
                if not self.is_path_in_approved_workspace(target_file):
                    return (
                        PermissionLevel.LEVEL_3_APPROVAL,
                        False,
                        f"Approval Required: Target path '{target_file}' is outside standard approved workspaces."
                    )
            return (
                PermissionLevel.LEVEL_2_REVERSIBLE,
                True,
                "Authorized: Reversible user action within approved workspace."
            )

        # 4. Level 1 Read-Only
        return (
            PermissionLevel.LEVEL_1_READONLY,
            True,
            "Authorized: Read-only inspection."
        )

    def check_tool_permission(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Convenience method returning a dictionary representation of the permission evaluation."""
        level, allowed, reason = self.evaluate_tool_permission(tool_name, args)
        return {"level": level, "allowed": allowed, "reason": reason}

    def request_approval(
        self,
        task_id: str = "",
        action_description: str = "",
        risk_factors: Optional[list[str]] = None,
        affected_targets: Optional[list[str]] = None,
        timeout_sec: float = 120.0,
        tool_name: str = "",
        arguments: Optional[dict[str, Any]] = None,
        description: str = "",
    ) -> ApprovalRequest:
        """Enqueues an approval request for user authorization."""
        desc = description or action_description
        if not desc and tool_name:
            desc = f"Execute tool '{tool_name}'"

        targets = affected_targets or []
        if arguments and not targets:
            if "path" in arguments:
                targets.append(str(arguments["path"]))
            elif "target_path" in arguments:
                targets.append(str(arguments["target_path"]))

        req = ApprovalRequest(
            task_id=task_id or f"task_{int(time.time())}",
            tool_name=tool_name,
            arguments=arguments or {},
            action_description=desc,
            description=desc,
            risk_factors=risk_factors or ["High-impact / Level 3 action"],
            affected_targets=targets,
            timeout_sec=timeout_sec,
        )
        self.pending_approvals[req.request_id] = req
        return req

    def resolve_approval(self, request_id: str, approved: bool) -> bool:
        """Resolves a pending approval request."""
        req = self.pending_approvals.get(request_id)
        if not req:
            return False
        if req.is_expired():
            req.status = "expired"
            self.approval_history.append({"request_id": request_id, "status": "expired", "time": time.time()})
            return False
        req.status = "approved" if approved else "rejected"
        self.approval_history.append({
            "request_id": request_id,
            "task_id": req.task_id,
            "status": req.status,
            "action": req.action_description,
            "time": time.time()
        })
        return approved

    def confirm_approval(self, request_id: str) -> bool:
        """Approves and marks the pending request as approved."""
        return self.resolve_approval(request_id, approved=True)

    def reject_approval(self, request_id: str) -> bool:
        """Rejects the pending request."""
        return self.resolve_approval(request_id, approved=False)

    def get_pending_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Retrieves a specific pending approval request."""
        return self.pending_approvals.get(request_id)

    def get_all_pending(self) -> list[ApprovalRequest]:
        """Returns all currently active approval requests."""
        return [r for r in self.pending_approvals.values() if r.status == "pending"]

    def cancel_all_pending(self) -> None:
        """Cancels all active approval requests immediately (e.g. on user abort)."""
        for req in self.pending_approvals.values():
            req.status = "cancelled"
            self.approval_history.append({"request_id": req.request_id, "status": "cancelled", "time": time.time()})
        self.pending_approvals.clear()
