"""Compatibility gap detection and limitation generation with provenance tracking."""

from exitwise.compare.diff import ExecutionDiffSummary
from exitwise.models import (
    CompatibilityGap,
    DifferentialTest,
    Limitation,
    OpenConcern,
    PatchAttempt,
    Provenance,
    TestRun,
)


def surface_compatibility_gaps(
    target_dep: str,
    replacement_dep: str,
    patch: PatchAttempt | None,
    diff_summary: ExecutionDiffSummary | None,
    diff_tests: list[DifferentialTest],
    gap_counter_start: int = 1,
) -> tuple[list[CompatibilityGap], list[OpenConcern], list[Limitation]]:
    """Surface factual, observed compatibility gaps and structural limitations."""
    gaps: list[CompatibilityGap] = []
    concerns: list[OpenConcern] = []
    limitations: list[Limitation] = []
    counter = gap_counter_start

    # 1. Patch application gap
    if patch and not patch.applied_cleanly:
        gaps.append(
            CompatibilityGap(
                id=f"GAP-{counter:04d}",
                description=f"Automated migration diff failed to apply cleanly: {patch.error_message or 'Hunk rejected'}",
                evidence_ids=[],
                severity="HIGH",
                status="OBSERVED",
                suggested_resolution="Review the unified diff manually and resolve conflicting hunk offsets.",
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 2. Test suite regression
    if diff_summary and diff_summary.is_regression:
        gaps.append(
            CompatibilityGap(
                id=f"GAP-{counter:04d}",
                description=f"Test suite encountered regressions after migrating to '{replacement_dep}'.",
                evidence_ids=[],
                severity="HIGH",
                status="OBSERVED",
                suggested_resolution="Inspect candidate traceback tail to identify breaking API incompatibilities.",
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 3. Differential tests failure
    for dt in diff_tests:
        if dt.candidate_passed is False:
            gaps.append(
                CompatibilityGap(
                    id=f"GAP-{counter:04d}",
                    description=f"Differential API test '{dt.test_name}' failed against candidate '{replacement_dep}'.",
                    evidence_ids=[dt.execution_evidence_id] if dt.execution_evidence_id else [],
                    severity="MEDIUM",
                    status="OBSERVED",
                    suggested_resolution="Verify signature differences or parameter changes in the replacement API.",
                    provenance=Provenance.OBSERVED,
                )
            )
            counter += 1

    # 4. Open concerns (features only testable in production, transitive dependencies, licensing)
    concerns.append(
        OpenConcern(
            description=f"Replacement '{replacement_dep}' may introduce new transitive dependencies requiring separate audit.",
            category="transitive_dependencies",
            provenance=Provenance.AI_GENERATED,
        )
    )
    concerns.append(
        OpenConcern(
            description="Code paths with dynamic parameters or external network endpoints require runtime staging verification.",
            category="untested_runtime_paths",
            provenance=Provenance.AI_GENERATED,
        )
    )

    # 5. Limitations
    limitations.append(
        Limitation(
            description="Test runs were executed in an isolated local sandbox with loopback networking enabled.",
            category="sandbox_environment",
            provenance=Provenance.OBSERVED,
        )
    )

    return gaps, concerns, limitations
