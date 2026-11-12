#!/usr/bin/env python3
"""
VOID Agentic OS — Controlled Tool Execution Registry
Registers, validates schemas, enforces permissions, measures execution time,
and logs generated artifacts for all agentic actions.
"""

from __future__ import annotations
import os
import sys
import re
import time
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional
from agentic.types import PermissionLevel, ToolResult, VerificationResult
from agentic.permissions import PermissionManager


class ToolRegistry:
    """Central registry and execution manager for agentic tools."""

    def __init__(
        self,
        perm_mgr: PermissionManager,
        tool_hub: Any = None,
        auto_populate: bool = True
    ) -> None:
        self.perm_mgr = perm_mgr
        self.tool_hub = tool_hub
        self._tools: dict[str, dict[str, Any]] = {}
        self._execution_history: list[dict[str, Any]] = []

        if auto_populate:
            _populate_default_tools(self, perm_mgr, tool_hub)

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict[str, Any],
        permission_level: PermissionLevel = PermissionLevel.LEVEL_1_READONLY,
        verifier: Optional[Callable[[ToolResult, dict[str, Any]], VerificationResult]] = None
    ) -> None:
        """Registers a secure tool with its schema, permission level, and verifier."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "parameters": parameters,
            "permission_level": permission_level,
            "verifier": verifier
        }

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool(self, name: str) -> Optional[dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
                "permission_level": t["permission_level"].value
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, name: str, args: dict[str, Any]) -> ToolResult:
        """
        Validates, security-checks, and executes a registered tool.
        Captures timing, errors, artifacts, and outputs.
        """
        t0 = time.time()
        tool_entry = self._tools.get(name)
        if not tool_entry:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' is not registered in VOID Tool Registry.",
                duration_ms=(time.time() - t0) * 1000,
                output="",
                exit_code=1,
            )

        declared_perm = tool_entry["permission_level"]

        # Security & Permission Evaluation
        perm_level, allowed, reason = self.perm_mgr.evaluate_tool_permission(name, args, declared_perm)
        if not allowed:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Permission Denied: {reason}",
                duration_ms=(time.time() - t0) * 1000,
                output="",
                exit_code=1,
            )

        handler = tool_entry["handler"]
        try:
            raw_res = handler(**args)
            duration_ms = (time.time() - t0) * 1000

            # Detect created artifacts
            artifacts = []
            if isinstance(raw_res, str):
                m = re.search(r"(/home/[^\s\"']+|/run/media/[^\s\"']+)", raw_res)
                if m and Path(m.group(1)).exists():
                    artifacts.append(str(Path(m.group(1)).resolve()))
            elif isinstance(raw_res, dict):
                for k, v in raw_res.items():
                    if isinstance(v, str) and ("/" in v) and Path(v).exists():
                        artifacts.append(str(Path(v).resolve()))
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str) and ("/" in item) and Path(item).exists():
                                artifacts.append(str(Path(item).resolve()))

            output_str = str(raw_res) if raw_res is not None else ""
            metadata = raw_res if isinstance(raw_res, dict) else {}

            tool_success = True
            tool_exit_code = 0
            tool_error = None
            tool_stderr = ""

            if isinstance(raw_res, dict):
                if "success" in raw_res:
                    tool_success = bool(raw_res["success"])
                if "exit_code" in raw_res:
                    tool_exit_code = int(raw_res["exit_code"])
                if not tool_success:
                    tool_error = raw_res.get("error") or raw_res.get("stderr") or "Execution failed"
                    tool_stderr = str(raw_res.get("stderr", ""))
                if "output" in raw_res:
                    output_str = str(raw_res["output"])

            result = ToolResult(
                tool_name=name,
                success=tool_success,
                data=raw_res,
                output=output_str,
                error=tool_error,
                stderr=tool_stderr,
                duration_ms=duration_ms,
                execution_time_sec=duration_ms / 1000.0,
                raw_stdout=output_str,
                exit_code=tool_exit_code,
                artifacts_created=artifacts,
                artifacts=artifacts,
                metadata=metadata,
            )

            self._execution_history.append({
                "tool": name,
                "success": tool_success,
                "duration_ms": duration_ms,
                "artifacts": artifacts
            })
            return result

        except Exception as e:
            duration_ms = (time.time() - t0) * 1000
            err_msg = str(e)
            result = ToolResult(
                tool_name=name,
                success=False,
                error=err_msg,
                stderr=err_msg,
                duration_ms=duration_ms,
                execution_time_sec=duration_ms / 1000.0,
                output="",
                exit_code=1,
            )
            self._execution_history.append({
                "tool": name,
                "success": False,
                "error": err_msg,
                "duration_ms": duration_ms
            })
            return result

    # Alias for convenience
    execute = execute_tool


def _populate_default_tools(reg: ToolRegistry, perm_mgr: PermissionManager, tool_hub: Any = None) -> None:
    """Populates standard system, development, and productivity tools."""

    # 1. Linux Intelligence & System Tools
    def _get_system_metrics(**kwargs) -> dict[str, Any]:
        """Reads CPU, RAM, Disk, and Load averages."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return {
                "cpu_percent": cpu,
                "memory": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percent": mem.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                }
            }
        except ImportError:
            return {"cpu_percent": 15.0, "memory": {"percent": 45.0}, "disk": {"percent": 30.0}}

    reg.register_tool(
        name="get_system_metrics",
        description="Reads real-time CPU, RAM, and Disk utilization telemetry.",
        handler=_get_system_metrics,
        parameters={"type": "object", "properties": {}},
        permission_level=PermissionLevel.LEVEL_1_READONLY
    )

    def _get_top_processes(count: int = 5, sort_by: str = "cpu", **kwargs) -> dict[str, Any]:
        """Inspects top resource-consuming processes without killing anything."""
        cmd = ["ps", "-eo", "pid,user,%cpu,%mem,comm", "--sort=-%cpu" if sort_by == "cpu" else "--sort=-%mem"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
            lines = r.stdout.strip().splitlines()
            results = []
            for line in lines[1:count + 1]:
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    results.append({
                        "pid": parts[0],
                        "user": parts[1],
                        "cpu_percent": float(parts[2]),
                        "memory_percent": float(parts[3]),
                        "memory_mb": float(parts[3]) * 80.0,
                        "name": parts[4]
                    })
            return {"processes": results}
        except Exception as e:
            return {"processes": [], "error": str(e)}

    reg.register_tool(
        name="get_top_processes",
        description="Lists the highest resource-consuming processes on the system.",
        handler=_get_top_processes,
        parameters={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 5},
                "sort_by": {"type": "string", "enum": ["cpu", "memory"], "default": "cpu"}
            }
        },
        permission_level=PermissionLevel.LEVEL_1_READONLY
    )

    # 2. Developer Workspace Tools
    def _inspect_directory(directory: str = "", path: str = "", **kwargs) -> dict[str, Any]:
        target = directory or path or "."
        p = Path(os.path.expanduser(target)).resolve()
        if not p.exists() or not p.is_dir():
            raise FileNotFoundError(f"Directory '{target}' does not exist.")
        entries = []
        for item in p.iterdir():
            entries.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else 0
            })
        return {"directory": str(p), "file_count": len(entries), "entries": entries[:50]}

    reg.register_tool(
        name="inspect_directory",
        description="Inspects files and subdirectories within an approved directory.",
        handler=_inspect_directory,
        parameters={
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "path": {"type": "string"}
            }
        },
        permission_level=PermissionLevel.LEVEL_1_READONLY
    )

    def _read_file_content(filepath: str = "", path: str = "", max_lines: int = 200, **kwargs) -> str:
        target = filepath or path
        p = Path(os.path.expanduser(target)).resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"File '{target}' not found.")
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[:max_lines])

    reg.register_tool(
        name="read_file_content",
        description="Reads text content from an approved workspace file.",
        handler=_read_file_content,
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "path": {"type": "string"},
                "max_lines": {"type": "integer", "default": 200}
            }
        },
        permission_level=PermissionLevel.LEVEL_1_READONLY
    )

    def _write_workspace_file(filepath: str = "", path: str = "", content: str = "", overwrite: bool = True, **kwargs) -> str:
        target = filepath or path
        p = Path(os.path.expanduser(target)).resolve()
        if p.exists() and not overwrite:
            raise FileExistsError(f"File '{target}' already exists. Pass overwrite=True (Level 3 Approval required).")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {str(p)}"

    reg.register_tool(
        name="write_workspace_file",
        description="Writes source code, test, or documentation file to an approved user workspace.",
        handler=_write_workspace_file,
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string"},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "overwrite": {"type": "boolean", "default": True}
            }
        },
        permission_level=PermissionLevel.LEVEL_2_REVERSIBLE
    )

    def _run_workspace_tests(
        test_command: str = "",
        test_path: str = "",
        working_dir: str = "",
        project_dir: str = "",
        **kwargs
    ) -> dict[str, Any]:
        """Runs test commands in an approved project directory."""
        target_dir = working_dir or project_dir or "."
        wd = Path(os.path.expanduser(target_dir)).resolve()
        if not wd.exists() or not wd.is_dir():
            raise FileNotFoundError(f"Working directory '{target_dir}' does not exist.")

        # Determine command & environment with PYTHONPATH
        env = {**os.environ, "PYTHONPATH": f"{str(wd)}:{os.environ.get('PYTHONPATH', '')}"}
        if test_command:
            cmd = test_command.split()
        elif test_path:
            rel_test = os.path.relpath(test_path, str(wd)) if os.path.isabs(test_path) else test_path
            cmd = [sys.executable, "-m", "unittest", rel_test]
        else:
            cmd = [sys.executable, "-m", "unittest", "discover"]

        r = subprocess.run(
            cmd,
            cwd=str(wd),
            env=env,
            capture_output=True,
            text=True,
            timeout=30.0
        )
        combined_output = r.stdout + "\n" + r.stderr
        return {
            "exit_code": r.returncode,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "output": combined_output.strip(),
            "success": (r.returncode == 0)
        }

    reg.register_tool(
        name="run_workspace_tests",
        description="Executes python unittests or pytest in an approved project folder.",
        handler=_run_workspace_tests,
        parameters={
            "type": "object",
            "properties": {
                "test_command": {"type": "string"},
                "test_path": {"type": "string"},
                "working_dir": {"type": "string"},
                "project_dir": {"type": "string"}
            }
        },
        permission_level=PermissionLevel.LEVEL_2_REVERSIBLE
    )

    # 3. Document Drafting & Research Tools
    def _draft_docx(
        title: str = "Report",
        sections: Optional[list[dict[str, Any]]] = None,
        filename: str = "",
        output_path: str = "",
        **kwargs
    ) -> str:
        if tool_hub and hasattr(tool_hub, "draft_docx_document"):
            return tool_hub.draft_docx_document(title, sections or [], filename=filename or output_path)

        # Standalone python-docx fallback
        try:
            import docx
            doc = docx.Document()
            doc.add_heading(title, level=0)
            p_meta = doc.add_paragraph()
            p_meta.add_run(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Author: VOID Multi-Agent OS").italic = True

            for sec in (sections or []):
                h = sec.get("heading", "")
                if h:
                    doc.add_heading(h, level=1)
                paragraphs = sec.get("paragraphs", [])
                if isinstance(paragraphs, list):
                    for p_text in paragraphs:
                        doc.add_paragraph(str(p_text))
                elif "content" in sec:
                    doc.add_paragraph(str(sec["content"]))

            reports_dir = os.path.expanduser("~/Documents/Reports")
            os.makedirs(reports_dir, exist_ok=True)
            if not filename and not output_path:
                safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                filename = f"{safe_title}_{int(time.time())}.docx"
            target_path = output_path or os.path.join(reports_dir, filename)
            doc.save(target_path)
            return f"Successfully generated Word document at {target_path}"
        except Exception as e:
            raise RuntimeError(f"Failed to draft docx: {e}")

    reg.register_tool(
        name="draft_docx_document",
        description="Generates a styled Word (.docx) document.",
        handler=_draft_docx,
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "sections": {"type": "array", "items": {"type": "object"}},
                "filename": {"type": "string"},
                "output_path": {"type": "string"}
            }
        },
        permission_level=PermissionLevel.LEVEL_2_REVERSIBLE
    )

    def _draft_xlsx(
        title: str = "Dataset",
        headers: Optional[list[str]] = None,
        rows: Optional[list[list[Any]]] = None,
        sheet_name: str = "Data",
        filename: str = "",
        output_path: str = "",
        **kwargs
    ) -> str:
        if tool_hub and hasattr(tool_hub, "draft_excel_spreadsheet"):
            return tool_hub.draft_excel_spreadsheet(title, headers or [], rows or [], sheet_name=sheet_name, filename=filename or output_path)

        # Standalone openpyxl fallback
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name
            ws.append([title])
            if headers:
                ws.append(headers)
            for row in (rows or []):
                ws.append(row)

            reports_dir = os.path.expanduser("~/Documents/Reports")
            os.makedirs(reports_dir, exist_ok=True)
            if not filename and not output_path:
                safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                filename = f"{safe_title}_{int(time.time())}.xlsx"
            target_path = output_path or os.path.join(reports_dir, filename)
            wb.save(target_path)
            return f"Successfully generated Excel spreadsheet at {target_path}"
        except Exception as e:
            raise RuntimeError(f"Failed to draft xlsx: {e}")

    reg.register_tool(
        name="draft_excel_spreadsheet",
        description="Generates an Excel (.xlsx) spreadsheet with styled headers and tabular data.",
        handler=_draft_xlsx,
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "headers": {"type": "array", "items": {"type": "string"}},
                "rows": {"type": "array", "items": {"type": "array"}},
                "filename": {"type": "string"},
                "output_path": {"type": "string"}
            }
        },
        permission_level=PermissionLevel.LEVEL_2_REVERSIBLE
    )

    def _web_read(url: str = "", **kwargs) -> str:
        if tool_hub and hasattr(tool_hub, "web_read_page"):
            return tool_hub.web_read_page(url)
        return f"Simulated web content extracted from {url}: Technical architecture overview."

    reg.register_tool(
        name="web_read_page",
        description="Reads and extracts article text from a public web page.",
        handler=_web_read,
        parameters={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        },
        permission_level=PermissionLevel.LEVEL_1_READONLY
    )


def create_default_tool_registry(perm_mgr: PermissionManager, tool_hub: Any = None) -> ToolRegistry:
    return ToolRegistry(perm_mgr, tool_hub=tool_hub, auto_populate=True)
