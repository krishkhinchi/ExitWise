# Dependency Exit Capsule: `toml`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:04:57.007694+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 19
- **Observed (deterministic / static / registry):** 8 (`OBSERVED`)
- **Verified by Sandbox Execution:** 3 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 8 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `toml`
- **Pinned Version:** `0.10.2`
- **Raw Specifier:** `toml==0.10.2`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `0.10.2`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0015` | **HIGH** | No new PyPI release in 2174 days (~6.0 years, last: 2020-11-01) | EV-PYPI-0011 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 3
- **Dynamic patching:** No
- **Coupling Score:** 2.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/config.py` | 3 | `toml` | import | runtime | `OBSERVED` |
| `linkwatch/config.py` | 37 | `toml.load` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 13 | `toml` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `tomllib` (Python Standard Library)
- **Validation Status:** `ACCEPTED` (Candidate is a built-in Python standard library module in Python >= 3.11)
- **Trade-offs:** Standard library in Python 3.11+; Read-only (no TOML write)
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] 1. Replace 'toml' with 'tomllib' in pyproject.toml / requirements.txt
2. [AI_GENERATED] 2. Update import statements in repository modules
3. [AI_GENERATED] 3. Run automated tests in sandbox environment

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[MEDIUM] GAP-0086:** Differential API test 'test_diff_compat_toml.py' failed against candidate 'tomllib'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.