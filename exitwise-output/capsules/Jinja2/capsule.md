# Dependency Exit Capsule: `Jinja2`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:03:26.556098+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 24
- **Observed (deterministic / static / registry):** 13 (`OBSERVED`)
- **Verified by Sandbox Execution:** 3 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 8 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `Jinja2`
- **Pinned Version:** `2.11.3`
- **Raw Specifier:** `Jinja2==2.11.3`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `3.1.6`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0030` | **CRITICAL** | Found 8 known security vulnerabilities: GHSA-cpwx-vrp4-4pq7 (Jinja2 vulnerable to sandbox breakout through attr filter selecting format method); GHSA-h5c8-rqwp-cp95 (Jinja vulnerable to HTML attribute injection when passing user input as keys to xmlattr filter); GHSA-h75v-3vvj-5mfj (Jinja vulnerable to HTML attribute injection when passing user input as keys to xmlattr filter) | GHSA-cpwx-vrp4-4pq7, GHSA-h5c8-rqwp-cp95, GHSA-h75v-3vvj-5mfj, GHSA-q2x7-8rv6-6q7h, PYSEC-2026-1471, PYSEC-2026-1473, PYSEC-2026-1474, PYSEC-2026-1475 | `OBSERVED` |
| `RISK-0031` | **MEDIUM** | Pinned at 2.11.3, 1 major version behind latest (3.1.6) | EV-PYPI-0026 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 7
- **Dynamic patching:** No
- **Coupling Score:** 3.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/report.py` | 3 | `jinja2.Environment` | import_from | runtime | `OBSERVED` |
| `linkwatch/report.py` | 3 | `jinja2.FileSystemLoader` | import_from | runtime | `OBSERVED` |
| `linkwatch/report.py` | 3 | `jinja2.select_autoescape` | import_from | runtime | `OBSERVED` |
| `linkwatch/report.py` | 9 | `jinja2.Environment` | call | runtime | `OBSERVED` |
| `linkwatch/report.py` | 10 | `jinja2.FileSystemLoader` | call | runtime | `OBSERVED` |
| `linkwatch/report.py` | 11 | `jinja2.select_autoescape` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 16 | `Jinja2` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `jinja2` (PyPI)
- **Validation Status:** `ACCEPTED` (Verified on PyPI (latest: 3.1.6))
- **Trade-offs:** Upgrade pin to Jinja2>=3.1.0; Resolves security CVEs
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] Step 1: Update dependency declaration in pyproject.toml or requirements.txt from Jinja2 to jinja2
2. [AI_GENERATED] Step 2: Verify that all import statements use the lowercase 'jinja2' package name
3. [AI_GENERATED] Step 3: Run the test suite to ensure template rendering remains consistent

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[MEDIUM] GAP-0078:** Differential API test 'test_diff_compat_jinja2.py' failed against candidate 'jinja2'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.