# Dependency Exit Capsule: `python-dateutil`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:05:03.610038+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 9
- **Observed (deterministic / static / registry):** 7 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `python-dateutil`
- **Pinned Version:** `unpinned`
- **Raw Specifier:** `python-dateutil`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `2.9.0.post0`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0065` | **MEDIUM** | No new PyPI release in 957 days (~2.6 years, last: 2024-03-01) | EV-PYPI-0061 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 3
- **Dynamic patching:** No
- **Coupling Score:** 2.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/dates.py` | 1 | `dateutil.parser` | import_from | runtime | `OBSERVED` |
| `linkwatch/dates.py` | 8 | `dateutil.parser` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 23 | `python-dateutil` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.