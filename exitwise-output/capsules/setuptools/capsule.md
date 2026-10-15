# Dependency Exit Capsule: `setuptools`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:01:39.882399+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 15
- **Observed (deterministic / static / registry):** 13 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `setuptools`
- **Pinned Version:** `75.8.0`
- **Raw Specifier:** `setuptools==75.8.0`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `84.0.0`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0055` | **CRITICAL** | Found 4 known security vulnerabilities: GHSA-5rjg-fvgr-3xxf (setuptools has a path traversal vulnerability in PackageIndex.download that leads to Arbitrary File Write); GHSA-h35f-9h28-mq5c (setuptools: MANIFEST.in exclusion bypass in sdist via Unicode normalization collision (NFC/NFD) on macOS APFS/HFS+); PYSEC-2025-49 (setuptools is a package that allows users to download, build, install, upgrade, and uninstall Python packages. A path tr) | GHSA-5rjg-fvgr-3xxf, GHSA-h35f-9h28-mq5c, PYSEC-2025-49, PYSEC-2026-3447 | `OBSERVED` |
| `RISK-0056` | **HIGH** | Pinned at 75.8.0, 9 major versions behind latest (84.0.0) | EV-PYPI-0051 | `OBSERVED` |
| `RISK-0057` | **MEDIUM** | Build/packaging tool 'setuptools' pinned directly in runtime dependencies instead of build-system | EV-PYPI-0051 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 7
- **Dynamic patching:** No
- **Coupling Score:** 3.0/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/resources.py` | 1 | `pkg_resources` | import | runtime | `OBSERVED` |
| `linkwatch/resources.py` | 7 | `pkg_resources.resource_filename` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 2 | `setuptools` | template_or_config_ref | config_or_template | `OBSERVED` |
| `pyproject.toml` | 3 | `setuptools` | template_or_config_ref | config_or_template | `OBSERVED` |
| `pyproject.toml` | 21 | `setuptools` | template_or_config_ref | config_or_template | `OBSERVED` |
| `pyproject.toml` | 30 | `setuptools` | template_or_config_ref | config_or_template | `OBSERVED` |
| `pyproject.toml` | 33 | `setuptools` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.