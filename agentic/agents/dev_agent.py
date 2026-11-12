"""
VOID Agentic OS - Developer Agent
Handles autonomous software development workflows:
1. Inspects code architecture in approved workspaces.
2. Scaffolds modular Python applications with unit test suites.
3. Runs unit tests in isolated subprocesses.
4. Diagnoses failing tests / syntax errors.
5. Applies surgical code fixes (with automatic backups).
6. Re-executes test suites to prove resolution.
"""

import os
import shutil
import time
from typing import Dict, Any, List, Optional
from agentic.types import AgentRole, AgentTask, ToolResult
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager


class DeveloperAgent(BaseAgent):
    """
    Autonomous Developer Agent for inspection, scaffolding, test-driven debugging,
    and surgical code modification within approved project directories.
    """

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.DEVELOPER,
            name="DeveloperAgent",
            description="Autonomous software engineering, unit test execution, and bug fixing.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        action = task.tool_args.get("action", "run_tests")

        if action == "run_tests":
            test_path = task.tool_args.get("test_path")
            project_dir = task.tool_args.get("project_dir")
            return self.tools.execute("run_workspace_tests", {
                "test_path": test_path,
                "project_dir": project_dir,
            })

        elif action == "scaffold_project":
            return self.scaffold_project(
                project_name=task.tool_args.get("project_name", "void_demo_app"),
                target_dir=task.tool_args.get("target_dir"),
                files=task.tool_args.get("files", {}),
            )

        elif action == "apply_fix":
            return self.apply_code_fix(
                file_path=task.tool_args.get("file_path"),
                new_content=task.tool_args.get("new_content"),
                expected_test_path=task.tool_args.get("test_path"),
            )

        elif action == "inspect_code":
            file_path = task.tool_args.get("file_path")
            return self.tools.execute("read_file_content", {"path": file_path})

        else:
            return ToolResult(
                tool_name="dev_agent",
                success=False,
                output="",
                error=f"Unsupported DeveloperAgent action: {action}",
                exit_code=1,
            )

    def scaffold_project(
        self,
        project_name: str,
        target_dir: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """
        Scaffolds a clean Python project with source code and tests.
        """
        if not target_dir:
            target_dir = os.path.expanduser(f"~/Documents/Projects/{project_name}")

        os.makedirs(target_dir, exist_ok=True)
        created_files = []

        files = files or {}
        for rel_path, content in files.items():
            full_path = os.path.join(target_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            write_res = self.tools.execute("write_workspace_file", {
                "path": full_path,
                "content": content,
                "overwrite": True,
            })
            if write_res.success:
                created_files.append(full_path)
            else:
                return write_res

        return ToolResult(
            tool_name="scaffold_project",
            success=True,
            output=f"Successfully scaffolded project '{project_name}' with {len(created_files)} files at {target_dir}.",
            artifacts=created_files,
            metadata={"project_dir": target_dir, "files": created_files},
        )

    def apply_code_fix(
        self,
        file_path: str,
        new_content: str,
        expected_test_path: Optional[str] = None,
    ) -> ToolResult:
        """
        Applies a surgical code fix with automatic safety backup,
        and optionally re-runs tests to verify resolution.
        """
        if not file_path or not os.path.exists(file_path):
            return ToolResult(
                tool_name="apply_code_fix",
                success=False,
                output="",
                error=f"Target file for fix does not exist: {file_path}",
                exit_code=1,
            )

        # 1. Create timestamped safety backup
        backup_path = f"{file_path}.bak_{int(time.time())}"
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            return ToolResult(
                tool_name="apply_code_fix",
                success=False,
                output="",
                error=f"Failed to create backup before applying fix: {e}",
                exit_code=1,
            )

        # 2. Write new content
        write_res = self.tools.execute("write_workspace_file", {
            "path": file_path,
            "content": new_content,
        })
        if not write_res.success:
            # Rollback
            shutil.copy2(backup_path, file_path)
            return write_res

        # 3. If test_path provided, re-run tests immediately
        test_summary = "Fix written successfully."
        if expected_test_path:
            project_dir = os.path.dirname(os.path.abspath(expected_test_path))
            test_res = self.tools.execute("run_workspace_tests", {
                "test_path": expected_test_path,
                "project_dir": project_dir,
            })
            if not test_res.success:
                return ToolResult(
                    tool_name="apply_code_fix",
                    success=False,
                    output=f"Applied fix to {file_path}, but tests still failed:\n{test_res.output}",
                    error=test_res.stderr or "Tests failed after fix",
                    artifacts=[file_path, backup_path],
                    exit_code=test_res.exit_code,
                    metadata={"backup": backup_path, "tests_passed": False},
                )
            test_summary = f"Fix verified! Tests passed:\n{test_res.output}"

        return ToolResult(
            tool_name="apply_code_fix",
            success=True,
            output=test_summary,
            artifacts=[file_path, backup_path],
            metadata={"backup": backup_path, "tests_passed": True},
        )
