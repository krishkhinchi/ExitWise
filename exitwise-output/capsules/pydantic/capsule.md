# Dependency Exit Capsule: `pydantic`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:04:56.738584+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 24
- **Observed (deterministic / static / registry):** 13 (`OBSERVED`)
- **Verified by Sandbox Execution:** 3 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 8 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `pydantic`
- **Pinned Version:** `1.10.13`
- **Raw Specifier:** `pydantic==1.10.13`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `2.14.1`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0035` | **HIGH** | Conflicting version constraints declared across repository manifest files | EV-DRIFT-0001 | `OBSERVED` |
| `RISK-0036` | **MEDIUM** | Pinned at 1.10.13, 1 major version behind latest (2.14.1) | EV-PYPI-0031 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 7
- **Dynamic patching:** No
- **Coupling Score:** 5.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/config.py` | 4 | `pydantic.BaseModel` | import_from | runtime | `OBSERVED` |
| `linkwatch/config.py` | 4 | `pydantic.validator` | import_from | runtime | `OBSERVED` |
| `linkwatch/config.py` | 7 | `class Site(pydantic.BaseModel)` | inheritance | runtime | `OBSERVED` |
| `linkwatch/config.py` | 14 | `pydantic.validator` | call | runtime | `OBSERVED` |
| `linkwatch/config.py` | 20 | `pydantic.validator` | call | runtime | `OBSERVED` |
| `linkwatch/config.py` | 27 | `class Settings(pydantic.BaseModel)` | inheritance | runtime | `OBSERVED` |
| `pyproject.toml` | 17 | `pydantic` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `pydantic` (PyPI)
- **Validation Status:** `ACCEPTED` (Verified on PyPI (latest: 2.14.1))
- **Trade-offs:** Migrate to Pydantic v2; Significant performance gains, aligns with pyproject.toml
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] 1. Replace 'pydantic' with 'pydantic' in pyproject.toml / requirements.txt
2. [AI_GENERATED] 2. Update import statements in repository modules
3. [AI_GENERATED] 3. Run automated tests in sandbox environment

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[MEDIUM] GAP-0082:** Differential API test 'test_diff_compat_pydantic.py' failed against candidate 'pydantic'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.