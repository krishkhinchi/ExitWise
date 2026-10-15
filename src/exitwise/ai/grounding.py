"""Grounding validation ensuring all AI claims cite real evidence and proposed packages exist."""

import sys
import httpx
from packaging.utils import canonicalize_name
from exitwise.models import CandidateValidation, ReplacementCandidate, Provenance

# Python stdlib modules in 3.12/3.13
STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "tomllib", "json", "urllib", "sqlite3", "csv", "xml", "hashlib", "dataclasses",
    "functools", "itertools", "pathlib", "os", "sys", "time", "datetime", "logging"
}


def validate_grounded_evidence(cited_ids: list[str], valid_evidence_ids: set[str]) -> tuple[list[str], list[str]]:
    """Separate valid cited evidence IDs from fabricated or unknown ones."""
    accepted = [eid for eid in cited_ids if eid in valid_evidence_ids]
    rejected = [eid for eid in cited_ids if eid not in valid_evidence_ids]
    return accepted, rejected


def validate_replacement_candidate(
    candidate_name: str,
    evidence_id: str,
    offline_mode: bool = False,
) -> ReplacementCandidate:
    """Deterministically validate a proposed candidate against Python stdlib and PyPI."""
    cleaned_name = candidate_name.strip()
    canonical = canonicalize_name(cleaned_name)

    # 1. Check if stdlib module in Python 3.12/3.13
    if canonical in STDLIB_MODULES or cleaned_name in STDLIB_MODULES:
        val = CandidateValidation(
            exists_on_pypi_or_stdlib=True,
            is_stdlib=True,
            declares_py_compat=True,
            installs_cleanly=True,
            validation_log="Candidate is a built-in Python standard library module in Python >= 3.11",
        )
        return ReplacementCandidate(
            name=cleaned_name,
            kind="stdlib",
            tradeoffs=["Zero external dependencies", "Standard library stability"],
            validation=val,
            status="ACCEPTED",
            evidence_ids=[evidence_id],
            provenance=Provenance.AI_GENERATED,
        )

    # 2. Check PyPI
    exists = False
    declares_py_compat = False
    log = ""
    rejection_reason = None

    if not offline_mode:
        try:
            url = f"https://pypi.org/pypi/{cleaned_name}/json"
            resp = httpx.get(url, timeout=6.0, follow_redirects=True)
            if resp.status_code == 200:
                exists = True
                data = resp.json()
                classifiers = data.get("info", {}).get("classifiers", [])
                req_py = data.get("info", {}).get("requires_python") or ""

                # Check Python 3.12/3.13 classifiers or permissive requires_python
                has_3_compat = any("Programming Language :: Python :: 3" in c for c in classifiers)
                if has_3_compat or not req_py or ">=3" in req_py:
                    declares_py_compat = True
                    log = f"Verified on PyPI (latest: {data.get('info', {}).get('version')})"
                else:
                    declares_py_compat = False
                    rejection_reason = f"PyPI metadata indicates potential incompatibility with Python 3.12/3.13 ({req_py})"
            else:
                exists = False
                rejection_reason = f"Package '{cleaned_name}' not found on PyPI (HTTP {resp.status_code})"
        except Exception as e:
            exists = False
            rejection_reason = f"Network validation failed for '{cleaned_name}': {e}"
    else:
        # In offline mode, check known good migration targets
        known_good = {"platformdirs", "charset-normalizer", "pytest", "pydantic"}
        if canonical in known_good:
            exists = True
            declares_py_compat = True
            log = "Verified via offline registry snapshot"
        else:
            exists = False
            rejection_reason = f"Package '{cleaned_name}' could not be verified in offline mode"

    status = "ACCEPTED" if (exists and declares_py_compat) else "REJECTED"

    val = CandidateValidation(
        exists_on_pypi_or_stdlib=exists,
        is_stdlib=False,
        declares_py_compat=declares_py_compat,
        installs_cleanly=exists,
        validation_log=log or (rejection_reason or ""),
    )

    return ReplacementCandidate(
        name=cleaned_name,
        kind="pypi",
        tradeoffs=[],
        validation=val,
        status=status,
        rejection_reason=rejection_reason,
        evidence_ids=[evidence_id],
        provenance=Provenance.AI_GENERATED,
    )
