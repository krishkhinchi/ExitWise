"""Capsule verification, hash manifest integrity checks, and reproducibility re-runs."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from exitwise.models import DependencyCapsule


def compute_sha256(file_path: Path) -> str:
    """Compute sha256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def write_manifest_and_scripts(capsule_dir: Path, capsule: DependencyCapsule) -> None:
    """Generate MANIFEST.sha256, reproduce.sh, and reproduce.ps1 inside capsule directory."""
    # 1. Generate reproduce.sh
    sh_lines = [
        "#!/usr/bin/env bash",
        "# Exitwise Reproduction Script",
        "set -euo pipefail",
        "",
        f'echo "=== Reproducing test verification for {capsule.dependency.name} ==="',
    ]
    for r in capsule.executed_test_results:
        sh_lines.append(f'echo "Running {r.side} suite on Python {r.python_version}..."')
        sh_lines.append(r.command)

    (capsule_dir / "reproduce.sh").write_text("\n".join(sh_lines) + "\n", encoding="utf-8")

    # 2. Generate reproduce.ps1
    ps_lines = [
        "# Exitwise Reproduction Script for Windows PowerShell",
        f'Write-Host "=== Reproducing test verification for {capsule.dependency.name} ===" -ForegroundColor Cyan',
    ]
    for r in capsule.executed_test_results:
        ps_lines.append(f'Write-Host "Running {r.side} suite on Python {r.python_version}..." -ForegroundColor Green')
        ps_lines.append(r.command)

    (capsule_dir / "reproduce.ps1").write_text("\n".join(ps_lines) + "\n", encoding="utf-8")

    # 3. Generate MANIFEST.sha256
    manifest_lines = []
    for f in sorted(capsule_dir.rglob("*")):
        if f.is_file() and f.name != "MANIFEST.sha256":
            rel_name = str(f.relative_to(capsule_dir)).replace("\\", "/")
            manifest_lines.append(f"{compute_sha256(f)}  {rel_name}")

    (capsule_dir / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def verify_capsule_directory(capsule_dir: Path) -> tuple[bool, list[str]]:
    """Verify hash integrity and re-run executed tests to check reproducibility."""
    issues = []
    manifest_file = capsule_dir / "MANIFEST.sha256"
    capsule_json_file = capsule_dir / "capsule.json"

    if not manifest_file.exists():
        return False, ["MANIFEST.sha256 not found in capsule directory"]
    if not capsule_json_file.exists():
        return False, ["capsule.json not found in capsule directory"]

    # 1. Verify file hashes
    for line in manifest_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected_hash, rel_path = line.split("  ", 1)
        target_file = capsule_dir / rel_path
        if not target_file.exists():
            issues.append(f"Missing file recorded in manifest: {rel_path}")
        else:
            actual_hash = compute_sha256(target_file)
            if actual_hash != expected_hash:
                issues.append(f"Hash mismatch on {rel_path}: expected {expected_hash}, got {actual_hash}")

    # 2. Load capsule data
    try:
        data = json.loads(capsule_json_file.read_text(encoding="utf-8"))
        capsule = DependencyCapsule.model_validate(data)
    except Exception as e:
        issues.append(f"Invalid capsule.json: {e}")
        return False, issues

    # 3. Re-run test commands if present
    for tr in capsule.executed_test_results:
        try:
            res = subprocess.run(
                tr.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=45,
            )
            if res.returncode != tr.exit_code:
                issues.append(
                    f"Test outcome drift for '{tr.side}': original exit code {tr.exit_code}, current re-run exit code {res.returncode}"
                )
        except Exception as e:
            issues.append(f"Failed to re-execute test '{tr.command}': {e}")

    is_reproducible = len(issues) == 0
    return is_reproducible, issues
