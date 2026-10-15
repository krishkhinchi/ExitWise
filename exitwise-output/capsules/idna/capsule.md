# Dependency Exit Capsule: `idna`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:04:05.669653+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 8
- **Observed (deterministic / static / registry):** 6 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `idna`
- **Pinned Version:** `2.7`
- **Raw Specifier:** `idna==2.7`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `3.20`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0060` | **CRITICAL** | Found 4 known security vulnerabilities: GHSA-65pc-fj4g-8rjx (Internationalized Domain Names in Applications (IDNA): Specially crafted inputs to idna.encode() can bypass CVE-2024-3651 fix); GHSA-jjg7-2v4v-x38h (Internationalized Domain Names in Applications (IDNA) vulnerable to denial of service from specially crafted inputs to idna.encode); PYSEC-2024-60 (A vulnerability was identified in the kjd/idna library, specifically within the `idna.encode()` function, affecting vers) | GHSA-65pc-fj4g-8rjx, GHSA-jjg7-2v4v-x38h, PYSEC-2024-60, PYSEC-2026-215 | `OBSERVED` |
| `RISK-0061` | **MEDIUM** | Pinned at 2.7, 1 major version behind latest (3.20) | EV-PYPI-0056 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 1
- **Occurrences:** 1
- **Dynamic patching:** No
- **Coupling Score:** 1.2/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `pyproject.toml` | 22 | `idna` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.