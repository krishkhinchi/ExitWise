"""Repository cloning, workspace isolation, and test runner detection."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RepoInfo:
    """Metadata regarding the ingested repository."""

    source_url_or_path: str
    workspace_path: Path
    commit_sha: str
    test_command: str
    has_tests: bool = True
    manifest_files: list[Path] = field(default_factory=list)


def is_git_url(target: str) -> bool:
    """Check if target string is a remote Git URL."""
    return target.startswith(("http://", "https://", "git@", "ssh://")) or target.endswith(".git")


def get_git_commit_sha(repo_dir: Path) -> str:
    """Extract commit SHA from git workspace, defaulting to 'unversioned' if not a git repo."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return res.stdout.strip()
    except Exception:
        return "0000000000000000000000000000000000000000"


def detect_test_command(workspace_path: Path) -> str:
    """Deterministically detect existing test command from repo files."""
    # Check pyproject.toml for pytest
    pyproject = workspace_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "tool.pytest" in content or "pytest" in content:
            return "python -m pytest"

    # Check Makefile
    makefile = workspace_path / "Makefile"
    if makefile.exists():
        content = makefile.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("test:") or line_str.startswith("check:"):
                # See if pytest is referenced in makefile
                if "pytest" in content:
                    return "python -m pytest"

    # Check tests directory
    tests_dir = workspace_path / "tests"
    if tests_dir.is_dir() and any(tests_dir.glob("test_*.py")):
        return "python -m pytest"

    return "python -m unittest discover -s tests"


def prepare_workspace(target_input: str, dest_dir: Path) -> RepoInfo:
    """Clone remote Git repo or copy local folder into an isolated temp directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    if is_git_url(target_input):
        import hashlib
        cache_key = hashlib.sha256(target_input.encode("utf-8")).hexdigest()[:16]
        cache_dir = Path(".cache") / "repos" / cache_key

        git_env = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "",
        }

        # If already cached locally, pull latest or copy directly from cache
        if cache_dir.is_dir() and (cache_dir / ".git").exists():
            try:
                subprocess.run(
                    ["git", "fetch", "--depth", "1", "origin"],
                    cwd=cache_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=git_env,
                )
                subprocess.run(
                    ["git", "reset", "--hard", "origin/HEAD"],
                    cwd=cache_dir,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=git_env,
                )
            except Exception:
                pass  # Use existing cache state
        else:
            cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth", "1",
                        "--single-branch",
                        "--no-tags",
                        target_input,
                        str(cache_dir),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=25,
                    env=git_env,
                )
            except subprocess.TimeoutExpired:
                shutil.rmtree(cache_dir, ignore_errors=True)
                raise RuntimeError(f"Cloning '{target_input}' timed out after 25s. Check network or repository access.")
            except subprocess.CalledProcessError as err:
                shutil.rmtree(cache_dir, ignore_errors=True)
                err_msg = (err.stderr or err.stdout or "Authentication required or repository not found").strip()
                raise RuntimeError(f"Git clone failed: {err_msg}")

        # Copy from cache to dest_dir
        def _ignore_git(path: str, names: list[str]) -> set[str]:
            return {".venv", "venv", "__pycache__", ".pytest_cache"}

        shutil.copytree(cache_dir, dest_dir, dirs_exist_ok=True, ignore=_ignore_git)
    else:
        src_path = Path(target_input).resolve()
        if not src_path.exists() or not src_path.is_dir():
            raise FileNotFoundError(f"Target path does not exist or is not a directory: {target_input}")

        # Copy directory excluding large/temp files
        def _ignore_patterns(path: str, names: list[str]) -> set[str]:
            ignored = set()
            for name in names:
                if name in {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "exitwise-output"}:
                    ignored.add(name)
            return ignored

        shutil.copytree(src_path, dest_dir, dirs_exist_ok=True, ignore=_ignore_patterns)

    commit_sha = get_git_commit_sha(dest_dir)
    test_cmd = detect_test_command(dest_dir)

    manifest_patterns = [
        "requirements*.txt",
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "Pipfile",
        "Dockerfile",
        "Makefile",
    ]
    manifests: list[Path] = []
    for pattern in manifest_patterns:
        manifests.extend(dest_dir.glob(pattern))

    return RepoInfo(
        source_url_or_path=target_input,
        workspace_path=dest_dir,
        commit_sha=commit_sha,
        test_command=test_cmd,
        has_tests=(dest_dir / "tests").is_dir(),
        manifest_files=manifests,
    )
