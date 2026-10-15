"""Capsule builder aggregating facts, proposals, and verified execution outcomes."""

import datetime
from exitwise import __version__
from exitwise.config import GEMMA_ACCESS_METHOD
from exitwise.models import (
    CapsuleMeta,
    DependencyCapsule,
    DependencyRecord,
    Provenance,
    TrustSummary,
)


def compute_trust_summary(capsule: DependencyCapsule) -> TrustSummary:
    """Calculate counts of claims by provenance state to populate the trust summary."""
    observed = 0
    verified_by_exec = 0
    ai_gen = 0
    ai_ver = 0
    not_ver = 0

    def _tally(prov: Provenance | str) -> None:
        nonlocal observed, verified_by_exec, ai_gen, ai_ver, not_ver
        val = prov.value if isinstance(prov, Provenance) else str(prov)
        if val == "OBSERVED":
            observed += 1
        elif val == "VERIFIED_BY_EXECUTION":
            verified_by_exec += 1
        elif val == "AI_GENERATED":
            ai_gen += 1
        elif val == "AI_VERIFIED":
            ai_ver += 1
        elif val == "NOT_VERIFIED":
            not_ver += 1

    # Tally dependency record
    _tally(capsule.dependency.provenance)

    # Risk indicators
    for item in capsule.risk_indicators:
        _tally(item.provenance)

    # Usage
    _tally(capsule.usage_summary.provenance)
    for loc in capsule.usage_locations:
        _tally(loc.provenance)

    # Proposed replacement & candidates
    if capsule.proposed_replacement:
        _tally(capsule.proposed_replacement.provenance)
    for cand in capsule.replacement_candidates:
        _tally(cand.provenance)

    # Steps
    for step in capsule.migration_steps:
        _tally(step.provenance)

    # Patch
    if capsule.patch:
        _tally(capsule.patch.provenance)

    # Suggested tests
    for st in capsule.suggested_tests:
        _tally(st.provenance)

    # Executed test runs
    for tr in capsule.executed_test_results:
        _tally(tr.provenance)

    # Gaps, concerns, limitations
    for g in capsule.compatibility_gaps:
        _tally(g.provenance)
    for oc in capsule.open_concerns:
        _tally(oc.provenance)
    for lim in capsule.limitations:
        _tally(lim.provenance)

    total = observed + verified_by_exec + ai_gen + ai_ver + not_ver
    return TrustSummary(
        observed_count=observed,
        verified_by_execution_count=verified_by_exec,
        ai_generated_count=ai_gen,
        ai_verified_count=ai_ver,
        not_verified_count=not_ver,
        total_claims=total,
    )


def determine_capsule_verdict(capsule: DependencyCapsule) -> str:
    """Evaluate overall readiness verdict based on executed tests and surfaced gaps."""
    # If no tests executed at all
    if not capsule.executed_test_results:
        return "NOT EXECUTED"

    candidate_runs = [r for r in capsule.executed_test_results if r.side == "candidate"]
    if not candidate_runs:
        return "NOT EXECUTED"

    # Check for critical errors or patch failures
    if capsule.patch and not capsule.patch.applied_cleanly:
        return "BLOCKED"

    has_candidate_failure = any(r.exit_code != 0 or r.failed > 0 for r in candidate_runs)
    has_critical_gaps = any(g.severity in ("CRITICAL", "HIGH") for g in capsule.compatibility_gaps)

    if has_candidate_failure or has_critical_gaps:
        return "BLOCKED"

    # If minor gaps exist
    if capsule.compatibility_gaps:
        return "READY WITH GAPS"

    return "READY"


def build_dependency_capsule(
    dependency_record: DependencyRecord,
    target_repo_url: str,
    target_commit_sha: str,
    tested_python_versions: list[str],
    gemma_model_id: str,
    risk_indicators: list,
    usage_summary: any,
    usage_locations: list,
    proposed_replacement: any,
    replacement_candidates: list,
    migration_steps: list,
    patch_attempt: any,
    suggested_tests: list,
    executed_test_results: list,
    compatibility_gaps: list,
    open_concerns: list,
    limitations: list,
    cached: bool = False,
) -> DependencyCapsule:
    """Construct and finalize a Dependency Exit Capsule."""
    meta = CapsuleMeta(
        tool_name="Exitwise",
        tool_version=__version__,
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        target_repo_url=target_repo_url,
        target_commit_sha=target_commit_sha,
        tested_python_versions=tested_python_versions,
        gemma_model_id=gemma_model_id,
        access_method=GEMMA_ACCESS_METHOD,
        cached=cached,
    )

    capsule = DependencyCapsule(
        meta=meta,
        dependency=dependency_record,
        risk_indicators=risk_indicators,
        usage_summary=usage_summary,
        usage_locations=usage_locations,
        proposed_replacement=proposed_replacement,
        replacement_candidates=replacement_candidates,
        migration_steps=migration_steps,
        patch=patch_attempt,
        suggested_tests=suggested_tests,
        executed_test_results=executed_test_results,
        compatibility_gaps=compatibility_gaps,
        open_concerns=open_concerns,
        limitations=limitations,
    )

    capsule.provenance_summary = compute_trust_summary(capsule)
    capsule.overall_verdict = determine_capsule_verdict(capsule)
    return capsule
