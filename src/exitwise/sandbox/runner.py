"""Test execution runner with flake guard, timeouts, and structured output parsing."""

import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from exitwise.models import DifferentialTest, TestRun, Provenance
from exitwise.sandbox.envs import scrub_child_environment

PYTEST_SUMMARY_PATTERN = re.compile(
    r"(?:(?P<passed>\d+)\s+passed)?.*?(?:(?P<failed>\d+)\s+failed)?.*?(?:(?P<errors>\d+)\s+error)?.*?(?:in\s+(?P<duration>[\d\.]+)\s*s)?",
    re.IGNORECASE,
)


@dataclass
class RawExecutionResult:
    """Subprocess execution output."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def execute_subprocess(
    cmd: list[str] | str,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> RawExecutionResult:
    """Execute command with scrubbed environment and strict timeout."""
    scrubbed = scrub_child_environment(env)
    start_time = time.time()
    try:
        use_shell = isinstance(cmd, str)
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=scrubbed,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.time() - start_time, 2)
        return RawExecutionResult(
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired as e:
        duration = round(time.time() - start_time, 2)
        return RawExecutionResult(
            exit_code=-1,
            stdout=e.stdout or "",
            stderr=e.stderr or f"Process timed out after {timeout} seconds",
            duration_seconds=duration,
            timed_out=True,
        )
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return RawExecutionResult(
            exit_code=-1,
            stdout="",
            stderr=str(e),
            duration_seconds=duration,
        )


def parse_pytest_counts(output: str) -> tuple[int, int, int]:
    """Extract passed, failed, error counts from pytest output tail."""
    passed, failed, errors = 0, 0, 0
    lines = output.splitlines()[-15:]
    for line in reversed(lines):
        if "passed" in line or "failed" in line or "error" in line:
            m = PYTEST_SUMMARY_PATTERN.search(line)
            if m:
                p = m.group("passed")
                f = m.group("failed")
                e = m.group("errors")
                if p:
                    passed = int(p)
                if f:
                    failed = int(f)
                if e:
                    errors = int(e)
                if passed or failed or errors:
                    break
    return passed, failed, errors


def run_repo_suite(
    workspace_path: Path,
    python_exe: str,
    test_command: str,
    side: str,
    python_ver: str,
    evidence_id: str,
    flake_guard: bool = True,
    timeout: int = 120,
) -> TestRun:
    """Run test suite in workspace with flake guard and parse outcome."""
    full_cmd = f"{python_exe} -m pytest" if "pytest" in test_command else f"{python_exe} -m unittest discover -s tests"
    res = execute_subprocess(full_cmd, cwd=workspace_path, timeout=timeout)

    is_flaky = False
    # Flake guard: re-run once if initial test failed
    if res.exit_code != 0 and flake_guard:
        re_res = execute_subprocess(full_cmd, cwd=workspace_path, timeout=timeout)
        if re_res.exit_code == 0:
            is_flaky = True
            res = re_res

    combined_out = (res.stdout + "\n" + res.stderr).strip()
    passed, failed, errors = parse_pytest_counts(combined_out)

    # Get pip freeze list
    freeze_res = execute_subprocess(f"{python_exe} -m pip freeze", cwd=workspace_path, timeout=15)
    freeze_list = [line.strip() for line in freeze_res.stdout.splitlines() if line.strip()]

    return TestRun(
        side=side,  # baseline or candidate
        python_version=python_ver,
        command=full_cmd,
        exit_code=res.exit_code,
        passed=passed,
        failed=failed,
        errors=errors,
        duration_seconds=res.duration_seconds,
        output_tail=combined_out[-2000:],
        pip_freeze=freeze_list,
        flaky=is_flaky,
        evidence_id=evidence_id,
        provenance=Provenance.VERIFIED_BY_EXECUTION,
    )


def run_differential_test(
    workspace_path: Path,
    python_exe: str,
    diff_test: DifferentialTest,
    python_ver: str,
    evidence_id: str,
) -> tuple[bool, str]:
    """Execute AI-generated differential test in the workspace."""
    test_file = workspace_path / "tests" / diff_test.test_name
    try:
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(diff_test.code, encoding="utf-8")

        cmd = f"{python_exe} -m pytest tests/{diff_test.test_name}"
        res = execute_subprocess(cmd, cwd=workspace_path, timeout=30)
        passed = (res.exit_code == 0)
        output = (res.stdout + "\n" + res.stderr).strip()
        return passed, output
    finally:
        if test_file.exists():
            test_file.unlink(missing_ok=True)
