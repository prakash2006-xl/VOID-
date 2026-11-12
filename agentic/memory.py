"""
VOID Agentic OS - Agent Memory Manager
Maintains persistent task and workflow memory in memory/agent_tasks.json and
memory/workflow_history.json while preserving existing facts.json and episodic memories.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from agentic.types import WorkflowPlan, AgentTask

logger = logging.getLogger("VOID.Agentic.Memory")


class AgentMemoryManager:
    """
    Persists and retrieves multi-agent execution plans, task states, and generated artifacts.
    Guarantees zero interference with existing memory/facts.json.
    """

    def __init__(self, memory_dir: Optional[str] = None):
        if not memory_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.memory_dir = os.path.join(base_dir, "memory")
        else:
            self.memory_dir = memory_dir

        os.makedirs(self.memory_dir, exist_ok=True)
        self.tasks_file = os.path.join(self.memory_dir, "agent_tasks.json")
        self.history_file = os.path.join(self.memory_dir, "workflow_history.json")

        self._ensure_storage()

    def _ensure_storage(self):
        """Initializes storage files if absent."""
        if not os.path.exists(self.tasks_file):
            self._save_json(self.tasks_file, {"tasks": {}})
        if not os.path.exists(self.history_file):
            self._save_json(self.history_file, {"workflows": []})

    def _load_json(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, path: str, data: Dict[str, Any]):
        temp_path = f"{path}.tmp_{os.getpid()}"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(temp_path, path)
        except Exception as e:
            logger.error(f"Failed to atomically write JSON to {path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def save_task(self, task: AgentTask):
        """Records task state into agent_tasks.json."""
        data = self._load_json(self.tasks_file)
        if "tasks" not in data:
            data["tasks"] = {}

        data["tasks"][task.task_id] = {
            "task_id": task.task_id,
            "agent": task.assigned_agent.value,
            "description": task.description,
            "status": task.status.value,
            "tool_name": task.tool_name,
            "artifacts": task.result.artifacts if task.result else [],
            "error": task.error,
            "duration_sec": task.execution_time_sec,
            "updated_at": time.time(),
        }
        self._save_json(self.tasks_file, data)

    def record_workflow_completion(self, plan: WorkflowPlan):
        """Appends a finished workflow to workflow_history.json."""
        data = self._load_json(self.history_file)
        if "workflows" not in data:
            data["workflows"] = []

        artifacts = []
        for t in plan.tasks:
            if t.result and t.result.artifacts:
                artifacts.extend(t.result.artifacts)

        record = {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "state": plan.state.value,
            "task_count": len(plan.tasks),
            "artifacts": list(set(artifacts)),
            "completed_at": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "agent": t.assigned_agent.value,
                    "status": t.status.value,
                    "duration_sec": t.execution_time_sec,
                }
                for t in plan.tasks
            ],
        }
        data["workflows"].append(record)
        # Keep recent 200 workflows
        if len(data["workflows"]) > 200:
            data["workflows"] = data["workflows"][-200:]

        self._save_json(self.history_file, data)

    def get_recent_workflows(self, count: int = 5) -> List[Dict[str, Any]]:
        """Returns the most recent completed workflows."""
        data = self._load_json(self.history_file)
        workflows = data.get("workflows", [])
        return workflows[-count:]

