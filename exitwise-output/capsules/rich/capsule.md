# Dependency Exit Capsule: `rich`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T09:59:43.116585+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 22
- **Observed (deterministic / static / registry):** 20 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `rich`
- **Pinned Version:** `unpinned`
- **Raw Specifier:** `rich>=13.7.0`
- **Source Manifests:** pyproject.toml
- **Latest PyPI Version:** `15.0.0`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 17
- **Dynamic patching:** No
- **Coupling Score:** 4.0/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `src/exitwise/cli.py` | 9 | `rich.console.Console` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 10 | `rich.table.Table` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 11 | `rich.progress.Progress` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 11 | `rich.progress.SpinnerColumn` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 11 | `rich.progress.TextColumn` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 11 | `rich.progress.BarColumn` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 11 | `rich.progress.TimeElapsedColumn` | import_from | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 42 | `rich.console.Console` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 75 | `rich.table.Table` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 153 | `rich.table.Table` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 241 | `rich.progress.Progress` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 242 | `rich.progress.SpinnerColumn` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 243 | `rich.progress.TextColumn` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 244 | `rich.progress.BarColumn` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 245 | `rich.progress.TimeElapsedColumn` | call | runtime | `OBSERVED` |
| `src/exitwise/cli.py` | 526 | `rich.table.Table` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 27 | `rich` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.