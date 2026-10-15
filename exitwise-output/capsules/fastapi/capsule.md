# Dependency Exit Capsule: `fastapi`

> **Verdict:** `NOT EXECUTED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T09:58:19.117646+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 29
- **Observed (deterministic / static / registry):** 27 (`OBSERVED`)
- **Verified by Sandbox Execution:** 0 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 2 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `fastapi`
- **Pinned Version:** `unpinned`
- **Raw Specifier:** `fastapi>=0.110.0`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `0.143.1`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|

## 3. Usage & Coupling

- **Files touched:** 3
- **Occurrences:** 24
- **Dynamic patching:** No
- **Coupling Score:** 4.8/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `api/index.py` | 5 | `fastapi.FastAPI` | import_from | runtime | `OBSERVED` |
| `api/index.py` | 5 | `fastapi.HTTPException` | import_from | runtime | `OBSERVED` |
| `api/index.py` | 6 | `fastapi.responses.HTMLResponse` | import_from | runtime | `OBSERVED` |
| `api/index.py` | 8 | `fastapi.FastAPI` | call | runtime | `OBSERVED` |
| `api/index.py` | 41 | `fastapi.HTTPException` | call | runtime | `OBSERVED` |
| `api/index.py` | 49 | `fastapi.HTTPException` | call | runtime | `OBSERVED` |
| `api/index.py` | 50 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `api/index.py` | 57 | `fastapi.HTTPException` | call | runtime | `OBSERVED` |
| `api/index.py` | 58 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `api/index.py` | 65 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `api/index.py` | 66 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 5 | `fastapi.FastAPI` | import_from | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 5 | `fastapi.HTTPException` | import_from | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 6 | `fastapi.responses.HTMLResponse` | import_from | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 6 | `fastapi.responses.JSONResponse` | import_from | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 7 | `fastapi.staticfiles.StaticFiles` | import_from | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 10 | `fastapi.FastAPI` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 44 | `fastapi.HTTPException` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 53 | `fastapi.HTTPException` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 54 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 62 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 63 | `fastapi.responses.HTMLResponse` | call | runtime | `OBSERVED` |
| `src/exitwise/web/server.py` | 79 | `fastapi.staticfiles.StaticFiles` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 33 | `fastapi` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

No automated replacement proposed (Keep & Monitor).

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|

## 6. Compatibility Gaps & Concerns

No compatibility gaps surfaced during execution.