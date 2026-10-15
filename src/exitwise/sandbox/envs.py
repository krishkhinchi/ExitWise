"""Isolated virtual environment creation with environment scrubbing and interpreter detection."""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRUB_ENV_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|auth|credential)"),
    re.compile(r"^GEMINI_"),
    re.compile(r"^GOOGLE_"),
    re.compile(r"^GITHUB_"),
    re.compile(r"^AWS_"),
    re.compile(r"^OPENAI_"),
    re.compile(r"^ANTHROPIC_"),
]


@dataclass
class PythonInterpreter:
    """Discovered Python runtime on host system."""

    version_str: str  # e.g. "3.13" or "3.12"
    executable_path: str
    is_available: bool = True
    skip_reason: str | None = None


def scrub_child_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Scrub sensitive API keys, tokens, and credentials from subprocess environment."""
    env = dict(base_env or os.environ)
    keys_to_remove = []
    for k in env.keys():
        for pat in SCRUB_ENV_PATTERNS:
            if pat.search(k):
                keys_to_remove.append(k)
                break

    for k in keys_to_remove:
        env.pop(k, None)

    # Ensure standard path and loopback support
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def discover_python_interpreters() -> list[PythonInterpreter]:
    """Detect available Python 3.12 and 3.13 interpreters on host."""
    interpreters: list[PythonInterpreter] = []
    curr_major, curr_minor = sys.version_info[:2]
    curr_ver_str = f"{curr_major}.{curr_minor}"

    # Current interpreter
    if curr_ver_str in ("3.12", "3.13"):
        interpreters.append(
            PythonInterpreter(
                version_str=curr_ver_str,
                executable_path=sys.executable,
                is_available=True,
            )
        )

    # Check for py launcher on Windows
    for target_ver in ("3.12", "3.13"):
        if any(i.version_str == target_ver for i in interpreters):
            continue
        try:
            res = subprocess.run(
                ["py", f"-{target_ver}", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                interpreters.append(
                    PythonInterpreter(
                        version_str=target_ver,
                        executable_path=res.stdout.strip(),
                        is_available=True,
                    )
                )
            else:
                interpreters.append(
                    PythonInterpreter(
                        version_str=target_ver,
                        executable_path="",
                        is_available=False,
                        skip_reason=f"Python {target_ver} not found on system; skipped matrix run",
                    )
                )
        except Exception:
            interpreters.append(
                PythonInterpreter(
                    version_str=target_ver,
                    executable_path="",
                    is_available=False,
                    skip_reason=f"Python {target_ver} not found on system; skipped matrix run",
                )
            )

    return interpreters


def create_isolated_venv(venv_dir: Path, interpreter: PythonInterpreter) -> Path:
    """Create a virtual environment inside venv_dir using the specified interpreter."""
    venv_dir.mkdir(parents=True, exist_ok=True)
    python_exe = interpreter.executable_path or sys.executable

    # Create venv using standard venv module
    subprocess.run(
        [python_exe, "-m", "venv", "--without-pip", str(venv_dir)],
        check=True,
        capture_output=True,
        timeout=30,
    )

    # Windows scripts vs Unix bin
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    return venv_python
