"""Unified diff verification, sandbox application, and bounded AI repair loops."""

import subprocess
from pathlib import Path
from exitwise.models import PatchAttempt, Provenance


def apply_patch_string(workspace_path: Path, unified_diff: str) -> tuple[bool, str | None]:
    """Test and apply a unified diff to a workspace directory."""
    if not unified_diff.strip():
        return True, None

    patch_file = workspace_path / "migration.diff"
    try:
        # Standardize newlines
        clean_diff = unified_diff.replace("\r\n", "\n")
        if not clean_diff.endswith("\n"):
            clean_diff += "\n"
        patch_file.write_text(clean_diff, encoding="utf-8")

        # 1. Test patch with git apply --check
        check_cmd = ["git", "apply", "--check", "--ignore-space-change", "--ignore-whitespace", "migration.diff"]
        check_res = subprocess.run(
            check_cmd,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=15,
        )

        if check_res.returncode != 0:
            err = check_res.stderr.strip() or check_res.stdout.strip() or "Patch does not apply cleanly"
            return False, err

        # 2. Apply patch
        apply_cmd = ["git", "apply", "--ignore-space-change", "--ignore-whitespace", "migration.diff"]
        apply_res = subprocess.run(
            apply_cmd,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=15,
        )

        if apply_res.returncode == 0:
            return True, None
        return False, apply_res.stderr.strip()
    except Exception as e:
        return False, str(e)
    finally:
        if patch_file.exists():
            patch_file.unlink(missing_ok=True)


def execute_patch_with_repair(
    workspace_path: Path,
    initial_diff: str,
    gemma_client: any = None,
    max_repairs: int = 2,
) -> PatchAttempt:
    """Apply diff to workspace copy, invoking bounded Gemma repair if git apply fails."""
    curr_diff = initial_diff
    last_error = None

    for attempt_idx in range(1, max_repairs + 2):
        success, error = apply_patch_string(workspace_path, curr_diff)
        if success:
            return PatchAttempt(
                attempt_number=attempt_idx,
                unified_diff=curr_diff,
                applied_cleanly=True,
                error_message=None,
                provenance=Provenance.VERIFIED_BY_EXECUTION,
            )

        last_error = error
        if attempt_idx <= max_repairs and gemma_client and getattr(gemma_client, "is_live", False):
            # Attempt repair via Gemma
            try:
                repair_prompt = (
                    f"The following diff failed to apply with error:\n{error}\n\n"
                    f"Original diff:\n{curr_diff}\n\n"
                    f"Please produce a repaired valid unified diff."
                )
                from exitwise.ai.schemas import MigrationPlanOutput
                rep = gemma_client._parse_and_validate(repair_prompt, MigrationPlanOutput)
                if rep and rep.unified_diff:
                    curr_diff = rep.unified_diff
                    continue
            except Exception:
                pass
        break

    return PatchAttempt(
        attempt_number=attempt_idx,
        unified_diff=curr_diff,
        applied_cleanly=False,
        error_message=last_error or "Failed to apply patch",
        provenance=Provenance.AI_GENERATED,
    )
