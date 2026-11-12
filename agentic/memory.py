"""
VOID Agentic OS - Agent Memory Manager with High Memory Thought & 7-Day Rolling Retention
Maintains:
1. memory/agent_tasks.json & memory/workflow_history.json
2. 7-Day Rolling Episodic Memory in memory/weekly_episodes.jsonl
3. Weekly Memory Digest Synthesis in memory/weekly_summaries/week_YYYY_WW.json & .md
4. Contextual Deep Retrieval to recall and answer using weekly memory files.
Preserves existing memory/facts.json and episodic memories with zero corruption.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from agentic.types import WorkflowPlan, AgentTask, TaskStatus

logger = logging.getLogger("VOID.Agentic.Memory")

SEVEN_DAYS_SECONDS = 7 * 24 * 3600  # 604,800 seconds (168 hours)


class AgentMemoryManager:
    """
    Manages persistent multi-agent memory, 7-day rolling thought retention,
    and weekly memory file synthesis for deep recall and contextual continuity.
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
        self.episodes_file = os.path.join(self.memory_dir, "weekly_episodes.jsonl")
        self.summaries_dir = os.path.join(self.memory_dir, "weekly_summaries")
        os.makedirs(self.summaries_dir, exist_ok=True)

        self._ensure_storage()

    def _ensure_storage(self):
        """Initializes storage files if absent."""
        if not os.path.exists(self.tasks_file):
            self._save_json(self.tasks_file, {"tasks": {}})
        if not os.path.exists(self.history_file):
            self._save_json(self.history_file, {"workflows": []})
        if not os.path.exists(self.episodes_file):
            with open(self.episodes_file, "a", encoding="utf-8") as f:
                pass

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

    # -----------------------------------------------------------------------
    # Task & Workflow State Storage (Preserved)
    # -----------------------------------------------------------------------
    def save_task(self, task: AgentTask):
        """Records task state into agent_tasks.json."""
        data = self._load_json(self.tasks_file)
        if "tasks" not in data:
            data["tasks"] = {}

        data["tasks"][task.task_id] = {
            "task_id": task.task_id,
            "agent": task.assigned_agent.value if task.assigned_agent else "unknown",
            "description": task.description or task.goal,
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
            "goal": plan.goal or plan.user_goal,
            "state": plan.state.value if hasattr(plan.state, "value") else str(plan.state),
            "task_count": len(plan.tasks),
            "artifacts": list(set(artifacts)),
            "completed_at": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tasks": [
                {
                    "task_id": t.task_id or t.id,
                    "agent": t.assigned_agent.value if t.assigned_agent else "unknown",
                    "status": t.status.value,
                    "duration_sec": t.execution_time_sec,
                }
                for t in plan.tasks
            ],
        }
        data["workflows"].append(record)
        if len(data["workflows"]) > 200:
            data["workflows"] = data["workflows"][-200:]

        self._save_json(self.history_file, data)

        # Automatically record a High Memory Thought episode for 7-day retention
        self.record_high_memory_thought(
            query=plan.goal or plan.user_goal,
            thought_summary=f"Executed {len(plan.tasks)} agent tasks with state {record['state']}.",
            plan_id=plan.plan_id,
            outcome=f"Completed {sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)} tasks successfully.",
            artifacts=list(set(artifacts)),
            tags=["workflow", "multi-agent"]
        )

    def get_recent_workflows(self, count: int = 5) -> List[Dict[str, Any]]:
        """Returns the most recent completed workflows."""
        data = self._load_json(self.history_file)
        workflows = data.get("workflows", [])
        return workflows[-count:]

    # -----------------------------------------------------------------------
    # 7-Day Rolling Episodic Memory & High Memory Thought Engine
    # -----------------------------------------------------------------------
    def record_high_memory_thought(
        self,
        query: str,
        thought_summary: str,
        plan_id: str = "",
        outcome: str = "",
        artifacts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Appends a rich thought episode to the 7-day rolling memory store.
        Captures reasoning trace, intent, outcome, and generated artifacts.
        """
        now = time.time()
        week_num = time.strftime("%Y-W%W", time.gmtime(now))
        episode = {
            "timestamp": now,
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
            "day_name": time.strftime("%A", time.localtime(now)),
            "week_id": week_num,
            "plan_id": plan_id,
            "query": query,
            "thought_summary": thought_summary,
            "outcome": outcome,
            "artifacts": artifacts or [],
            "tags": tags or [],
        }

        try:
            with open(self.episodes_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(episode) + "\n")
        except Exception as e:
            logger.error(f"Failed to append episode to {self.episodes_file}: {e}")

        return episode

    def get_7day_episodes(self) -> List[Dict[str, Any]]:
        """
        Reads and returns all episodes recorded in the past 7 days (168 hours).
        Automatically filters out older records.
        """
        cutoff = time.time() - SEVEN_DAYS_SECONDS
        episodes = []
        if not os.path.exists(self.episodes_file):
            return []

        try:
            with open(self.episodes_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ep = json.loads(line)
                        if ep.get("timestamp", 0) >= cutoff:
                            episodes.append(ep)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error reading {self.episodes_file}: {e}")

        return episodes

    def generate_weekly_memory_file(self) -> str:
        """
        Analyzes the past 7 days of memory thoughts, synthesizes a complete
        weekly memory report, and saves it in memory/weekly_summaries/ as both
        JSON (machine-readable) and Markdown (human-readable).
        Returns the path to the generated Markdown weekly memory file.
        """
        episodes = self.get_7day_episodes()
        now = time.time()
        week_id = time.strftime("%Y_W%W", time.localtime(now))
        start_date = time.strftime("%Y-%m-%d", time.localtime(now - SEVEN_DAYS_SECONDS))
        end_date = time.strftime("%Y-%m-%d", time.localtime(now))

        # Aggregate statistics
        total_queries = len(episodes)
        all_artifacts = []
        topics_covered = set()
        activity_by_day: Dict[str, int] = {}

        for ep in episodes:
            day = ep.get("day_name", "Unknown")
            activity_by_day[day] = activity_by_day.get(day, 0) + 1
            for art in ep.get("artifacts", []):
                all_artifacts.append(art)
            for tag in ep.get("tags", []):
                topics_covered.add(tag)

        unique_artifacts = list(dict.fromkeys(all_artifacts))

        # 1. Save Structured JSON Digest
        json_path = os.path.join(self.summaries_dir, f"weekly_memory_{week_id}.json")
        digest_data = {
            "week_id": week_id,
            "period": f"{start_date} to {end_date}",
            "generated_at": time.time(),
            "total_episodes": total_queries,
            "activity_by_day": activity_by_day,
            "topics": list(topics_covered),
            "artifacts_created": unique_artifacts,
            "episodes": episodes,
        }
        self._save_json(json_path, digest_data)

        # 2. Save Human-Readable & Searchable Markdown Digest
        md_path = os.path.join(self.summaries_dir, f"weekly_memory_{week_id}.md")
        lines = [
            f"# VOID Weekly Memory Digest — Week {week_id}",
            f"*Retention Period: {start_date} to {end_date} (Last 7 Days)*",
            f"*Generated by VOID High Memory Engine on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "## 1. Executive Summary & Weekly Highlights",
            f"- **Total Interactions & Thought Traces:** {total_queries}",
            f"- **Distinct Deliverables & Artifacts Produced:** {len(unique_artifacts)}",
            f"- **Active Days:** {', '.join(f'{d} ({c})' for d, c in activity_by_day.items()) or 'None recorded'}\n",
            "## 2. Deliverables & Files Created This Week",
        ]

        if unique_artifacts:
            for art in unique_artifacts:
                lines.append(f"- `{art}` ({'Exists' if os.path.exists(art) else 'Archived'})")
        else:
            lines.append("- *No persistent files created during this window.*")

        lines.extend([
            "\n## 3. Chronological Thought Log (Past 7 Days)",
        ])

        if episodes:
            for i, ep in enumerate(episodes, 1):
                lines.append(f"### Episode {i}: [{ep.get('day_name', '')} {ep.get('iso_time', '')}]")
                lines.append(f"- **User Intent / Goal:** {ep.get('query', '')}")
                lines.append(f"- **Reasoning & Execution:** {ep.get('thought_summary', '')}")
                if ep.get("outcome"):
                    lines.append(f"- **Outcome:** {ep.get('outcome', '')}")
                if ep.get("artifacts"):
                    lines.append(f"- **Artifacts:** {', '.join(ep.get('artifacts', []))}")
                lines.append("")
        else:
            lines.append("- *No episodes logged in the past 7 days.*")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            logger.error(f"Failed to write weekly memory markdown {md_path}: {e}")

        logger.info(f"Weekly memory file generated successfully at {md_path}")
        return md_path

    def query_weekly_memory(self, search_query: str) -> Dict[str, Any]:
        """
        Deep retrieval engine: searches across the past 7 days of episodes and weekly digests.
        Extracts relevant thought logs, files created, and facts to answer user queries with full historical context.
        """
        episodes = self.get_7day_episodes()
        search_lower = search_query.lower()
        search_tokens = [w for w in search_lower.split() if len(w) > 2]

        is_general_recap = any(p in search_lower for p in [
            "this week", "weekly recap", "what did we do", "recall this week",
            "summary of the week", "recent work", "past week", "weekly summary",
            "recap", "all work", "everything"
        ])

        matched_episodes = []
        matched_artifacts = set()

        for ep in episodes:
            score = 0
            ep_text = f"{ep.get('query', '')} {ep.get('thought_summary', '')} {ep.get('outcome', '')} {' '.join(ep.get('artifacts', []))}".lower()
            if is_general_recap:
                score = 1
            else:
                for token in search_tokens:
                    if token in ep_text:
                        score += 1
            if score > 0 or not search_tokens:
                matched_episodes.append((score, ep))
                for art in ep.get("artifacts", []):
                    matched_artifacts.add(art)

        # Sort by relevance score
        matched_episodes.sort(key=lambda x: x[0], reverse=True)
        top_matches = [ep for _, ep in matched_episodes[:8]]

        # Synthesize context answer
        if top_matches:
            summary_points = []
            for m in top_matches[:5]:
                summary_points.append(f"• On {m.get('day_name')}: {m.get('query')} (Outcome: {m.get('outcome')})")

            answer = (
                f"Based on your 7-day memory traces, here is what we worked on:\n"
                + "\n".join(summary_points)
            )
            if matched_artifacts:
                answer += f"\n\nFiles referenced: {', '.join(list(matched_artifacts)[:4])}"
        else:
            answer = (
                f"I reviewed your 7-day memory logs ({len(episodes)} total episodes), "
                f"but found no direct match for '{search_query}'. You can say 'generate weekly memory' to see the full digest."
            )

        return {
            "answer": answer,
            "total_episodes_searched": len(episodes),
            "match_count": len(top_matches),
            "matches": top_matches,
            "artifacts": list(matched_artifacts),
        }
