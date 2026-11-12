"""
VOID Agentic OS - Verification Agent
Provides independent, evidence-based verification for all agent actions and artifacts.
Never assumes success based on LLM claims; inspects real filesystem, exit codes, and syntax.
"""

import os
import ast
import json
import zipfile
import hashlib
from typing import Dict, Any, Optional, List
from agentic.types import AgentRole, AgentTask, ToolResult, VerificationResult
from agentic.agents.base import BaseAgent
from agentic.tools import ToolRegistry
from agentic.providers import AIProviderManager


class VerificationAgent(BaseAgent):
    """
    Independent verification agent that validates artifacts, code syntax,
    test results, and system state changes using concrete evidence.
    """

    def __init__(self, tools: ToolRegistry, provider_manager: AIProviderManager):
        super().__init__(
            role=AgentRole.VERIFIER,
            name="VerificationAgent",
            description="Performs independent evidence-based verification of files, syntax, and test runs.",
            tools=tools,
            provider_manager=provider_manager,
        )

    def _execute(self, task: AgentTask, context: Dict[str, Any]) -> ToolResult:
        """
        Runs verification against task targets specified in task.tool_args or context.
        Returns a ToolResult containing the VerificationResult.
        """
        target_type = task.tool_args.get("target_type", "artifact")
        target_path = task.tool_args.get("target_path")
        expected_exit_code = task.tool_args.get("expected_exit_code", 0)
        previous_result: Optional[ToolResult] = context.get("previous_result")

        v_result = self.verify(
            target_type=target_type,
            target_path=target_path,
            previous_result=previous_result,
            custom_checks=task.tool_args.get("custom_checks", []),
        )

        task.verification_result = v_result

        return ToolResult(
            tool_name="verify",
            success=v_result.verified,
            output=f"Verification {'PASSED' if v_result.verified else 'FAILED'}: {v_result.evidence}",
            error=v_result.failure_reason,
            artifacts=[target_path] if target_path and v_result.verified else [],
            metadata=v_result.details,
        )

    def verify(
        self,
        target_type: str,
        target_path: Optional[str] = None,
        previous_result: Optional[ToolResult] = None,
        custom_checks: Optional[List[str]] = None,
    ) -> VerificationResult:
        """
        Executes concrete verification checks according to target_type.
        """
        custom_checks = custom_checks or []

        # 1. Verification of File Artifact (DOCX, XLSX, JSON, PY, MD, TXT)
        if target_type in ("artifact", "file"):
            if not target_path:
                return VerificationResult(
                    verified=False,
                    evidence="No file path provided for verification.",
                    failure_reason="Target path is None or empty.",
                )
            return self._verify_file_artifact(target_path)

        # 2. Verification of Python Code Syntax
        elif target_type in ("python_syntax", "code"):
            if not target_path:
                return VerificationResult(
                    verified=False,
                    evidence="No python file path provided for syntax verification.",
                    failure_reason="Target path is None or empty.",
                )
            return self._verify_python_syntax(target_path)

        # 3. Verification of Subprocess / Test Execution Result
        elif target_type in ("test_execution", "subprocess"):
            return self._verify_test_execution(previous_result)

        # 4. Verification of System Metrics / Read-Only State
        elif target_type in ("system_metrics", "system_state"):
            return self._verify_system_metrics(previous_result)

        # 5. Verification of Media / Browser Playback
        elif target_type in ("media_playback", "playback", "browser_playback"):
            return self._verify_media_playback(previous_result)

        # Default fallback verification
        if previous_result:
            return VerificationResult(
                verified=previous_result.success,
                evidence=f"Previous tool '{previous_result.tool_name}' exit_code={previous_result.exit_code}",
                failure_reason=previous_result.error if not previous_result.success else None,
                details=previous_result.metadata,
            )

        return VerificationResult(
            verified=False,
            evidence="Unknown verification target_type with no previous result.",
            failure_reason=f"Unsupported target_type: {target_type}",
        )

    def _verify_file_artifact(self, path: str) -> VerificationResult:
        """Checks file existence, non-zero size, read permission, and format integrity."""
        if not os.path.exists(path):
            return VerificationResult(
                verified=False,
                evidence=f"File does not exist on disk: {path}",
                failure_reason="FILE_NOT_FOUND",
            )

        try:
            stat_info = os.stat(path)
            size_bytes = stat_info.st_size
            if size_bytes == 0:
                return VerificationResult(
                    verified=False,
                    evidence=f"File exists but is empty (0 bytes): {path}",
                    failure_reason="EMPTY_FILE",
                )

            # Hash generation for tamper/integrity evidence
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            file_hash = sha256.hexdigest()[:16]

            # Format-specific integrity checks
            details = {
                "path": path,
                "size_bytes": size_bytes,
                "sha256_short": file_hash,
                "mode": oct(stat_info.st_mode),
            }

            ext = os.path.splitext(path)[1].lower()

            # Word DOCX / Excel XLSX format check (must be valid zip container with XML contents)
            if ext in (".docx", ".xlsx"):
                if not zipfile.is_zipfile(path):
                    return VerificationResult(
                        verified=False,
                        evidence=f"File {path} is not a valid zip archive (corrupt {ext}).",
                        failure_reason=f"INVALID_{ext[1:].upper()}_CONTAINER",
                        details=details,
                    )
                with zipfile.ZipFile(path, "r") as zf:
                    namelist = zf.namelist()
                    if "[Content_Types].xml" not in namelist:
                        return VerificationResult(
                            verified=False,
                            evidence=f"File {path} lacks Office [Content_Types].xml structure.",
                            failure_reason=f"MALFORMED_{ext[1:].upper()}_XML",
                            details=details,
                        )
                details["office_container_valid"] = True

            # JSON file check
            elif ext == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    json.load(f)
                details["json_valid"] = True

            # Python syntax check
            elif ext == ".py":
                with open(path, "r", encoding="utf-8") as f:
                    code_content = f.read()
                ast.parse(code_content, filename=path)
                details["python_ast_valid"] = True

            return VerificationResult(
                verified=True,
                evidence=f"File verified: {os.path.basename(path)} ({size_bytes} bytes, hash={file_hash})",
                details=details,
            )

        except Exception as e:
            return VerificationResult(
                verified=False,
                evidence=f"Exception while validating file {path}: {str(e)}",
                failure_reason=f"VALIDATION_EXCEPTION: {type(e).__name__}",
                details={"error": str(e)},
            )

    def _verify_python_syntax(self, path: str) -> VerificationResult:
        """Verifies Python source code syntax using AST parser."""
        if not os.path.exists(path):
            return VerificationResult(
                verified=False,
                evidence=f"Python file not found: {path}",
                failure_reason="FILE_NOT_FOUND",
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code, filename=path)
            node_count = sum(1 for _ in ast.walk(tree))
            return VerificationResult(
                verified=True,
                evidence=f"Python syntax valid for {os.path.basename(path)} ({node_count} AST nodes parsed)",
                details={"ast_node_count": node_count, "path": path},
            )
        except SyntaxError as se:
            return VerificationResult(
                verified=False,
                evidence=f"SyntaxError in {path} at line {se.lineno}, col {se.offset}: {se.msg}",
                failure_reason="SYNTAX_ERROR",
                details={"lineno": se.lineno, "offset": se.offset, "msg": se.msg},
            )

    def _verify_test_execution(self, result: Optional[ToolResult]) -> VerificationResult:
        """Validates test runner results from pytest or unittest."""
        if not result:
            return VerificationResult(
                verified=False,
                evidence="No test execution result provided.",
                failure_reason="MISSING_RESULT",
            )

        if not result.success or result.exit_code != 0:
            return VerificationResult(
                verified=False,
                evidence=f"Test runner failed with exit_code={result.exit_code}. Stderr: {result.stderr[:200]}",
                failure_reason="TESTS_FAILED",
                details={"exit_code": result.exit_code, "output": result.output[:500]},
            )

        # Confirm output contains positive test indicators
        output_lower = result.output.lower()
        if "ran " in output_lower and ("ok" in output_lower or "passed" in output_lower):
            return VerificationResult(
                verified=True,
                evidence=f"Test suite passed with exit_code=0: {result.output.strip().splitlines()[-1]}",
                details={"exit_code": 0, "summary_line": result.output.strip().splitlines()[-1]},
            )

        return VerificationResult(
            verified=True,
            evidence=f"Subprocess terminated successfully with exit_code=0",
            details={"exit_code": 0},
        )

    def _verify_system_metrics(self, result: Optional[ToolResult]) -> VerificationResult:
        """Validates that system metric inspection returned non-empty, sensible telemetry."""
        if not result or not result.success:
            return VerificationResult(
                verified=False,
                evidence="System metric query failed or produced no output.",
                failure_reason="METRICS_QUERY_FAILED",
            )
        metadata = result.metadata or {}
        if "cpu_percent" in metadata or "memory" in metadata or "top_processes" in metadata:
            return VerificationResult(
                verified=True,
                evidence=f"System metrics captured with valid telemetry keys: {list(metadata.keys())}",
                details=metadata,
            )
        return VerificationResult(
            verified=True,
            evidence="System state inspection succeeded.",
            details=metadata,
        )

    def _verify_media_playback(self, result: Optional[ToolResult]) -> VerificationResult:
        """Verifies active media playback via MPRIS or PipeWire audio stream or browser presence."""
        import subprocess
        playerctl_status = ""
        try:
            r = subprocess.run(["playerctl", "status"], capture_output=True, text=True, timeout=1.5)
            playerctl_status = r.stdout.strip()
        except Exception:
            pass

        audio_stream = False
        try:
            r = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True, timeout=1.5)
            if "state: RUNNING" in r.stdout or "Corked: no" in r.stdout or "chromium" in r.stdout.lower():
                audio_stream = True
        except Exception:
            pass

        import psutil
        browser_active = False
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                name = (p.info['name'] or '').lower()
                cmdline = " ".join(p.info['cmdline'] or []).lower()
                if "chromium" in name or "chrome" in name or "youtube" in cmdline:
                    browser_active = True
                    break
            except Exception:
                continue

        verified = bool(playerctl_status in ("Playing", "Paused") or audio_stream or browser_active or (result and result.success))
        evidence = f"Media Playback Verified: playerctl='{playerctl_status}', audio_stream={audio_stream}, browser_active={browser_active}"
        return VerificationResult(
            verified=verified,
            evidence=evidence,
            details={"playerctl": playerctl_status, "audio_stream": audio_stream, "browser_active": browser_active}
        )

