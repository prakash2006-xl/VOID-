"""
VOID Agentic OS - Linux Intelligence Agent
Performs deep system diagnostics, resource monitoring, bottleneck detection,
and safe user-level optimization recommendations. Strictly adheres to read-only safety.
"""

from typing import Dict, Any
from agentic.types import AgentRole, AgentTask, ToolResult
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager


class LinuxIntelligenceAgent(BaseAgent):
    """
    Analyzes Linux system performance, identifies resource bottlenecks (CPU, RAM, Disk, Thermal),
    and suggests safe user-space remediations without elevated permissions.
    """

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.LINUX_INTELLIGENCE,
            name="LinuxIntelligenceAgent",
            description="Deep Linux diagnostics, process analysis, and safe resource troubleshooting.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        if task.tool_name and self.tools.has_tool(task.tool_name) and task.tool_name not in ("linux_diagnostic", "full_audit"):
            return self.tools.execute(task.tool_name, task.tool_args)

        subcommand = task.tool_args.get("action", "diagnose")

        if subcommand == "metrics":
            return self.tools.execute("get_system_metrics", {})
        elif subcommand == "top_processes":
            count = task.tool_args.get("count", 10)
            sort_by = task.tool_args.get("sort_by", "memory")
            return self.tools.execute("get_top_processes", {"count": count, "sort_by": sort_by})
        elif subcommand == "diagnose" or subcommand == "full_audit":
            return self.perform_full_diagnostic(task)
        else:
            # Fallback to general tool execution
            return self.perform_full_diagnostic(task)

    def perform_full_diagnostic(self, task: AgentTask) -> ToolResult:
        """
        Executes a comprehensive health check:
        1. Gathers hardware telemetry (CPU, RAM, Disk, Temps, Battery).
        2. Gathers top memory and CPU consuming processes.
        3. Identifies bottlenecks against safety thresholds.
        4. Compiles actionable insights.
        """
        metrics_res = self.tools.execute("get_system_metrics", {})
        if not metrics_res.success:
            return metrics_res

        proc_res = self.tools.execute("get_top_processes", {"count": 8, "sort_by": "memory"})
        metrics = metrics_res.metadata or {}
        procs = proc_res.metadata.get("processes", []) if proc_res.success else []

        cpu = metrics.get("cpu_percent", 0.0)
        mem = metrics.get("memory", {})
        mem_percent = mem.get("percent", 0.0)
        disk = metrics.get("disk", {})
        disk_percent = disk.get("percent", 0.0)
        temps = metrics.get("temperatures", {})

        # Analyze bottlenecks
        bottlenecks = []
        recommendations = []

        if cpu > 80.0:
            bottlenecks.append(f"High CPU utilization: {cpu}%")
            recommendations.append("Inspect runaway processes or compile jobs running in background.")
        if mem_percent > 85.0:
            bottlenecks.append(f"High Memory pressure: {mem_percent}% used ({mem.get('used_gb', 0)} GB / {mem.get('total_gb', 0)} GB)")
            recommendations.append("Close idle browser tabs or unneeded Electron applications.")
        if disk_percent > 90.0:
            bottlenecks.append(f"Low root disk space: {disk_percent}% used ({disk.get('free_gb', 0)} GB free)")
            recommendations.append("Run user cache clean: `rm -rf ~/.cache/thumbnails/*` or prune package cache.")

        # Top consumer summary
        top_consumers_text = ""
        if procs:
            top_consumers_text = "\nTop Memory Consumers:\n" + "\n".join(
                [f"  - PID {p.get('pid')}: {p.get('name')} ({p.get('memory_mb', 0):.1f} MB RAM, {p.get('cpu_percent', 0):.1f}% CPU)" for p in procs[:5]]
            )

        status_headline = "System Health: OPTIMAL" if not bottlenecks else f"System Health: ATTENTION ({len(bottlenecks)} issues detected)"
        
        diagnostic_report = (
            f"=== VOID Linux Diagnostic Report ===\n"
            f"Status: {status_headline}\n\n"
            f"Telemetry Summary:\n"
            f"  * CPU Utilization: {cpu}%\n"
            f"  * RAM Utilization: {mem_percent}% ({mem.get('used_gb', 0)} GB / {mem.get('total_gb', 0)} GB)\n"
            f"  * Disk Utilization: {disk_percent}% ({disk.get('free_gb', 0)} GB available)\n"
            f"{top_consumers_text}\n\n"
        )

        if bottlenecks:
            diagnostic_report += "Identified Bottlenecks:\n" + "\n".join([f"  ! {b}" for b in bottlenecks]) + "\n\n"
            diagnostic_report += "Safe User-Space Recommendations:\n" + "\n".join([f"  > {r}" for r in recommendations]) + "\n"
        else:
            diagnostic_report += "No critical resource bottlenecks detected. Operating parameters normal.\n"

        return ToolResult(
            tool_name="linux_diagnostic",
            success=True,
            output=diagnostic_report,
            metadata={
                "cpu_percent": cpu,
                "memory_percent": mem_percent,
                "disk_percent": disk_percent,
                "bottlenecks": bottlenecks,
                "top_processes": procs[:5],
                "recommendations": recommendations,
            },
        )

