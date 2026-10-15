"""Pydantic v2 data models for Exitwise Dependency Exit Capsules.

Every leaf statement, recommendation, or result carries a strict Provenance tag.
"""

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class Provenance(str, Enum):
    """Provenance states enforcing strict separation of AI claims and verified facts."""

    OBSERVED = "OBSERVED"  # Measured directly by tool (fetched metadata, AST, exit codes)
    VERIFIED_BY_EXECUTION = "VERIFIED_BY_EXECUTION"  # Claim confirmed by sandbox test run
    AI_GENERATED = "AI_GENERATED"  # Produced by Gemma, unverified
    AI_VERIFIED = "AI_VERIFIED"  # AI-proposed and later confirmed by execution
    NOT_VERIFIED = "NOT_VERIFIED"  # Could not be checked, with concrete reason


class Evidence(BaseModel):
    """An atomic piece of observed or execution-derived evidence."""

    id: str = Field(description="Unique evidence identifier, e.g. EV-PYPI-0001")
    source: str = Field(description="Evidence producer (e.g. pypi_api, osv_api, ast, sandbox)")
    kind: str = Field(description="Category of evidence (e.g. metadata, ast_patch, test_output)")
    observed_value: Any = Field(description="Observed data or summary")
    timestamp: str = Field(description="ISO timestamp of observation")
    raw_ref: str | None = Field(default=None, description="Path to raw log or payload file")


class RiskIndicator(BaseModel):
    """Deterministic or surfaced risk flag for a dependency."""

    id: str
    dependency: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    source: str
    observed_value: str
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.OBSERVED


class UsageLocation(BaseModel):
    """Exact code location where a dependency is referenced or invoked."""

    file: str
    line: int
    col: int = 0
    symbol: str
    kind: str  # import, call, patch, attribute_access, inheritance, type_annotation, template_ref
    snippet: str
    context: str  # runtime, test, config, patching
    provenance: Provenance = Provenance.OBSERVED


class UsageSummary(BaseModel):
    """Aggregated coupling and usage characterization for a dependency."""

    total_files: int = 0
    total_occurrences: int = 0
    distinct_symbols: list[str] = Field(default_factory=list)
    is_monkey_patched: bool = False
    is_test_only: bool = False
    coupling_score: float = 0.0
    ai_characterization: str | None = None
    ai_characterization_evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.OBSERVED


class CandidateValidation(BaseModel):
    """Deterministic validation results for an AI-proposed replacement candidate."""

    exists_on_pypi_or_stdlib: bool = False
    is_stdlib: bool = False
    declares_py_compat: bool = False
    installs_cleanly: bool = False
    validation_log: str = ""


class ReplacementCandidate(BaseModel):
    """Proposed replacement candidate with trade-offs and validation status."""

    name: str
    kind: Literal["pypi", "stdlib", "none"]
    tradeoffs: list[str] = Field(default_factory=list)
    validation: CandidateValidation = Field(default_factory=CandidateValidation)
    status: Literal["ACCEPTED", "REJECTED", "MONITOR_ONLY"] = "ACCEPTED"
    rejection_reason: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.AI_GENERATED


class MigrationStep(BaseModel):
    """Ordered step for executing a dependency migration."""

    order: int
    description: str
    command: str | None = None
    status: Literal["AI_PROPOSED", "EXECUTED", "FAILED", "SKIPPED"] = "AI_PROPOSED"
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.AI_GENERATED


class PatchAttempt(BaseModel):
    """Patch applied to sandbox workspace."""

    attempt_number: int = 1
    unified_diff: str = ""
    applied_cleanly: bool = False
    error_message: str | None = None
    provenance: Provenance = Provenance.AI_GENERATED


class DifferentialTest(BaseModel):
    """AI-generated differential compatibility test."""

    test_name: str
    code: str
    target_apis: list[str] = Field(default_factory=list)
    baseline_passed: bool | None = None
    candidate_passed: bool | None = None
    execution_evidence_id: str | None = None
    provenance: Provenance = Provenance.AI_GENERATED


class TestRun(BaseModel):
    """Observed test execution outcome in an isolated sandbox environment."""

    side: Literal["baseline", "candidate", "differential"]
    python_version: str
    command: str
    exit_code: int
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    output_tail: str = ""
    pip_freeze: list[str] = Field(default_factory=list)
    flaky: bool = False
    evidence_id: str = ""
    not_executed_reason: str | None = None
    provenance: Provenance = Provenance.VERIFIED_BY_EXECUTION


class CompatibilityGap(BaseModel):
    """Observed or hypothesized behavioral/API gap after replacement."""

    id: str
    description: str
    evidence_ids: list[str] = Field(default_factory=list)
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    status: Literal["OBSERVED", "AI_HYPOTHESIS"]
    suggested_resolution: str
    provenance: Provenance = Provenance.OBSERVED


class OpenConcern(BaseModel):
    """Untested code paths, license differences, or production-only concerns."""

    description: str
    category: str
    provenance: Provenance = Provenance.AI_GENERATED


class Limitation(BaseModel):
    """Technical limitation or skipped step in the capsule generation."""

    description: str
    category: str
    provenance: Provenance = Provenance.OBSERVED


class TrustSummary(BaseModel):
    """Counts per provenance tag to give maintainers transparent confidence."""

    observed_count: int = 0
    verified_by_execution_count: int = 0
    ai_generated_count: int = 0
    ai_verified_count: int = 0
    not_verified_count: int = 0
    total_claims: int = 0


class CapsuleMeta(BaseModel):
    """Metadata block recording run environment, commit SHA, and Gemma model ID."""

    schema_version: str = "1.0.0"
    tool_name: str = "Exitwise"
    tool_version: str = "0.1.0"
    generated_at: str
    target_repo_url: str
    target_commit_sha: str
    tested_python_versions: list[str] = Field(default_factory=list)
    gemma_model_id: str
    access_method: str
    cached: bool = False


class DependencyRecord(BaseModel):
    """Target dependency inspected."""

    name: str
    raw_spec: str
    source_manifests: list[str] = Field(default_factory=list)
    pinned_version: str | None = None
    constraint: str | None = None
    latest_version: str | None = None
    provenance: Provenance = Provenance.OBSERVED


class DependencyCapsule(BaseModel):
    """Canonical Dependency Exit Capsule containing all verified facts and AI proposals."""

    meta: CapsuleMeta
    dependency: DependencyRecord
    risk_indicators: list[RiskIndicator] = Field(default_factory=list)
    usage_summary: UsageSummary = Field(default_factory=UsageSummary)
    usage_locations: list[UsageLocation] = Field(default_factory=list)
    proposed_replacement: ReplacementCandidate | None = None
    replacement_candidates: list[ReplacementCandidate] = Field(default_factory=list)
    migration_steps: list[MigrationStep] = Field(default_factory=list)
    patch: PatchAttempt | None = None
    suggested_tests: list[DifferentialTest] = Field(default_factory=list)
    executed_test_results: list[TestRun] = Field(default_factory=list)
    compatibility_gaps: list[CompatibilityGap] = Field(default_factory=list)
    open_concerns: list[OpenConcern] = Field(default_factory=list)
    limitations: list[Limitation] = Field(default_factory=list)
    provenance_summary: TrustSummary = Field(default_factory=TrustSummary)
    overall_verdict: Literal["READY", "READY WITH GAPS", "BLOCKED", "NOT EXECUTED"] = "NOT EXECUTED"


class CapsuleIndexItem(BaseModel):
    """Summary item for the top-level index."""

    dependency_name: str
    pinned_version: str | None
    latest_version: str | None
    risk_score: float
    risk_level: str
    replacement_name: str | None
    replacement_status: str
    verdict: str
    capsule_rel_path: str
    provenance_summary: TrustSummary
