# Dependency Exit Capsule: `requests`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:04:31.316634+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 14
- **Observed (deterministic / static / registry):** 12 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `requests`
- **Pinned Version:** `2.31.0`
- **Raw Specifier:** `requests==2.31.0`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `2.34.2`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0025` | **CRITICAL** | Found 6 known security vulnerabilities: GHSA-9hjg-9r4m-mvj7 (Requests vulnerable to .netrc credentials leak via malicious URLs); GHSA-9wx4-h78v-vm56 (Requests `Session` object does not verify requests after making first request with verify=False); GHSA-gc5v-m9x4-r6x2 (Requests has Insecure Temp File Reuse in its extract_zipped_paths() utility function) | GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2, PYSEC-2026-1872, PYSEC-2026-1873, PYSEC-2026-2275 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 4
- **Occurrences:** 8
- **Dynamic patching:** YES (Hazard)
- **Coupling Score:** 8.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/checker.py` | 5 | `requests` | import | runtime | `OBSERVED` |
| `linkwatch/checker.py` | 6 | `requests.Session` | import_from | runtime | `OBSERVED` |
| `linkwatch/checker.py` | 13 | `requests.Session` | call | runtime | `OBSERVED` |
| `linkwatch/encoding.py` | 5 | `requests.utils._parse_content_type_header` | import_from | runtime | `OBSERVED` |
| `linkwatch/encoding.py` | 11 | `requests.utils._parse_content_type_header` | call | runtime | `OBSERVED` |
| `linkwatch/http_patch.py` | 1 | `requests` | import | runtime | `OBSERVED` |
| `linkwatch/http_patch.py` | 14 | `requests.Session.request` | patch | patching | `OBSERVED` |
| `pyproject.toml` | 15 | `requests` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.