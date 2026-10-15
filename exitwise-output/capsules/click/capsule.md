# Dependency Exit Capsule: `click`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T09:59:22.843854+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 24
- **Observed (deterministic / static / registry):** 22 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `click`
- **Pinned Version:** `unpinned`
- **Raw Specifier:** `click>=8.1.0`
- **Source Manifests:** pyproject.toml
- **Latest PyPI Version:** `8.5.0`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 19
- **Dynamic patching:** No
- **Coupling Score:** 4.0/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `src/exitwise/cli.py` | 8 | `click` | import | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 45 | `click.group` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 46 | `click.version_option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 54 | `click.argument` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 55 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 56 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 137 | `click.argument` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 138 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 193 | `click.argument` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 194 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 195 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 196 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 197 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 198 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 199 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 553 | `click.argument` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 569 | `click.option` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 570 | `click.option` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 26 | `click` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.