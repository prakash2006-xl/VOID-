"""
VOID Agentic OS - Audit Logger
Provides append-only structured JSONL logging for agent executions, tool calls,
verification evidence, and security-relevant actions with secret masking.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("VOID.Agentic.Audit")


class AuditLogger:
    """
    Appends structured execution events to logs/agentic_audit.jsonl with strict secret masking.
    """

    def __init__(self, log_path: Optional[str] = None):
        if not log_path:
            # Default to VOID repository logs/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.log_path = os.path.join(log_dir, "agentic_audit.jsonl")
        else:
            self.log_path = log_path
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(
        self,
        event_type: str,
        agent_role: str,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_sec: float = 0.0,
    ):
        """Appends a masked JSON record to the audit file."""
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "agent_role": agent_role,
            "task_id": task_id,
            "success": success,
            "duration_sec": round(duration_sec, 3),
            "details": self._mask_secrets(details or {}),
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to audit log {self.log_path}: {e}")

    def _mask_secrets(self, data: Any) -> Any:
        """Recursively masks API keys, bearer tokens, and passwords."""
        if isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                lower_k = k.lower()
                if any(sec in lower_k for sec in ("key", "secret", "token", "password", "auth")):
                    if isinstance(v, str) and len(v) > 8:
                        masked[k] = f"{v[:3]}...{v[-4:]}"
                    else:
                        masked[k] = "******"
                else:
                    masked[k] = self._mask_secrets(v)
            return masked
        elif isinstance(data, list):
            return [self._mask_secrets(item) for item in data]
        return data

