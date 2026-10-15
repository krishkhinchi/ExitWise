"""Deterministic comparison of baseline vs candidate execution outcomes."""

from dataclasses import dataclass, field
from exitwise.models import TestRun


@dataclass
class ExecutionDiffSummary:
    """Outcome comparison between baseline and candidate test runs."""

    baseline_exit_code: int
    candidate_exit_code: int
    is_regression: bool
    is_improvement: bool
    passed_delta: int
    failed_delta: int
    duration_delta: float
    newly_failing: list[str] = field(default_factory=list)
    new_warnings: list[str] = field(default_factory=list)


def compare_test_runs(baseline: TestRun, candidate: TestRun) -> ExecutionDiffSummary:
    """Compare baseline and candidate test execution results."""
    is_reg = (candidate.exit_code != 0 and baseline.exit_code == 0) or (candidate.failed > baseline.failed)
    is_imp = (baseline.exit_code != 0 and candidate.exit_code == 0) or (candidate.passed > baseline.passed and candidate.failed <= baseline.failed)

    passed_diff = candidate.passed - baseline.passed
    failed_diff = candidate.failed - baseline.failed
    dur_diff = round(candidate.duration_seconds - baseline.duration_seconds, 2)

    newly_failing = []
    if candidate.failed > baseline.failed:
        newly_failing.append(f"Candidate encountered {candidate.failed - baseline.failed} additional test failure(s)")

    new_warnings = []
    if "DeprecationWarning" in candidate.output_tail and "DeprecationWarning" not in baseline.output_tail:
        new_warnings.append("New DeprecationWarning triggered during candidate execution")

    return ExecutionDiffSummary(
        baseline_exit_code=baseline.exit_code,
        candidate_exit_code=candidate.exit_code,
        is_regression=is_reg,
        is_improvement=is_imp,
        passed_delta=passed_diff,
        failed_delta=failed_diff,
        duration_delta=dur_diff,
        newly_failing=newly_failing,
        new_warnings=new_warnings,
    )
