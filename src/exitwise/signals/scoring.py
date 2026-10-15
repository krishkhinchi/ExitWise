"""Deterministic risk scoring and indicator generation with full provenance and evidence citations."""

from packaging.version import parse as parse_version
from exitwise.models import RiskIndicator, Provenance
from exitwise.signals.pypi import PyPIMetadata
from exitwise.signals.osv import VulnerabilityRecord
from exitwise.signals.github import GitHubHealth
from exitwise.signals.py_compat import PythonCompatResult

# Tooling packages that belong in build-system or dev, not pinned in runtime manifests
BUILD_TOOLING_PACKAGES = {"setuptools", "wheel", "pip", "distutils", "flit", "poetry-core"}


def assess_dependency_risk(
    package_name: str,
    pinned_version: str | None,
    pypi: PyPIMetadata,
    vulns: list[VulnerabilityRecord],
    github: GitHubHealth,
    py_compat: PythonCompatResult,
    manifest_conflict_ev_ids: list[str],
    is_runtime_dependency: bool = True,
    risk_counter_start: int = 1,
) -> tuple[list[RiskIndicator], float, str]:
    """Compute transparent risk indicators and composite score for a package."""
    indicators: list[RiskIndicator] = []
    counter = risk_counter_start

    # 1. Manifest conflict / drift
    if manifest_conflict_ev_ids:
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="HIGH",
                source="manifest_drift_detector",
                observed_value="Conflicting version constraints declared across repository manifest files",
                evidence_ids=manifest_conflict_ev_ids,
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 2. Python version incompatibility
    if not py_compat.compatible_312 or not py_compat.compatible_313:
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="CRITICAL",
                source="python_compat_evaluator",
                observed_value=f"Incompatible with target Python runtimes: {py_compat.incompat_reason or 'Excluded by classifiers or requires-python'}",
                evidence_ids=[py_compat.evidence_id],
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 3. Known CVEs from OSV.dev
    if vulns:
        vuln_strs = [f"{v.vuln_id} ({v.summary})" for v in vulns[:3]]
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="CRITICAL" if any(v.severity in ("CRITICAL", "HIGH") for v in vulns) else "HIGH",
                source="osv_api",
                observed_value=f"Found {len(vulns)} known security vulnerabilities: {'; '.join(vuln_strs)}",
                evidence_ids=[v.vuln_id for v in vulns],
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 4. Yanked release on PyPI
    if pypi.pinned_version_yanked:
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="HIGH",
                source="pypi_api",
                observed_value=f"Pinned version {pinned_version} has been yanked on PyPI ({pypi.pinned_yanked_reason or 'No reason provided'})",
                evidence_ids=[pypi.evidence_id],
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 5. Major version lag (pinned vs latest)
    if pinned_version and pypi.latest_version and pypi.latest_version != "unknown":
        try:
            p_ver = parse_version(pinned_version)
            l_ver = parse_version(pypi.latest_version)
            if hasattr(p_ver, "major") and hasattr(l_ver, "major"):
                major_gap = l_ver.major - p_ver.major
                if major_gap >= 2:
                    indicators.append(
                        RiskIndicator(
                            id=f"RISK-{counter:04d}",
                            dependency=package_name,
                            severity="HIGH",
                            source="pypi_api",
                            observed_value=f"Pinned at {pinned_version}, {major_gap} major versions behind latest ({pypi.latest_version})",
                            evidence_ids=[pypi.evidence_id],
                            provenance=Provenance.OBSERVED,
                        )
                    )
                    counter += 1
                elif major_gap == 1:
                    indicators.append(
                        RiskIndicator(
                            id=f"RISK-{counter:04d}",
                            dependency=package_name,
                            severity="MEDIUM",
                            source="pypi_api",
                            observed_value=f"Pinned at {pinned_version}, 1 major version behind latest ({pypi.latest_version})",
                            evidence_ids=[pypi.evidence_id],
                            provenance=Provenance.OBSERVED,
                        )
                    )
                    counter += 1
        except Exception:
            pass

    # 6. Days since last release (Staleness / Maintenance risk)
    if pypi.days_since_last_release is not None and pypi.days_since_last_release > 730:
        years = round(pypi.days_since_last_release / 365.25, 1)
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="HIGH" if pypi.days_since_last_release > 1095 else "MEDIUM",
                source="pypi_api",
                observed_value=f"No new PyPI release in {pypi.days_since_last_release} days (~{years} years, last: {pypi.release_date})",
                evidence_ids=[pypi.evidence_id],
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 7. Deprecation / Inactive status on PyPI or GitHub
    if pypi.is_deprecated_or_unmaintained or github.is_archived:
        reasons = list(pypi.deprecation_notes)
        ev_ids = [pypi.evidence_id]
        if github.is_archived:
            reasons.append("GitHub repository is archived (read-only)")
            ev_ids.append(github.evidence_id)

        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="HIGH",
                source="pypi_and_github_signals",
                observed_value=f"Project unmaintained or deprecated: {'; '.join(reasons)}",
                evidence_ids=ev_ids,
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # 8. Runtime pin of build tooling (e.g. setuptools==75.8.0 in requirements.txt)
    if is_runtime_dependency and package_name.lower() in BUILD_TOOLING_PACKAGES:
        indicators.append(
            RiskIndicator(
                id=f"RISK-{counter:04d}",
                dependency=package_name,
                severity="MEDIUM",
                source="manifest_analyzer",
                observed_value=f"Build/packaging tool '{package_name}' pinned directly in runtime dependencies instead of build-system",
                evidence_ids=[pypi.evidence_id] if pypi.evidence_id else [],
                provenance=Provenance.OBSERVED,
            )
        )
        counter += 1

    # Calculate transparent numeric score (0 to 100)
    score = 0.0
    for ind in indicators:
        if ind.severity == "CRITICAL":
            score += 35.0
        elif ind.severity == "HIGH":
            score += 20.0
        elif ind.severity == "MEDIUM":
            score += 10.0
        elif ind.severity == "LOW":
            score += 5.0

    score = min(score, 100.0)

    # Risk level classification
    if score >= 60.0:
        level = "CRITICAL"
    elif score >= 40.0:
        level = "HIGH"
    elif score >= 20.0:
        level = "MEDIUM"
    elif score > 0.0:
        level = "LOW"
    else:
        level = "NEGLIGIBLE"

    return indicators, score, level
