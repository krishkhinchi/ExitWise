# Product Requirements Document: Exitwise

**Product:** Exitwise, an AI-assisted Dependency Exit Capsule generator
**Hackathon:** Building Resilient Open-Source Software with AI, Track 1 (Gemma 4: Dependency Resilience)
**Target repository:** https://github.com/rishrek/LinkWatch (Python CLI link and uptime checker)
**Runtime constraint:** Python 3.12 and 3.13 only. Not compatible with Python 3.14.
**Status:** Draft v1.0
**Date:** 15 October 2026

---

## 1. Overview

### 1.1 Summary
Exitwise is an open-source developer tool that inspects a real Python repository, finds dependencies that put it at risk, maps exactly how each is used, uses Gemma 4 to propose a replacement and migration path, actually executes tests against both the original and the replacement, and produces a reusable, verifiable **Dependency Exit Capsule** per dependency.

### 1.2 Core principle
> **Gemma proposes; the machine verifies; the capsule records which is which.**

AI-generated recommendations must always be visibly separated from information that was observed or verified through execution. This principle drives the data model, the UI and the acceptance criteria.

### 1.3 Problem statement
Open-source projects depend on third-party packages that become outdated, unmaintained, deprecated, vulnerable, incompatible with new Python versions, or hard to replace. Maintainers usually discover this only when something breaks. Migration is slow, and nobody can easily verify an AI's migration advice. Generic AI suggestions are not trusted because they aren't tied to the repository's real code, real test runs or real evidence.

### 1.4 Vision
Make dependency migration transparent, testable and reusable. A maintainer should be able to hand a capsule to a teammate, a contributor or CI and have them reproduce the evidence without trusting the AI.

---

## 2. Goals, Non-Goals and Success Metrics

### 2.1 Goals
| ID | Goal |
|----|------|
| G1 | Dynamically identify at-risk dependencies from live repository and registry data, with no pre-written answers. |
| G2 | Locate where and how every flagged dependency is used, including indirect coupling such as monkey-patching. |
| G3 | Use Gemma 4 meaningfully for triage, usage analysis, replacement proposals, migration patches and test generation. |
| G4 | Execute tests for the original and the replacement wherever technically feasible, and be honest where it isn't. |
| G5 | Compare observed results and surface compatibility gaps and unresolved risks. |
| G6 | Emit a reusable, schema-validated, reproducible capsule per dependency. |
| G7 | Keep AI-generated and observed or verified information strictly separate everywhere. |

### 2.2 Non-Goals
- Not an automatic "merge-ready" upgrade bot. Exitwise prepares and evidences migrations; the maintainer decides.
- Not a general SAST or vulnerability scanner. Vulnerability data is one risk indicator among several.
- No support for non-Python ecosystems in v1 (JS, Go, Rust and so on).
- No fine-tuning or self-hosting of Gemma in v1. Hosted API access only.
- No Python 3.14 support, by constraint.

### 2.3 Success metrics
| Metric | Target |
|--------|--------|
| Dependencies from the target repo flagged and given a capsule | 100% of flagged dependencies (not only the top one) |
| Capsule items carrying a provenance tag | 100% |
| Hallucinated replacement packages that reach execution | 0 (all rejected by validation) |
| Flagged dependencies with at least one executed baseline-vs-candidate run | at least 60%; the rest carry an explicit `NOT_EXECUTED` reason |
| `exitwise verify` reproduces a capsule's recorded results | yes, or reports drift clearly |
| Full run on the target repo | under 10 minutes on a typical laptop |
| Both Python 3.12 and 3.13 pass in CI | yes |

---

## 3. Users and Use Cases

### 3.1 Personas
- **Maya, the solo maintainer.** Maintains a small project, has little time, wants to know what to fix first and whether a swap is safe.
- **Dev, the contributor.** Wants a ready-made, evidenced migration plan to turn into a pull request.
- **Hackathon judge.** Wants to quickly see that Gemma 4 is central, that results are dynamic and that claims are verified.

### 3.2 User stories
| ID | Story |
|----|-------|
| US1 | As a maintainer, I run one command on my repo and get a ranked list of risky dependencies with evidence. |
| US2 | As a maintainer, I see every file and line where a dependency is used and how tightly it's coupled. |
| US3 | As a maintainer, I get a proposed replacement with ordered migration steps and a patch. |
| US4 | As a maintainer, I see test results for before and after, so I know what actually works. |
| US5 | As a contributor, I get a capsule I can re-run with one command to confirm the evidence. |
| US6 | As a reviewer, I can tell at a glance which statements are AI-generated and which were measured. |
| US7 | As a maintainer with no API access, I still get the deterministic analysis, with AI sections clearly marked "not generated". |

---

## 4. Scope and Pipeline

Six stages, each independently runnable and mapped to the challenge requirements.

| Stage | Command | Challenge requirement |
|-------|---------|-----------------------|
| 1. Identify risk | `exitwise scan` | Req. 1: identify potentially at-risk dependencies |
| 2. Map usage | `exitwise usage` | Req. 2: determine where and how each is used |
| 3. Propose | `exitwise propose` | Req. 3: replacement and migration approach for all |
| 4. Execute | `exitwise test` | Req. 4: run tests on original and replacement |
| 5. Compare | `exitwise compare` | Req. 5: compatibility gaps and unresolved risks |
| 6. Capsule | `exitwise capsule` | Req. 6: reusable Dependency Exit Capsule |
| All | `exitwise run` | End to end |

---

## 5. Functional Requirements

Priority: **P0** = must ship, **P1** = should ship, **P2** = nice to have.

### 5.1 Repository ingestion
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-1.1 | Accept a local path or a Git URL. Clone into a temp workspace. Never modify the original. | P0 |
| FR-1.2 | Record the target commit SHA and URL in capsule metadata. | P0 |
| FR-1.3 | Detect the repo's test command (Makefile, pyproject, pytest config). | P0 |
| FR-1.4 | Fail with a clear error on Python outside 3.12 to 3.13 (exit code 2). | P0 |

### 5.2 Risk identification (Stage 1)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-2.1 | Parse `requirements*.txt` (including `-r`, markers, extras), `pyproject.toml` (PEP 621 and optional groups), `setup.cfg`, `setup.py` (AST only, never executed), `Pipfile`, and install lines in Dockerfile and Makefile. | P0 |
| FR-2.2 | Detect manifest drift: the same package with conflicting constraints across files. | P0 |
| FR-2.3 | Fetch live PyPI metadata: latest version, release dates, yanked flags, `requires_python`, classifiers, deprecation language. | P0 |
| FR-2.4 | Query OSV.dev for known vulnerabilities per pinned version. | P0 |
| FR-2.5 | Query GitHub for archived status and last push where a source URL exists. Degrade gracefully on rate limits. | P1 |
| FR-2.6 | Run resolver checks (`pip check` or dry-run install) in a throwaway venv to detect conflicts. | P0 |
| FR-2.7 | Install-and-import smoke test per package on Python 3.12 and 3.13. | P1 |
| FR-2.8 | Surface deprecation warnings actually triggered by running the repo's tests. | P1 |
| FR-2.9 | Detect undeclared imports and runtime pins of build tooling. | P1 |
| FR-2.10 | Compute a transparent risk score. Each indicator has severity, source, observed value and an evidence ID. | P0 |
| FR-2.11 | Distinguish "old but stable" from "old and broken" to avoid false alarms. | P1 |
| FR-2.12 | Gemma produces an AI triage explanation over the deterministic evidence, labelled AI. | P0 |
| FR-2.13 | Process all flagged dependencies by default. Support `--only a,b` to narrow. | P0 |

### 5.3 Usage mapping (Stage 2)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-3.1 | AST scan of all `.py` files for imports, aliases, submodule imports, attribute chains, calls, inheritance, decorators and annotations. | P0 |
| FR-3.2 | Detect dynamic patching of dependency objects (for example, assigning to a module or class attribute). | P0 |
| FR-3.3 | Scan non-Python files (templates, TOML, Dockerfile, Makefile, CI config) for references. | P1 |
| FR-3.4 | Map import names to distribution names correctly (for example `dateutil` to `python-dateutil`). | P0 |
| FR-3.5 | Per usage record: file, line, column, symbol, kind, snippet (±3 lines), context (runtime, test, config). | P0 |
| FR-3.6 | Compute a coupling score from files touched, distinct symbols, patching or inheritance, and test-only vs runtime. | P1 |
| FR-3.7 | Gemma characterises usage depth and risk from snippets (AI-labelled). Locations stay OBSERVED. | P0 |

### 5.4 Replacement and migration (Stage 3)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-4.1 | Gemma proposes 1 to 3 ranked replacement candidates with trade-offs (PyPI names or stdlib only). | P0 |
| FR-4.2 | Every candidate is validated: exists on PyPI or stdlib, declares Python 3.12 and 3.13 compatibility, installs successfully. Failures are recorded as rejected with a reason. | P0 |
| FR-4.3 | Gemma produces ordered migration steps, each tagged `AI_GENERATED` until executed. | P0 |
| FR-4.4 | Gemma produces a unified diff. Check it with `git apply --check`, apply to a sandbox copy only. | P0 |
| FR-4.5 | If the patch fails, run a bounded repair loop (max 2 attempts) and record every attempt. | P1 |
| FR-4.6 | "Keep and monitor" is a valid recommendation when evidence doesn't justify migration. | P1 |

### 5.5 Test execution (Stage 4)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-5.1 | Create isolated environments (prefer `uv`, fall back to `venv`). No global installs. | P0 |
| FR-5.2 | Baseline run: repo as-is. Record exit code, pass/fail counts, duration, output tail, `pip freeze`, interpreter version. | P0 |
| FR-5.3 | Candidate run: patched copy with the replacement. Same recording. | P0 |
| FR-5.4 | Gemma generates differential compatibility tests for the APIs the repo actually uses. Run against both sides. Test code is AI-labelled; results are OBSERVED. | P0 |
| FR-5.5 | Matrix execution on Python 3.12 and 3.13 where available. Record "not available, skipped" otherwise. | P1 |
| FR-5.6 | Flake guard: re-run failures once and mark results `flaky` when they differ. | P1 |
| FR-5.7 | When not feasible, record `NOT_EXECUTED` with a concrete reason. Never infer a pass. | P0 |
| FR-5.8 | Run dependencies in parallel with a concurrency cap. | P1 |
| FR-5.9 | Optional `--docker` runner. | P2 |

### 5.6 Comparison and gaps (Stage 5)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-6.1 | Deterministic diff: newly failing tests, new warnings, import errors, behavioural differences from differential tests, API symbols with no equivalent. | P0 |
| FR-6.2 | Each gap has an ID, description, evidence IDs, severity, status (`OBSERVED` or `AI_HYPOTHESIS`) and suggested resolution. | P0 |
| FR-6.3 | Gemma writes the narrative after facts are fixed. A validator rejects any pass/fail claim not present in evidence. | P0 |
| FR-6.4 | Open concerns and limitations are a mandatory section (untested paths, licence differences, transitive changes, skipped steps). | P0 |
| FR-6.5 | Rough performance delta, labelled indicative. | P2 |

### 5.7 Capsule (Stage 6)
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-7.1 | One capsule directory per dependency plus a top-level index. | P0 |
| FR-7.2 | Outputs: `capsule.json` (canonical, versioned), `capsule.schema.json`, `capsule.md`, self-contained `capsule.html`, `evidence/`, `reproduce.sh` and `reproduce.ps1`, `MANIFEST.sha256`. | P0 |
| FR-7.3 | Required sections: dependency details, risk indicators, usage locations, proposed replacement, migration steps, suggested tests, executed test results, compatibility gaps, open concerns, limitations. Empty arrays allowed, never omitted. | P0 |
| FR-7.4 | Meta block: tool version, timestamp, target repo URL and commit, Python versions, Gemma model ID as returned by the API, access method. | P0 |
| FR-7.5 | Every leaf item carries one provenance value: `OBSERVED`, `VERIFIED_BY_EXECUTION`, `AI_GENERATED`, `AI_VERIFIED`, `NOT_VERIFIED`. A schema check fails if missing. | P0 |
| FR-7.6 | Trust summary at the top of each capsule with counts per provenance type, plus a legend. | P0 |
| FR-7.7 | `exitwise verify <dir>` checks hashes, re-runs recorded commands in a fresh sandbox and reports reproducible or drifted. | P1 |
| FR-7.8 | `exitwise capsule export --format md\|html\|json`. | P1 |

### 5.8 Gemma 4 integration
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-8.1 | Use the hosted Gemini API via the official `google-genai` SDK. Confirm the Gemma 4 model ID from the official docs or the models list; make it configurable (`EXITWISE_MODEL`). | P0 |
| FR-8.2 | API key from `GEMINI_API_KEY` or `GOOGLE_API_KEY`. Never logged, committed or written into capsules. Provide `.env.example`. | P0 |
| FR-8.3 | Structured output validated by pydantic v2, with a repair loop of at most 2 retries. | P0 |
| FR-8.4 | Backoff with jitter, request budget per run, timeouts. Show request and token counts in the run summary. | P0 |
| FR-8.5 | Grounding: prompts receive only observed evidence with evidence IDs. Claims must cite IDs. Uncited claims are marked `ai_unsupported`; claims citing unknown IDs are rejected. | P0 |
| FR-8.6 | If the API is unreachable or no key is set, continue with deterministic stages and mark AI sections "not generated". Never fabricate. | P0 |
| FR-8.7 | Send only minimal snippets and metadata per prompt, not the whole repo. | P0 |
| FR-8.8 | Documentation states model name, version, access method and applicable terms (Gemma Apache 2.0 per the brief, linked to the official pages). | P0 |

### 5.9 CLI and UI
| ID | Requirement | Pri |
|----|-------------|-----|
| FR-9.1 | `exitwise run <path\|url> [--only] [--python 3.12\|3.13\|both] [--model] [--offline-signals] [--out] [--docker] [--no-cache]`. | P0 |
| FR-9.2 | Live Rich display: row per dependency, stage status, spinner, final verdict badge (`READY`, `READY WITH GAPS`, `BLOCKED`, `NOT EXECUTED`). | P0 |
| FR-9.3 | Exit codes: 0 success, 2 bad environment, 3 target unreachable, 4 partial results. | P1 |
| FR-9.4 | Self-contained HTML capsule report with no external requests, styled per design.md. | P0 |
| FR-9.5 | Local web dashboard (FastAPI plus Server-Sent Events) showing live progress and capsule browsing. | P2 |
| FR-9.6 | Caching is off by default. Any cached response is flagged `cached` in the capsule. | P1 |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Compatibility | `requires-python = ">=3.12,<3.14"`. CI on 3.12 and 3.13. Runtime guard rejects other versions. |
| NFR-2 | Dependency hygiene | Exitwise's own dependencies are minimal, current, maintained and declared directly. Audit (pip-audit or OSV) is clean in CI. |
| NFR-3 | Security | Sandbox uses temp dirs, scrubbed environment (no API keys), timeouts and resource limits. `SECURITY.md` documents the threat model for executing third-party and AI-written code. Never execute `setup.py`; use AST only. |
| NFR-4 | Privacy | Document exactly what is sent to the Gemma API. Redact secrets from logs and capsules. |
| NFR-5 | Reproducibility | Capsules include interpreter versions, `pip freeze`, commands and hashes. |
| NFR-6 | Performance | Full run on the target repo under 10 minutes. Stages run in parallel across dependencies. |
| NFR-7 | Reliability | Graceful degradation for offline, rate-limited, missing-interpreter and missing-API-key cases. |
| NFR-8 | Quality | `ruff` clean, `mypy --strict` on core modules, unit and integration tests, golden-file test for schema stability. |
| NFR-9 | Accessibility | HTML report meets WCAG AA contrast, keyboard navigation, semantic headings, with no colour-only signalling. |
| NFR-10 | Licensing | Open source (Apache-2.0 or MIT) with a LICENSE file. |

---

## 7. Technical Architecture

### 7.1 Components
`ingest` (repo, manifests) → `signals` (PyPI, OSV, GitHub, resolver, py-compat, scoring) → `usage` (AST scanner, import map, coupling) → `ai` (client, schemas, grounding, prompts) → `sandbox` (envs, runner, patching) → `compare` (diff, gaps) → `capsule` (builder, schema, render, verify) → `web` (optional server and static UI).

### 7.2 Stack
Python 3.12/3.13, `click` or `typer`, `rich`, `pydantic` v2, `httpx`, `packaging`, stdlib `tomllib`, `jinja2` 3.x, `google-genai`, `pytest`, `ruff`, `mypy`. Optional: `fastapi`, `uvicorn`.

### 7.3 Core data model (abridged)
- `Evidence { id, source, kind, observed_value, timestamp, raw_ref }`
- `RiskIndicator { id, dependency, severity, source, observed_value, evidence_ids, provenance }`
- `UsageLocation { file, line, col, symbol, kind, snippet, context, provenance }`
- `Replacement { name, kind(pypi|stdlib), tradeoffs, validation{exists, py_compat, installs}, status(accepted|rejected), provenance }`
- `MigrationStep { order, description, provenance }`
- `TestRun { side(baseline|candidate), python, command, exit_code, passed, failed, duration, output_ref, flaky, provenance }`
- `Gap { id, description, evidence_ids, severity, status, resolution, provenance }`
- `Capsule { meta, dependency, risk_indicators[], usage_locations[], proposed_replacement, migration_steps[], suggested_tests[], executed_test_results[], compatibility_gaps[], open_concerns[], limitations[], provenance_summary }`

### 7.4 Provenance semantics
| Value | Meaning |
|-------|---------|
| `OBSERVED` | Measured directly by the tool (fetched metadata, AST finding, command output). |
| `VERIFIED_BY_EXECUTION` | A claim confirmed by a recorded test run. |
| `AI_GENERATED` | Produced by Gemma, not yet verified. |
| `AI_VERIFIED` | AI-proposed and later confirmed by execution (linked to the evidence). |
| `NOT_VERIFIED` | Could not be checked, with reason. |

---

## 8. UX Requirements

- Visual design follows `design.md` (tokens as CSS custom properties, light and dark modes if specified).
- Provenance badges are the most deliberate element: distinct colour, icon and label per type.
- Each capsule opens with the trust summary and legend, then sections in the order of FR-7.3.
- Code snippets show file and line. Diffs show before and after. Test results show baseline and candidate side by side.
- The HTML report works offline as a single file.

---

## 9. Documentation Deliverables

| File | Contents |
|------|----------|
| `README.md` | Pitch, provenance principle, Mermaid architecture, quickstart for 3.12 and 3.13 (3.14 unsupported), API key setup, model ID, version, access method, terms, sample output, limitations. |
| `docs/capsule-spec.md` | Capsule schema and provenance semantics. |
| `docs/gemma-usage.md` | Each Gemma job, its validation and failure handling. |
| `docs/demo.md` | Three-minute demo script. |
| `docs/decisions.md` | Defaults chosen and why. |
| `SECURITY.md` | Sandbox threat model. |
| `LICENSE` | Open-source licence. |

---

## 10. Testing Strategy

- **Unit:** manifest parsing edge cases, drift detection, scoring, AST scanner (aliases, submodules, monkey-patching), import-to-distribution mapping, provenance enforcement, grounding validator, patch apply and repair loop with mocked Gemma.
- **Integration:** fixture repo with a known-bad dependency, end to end with a mocked Gemma client (mocks only in tests).
- **Live:** one `@pytest.mark.live` test against the target repo with a real key (skipped without a key).
- **Golden files:** `capsule.json` schema stability.
- **Accessibility:** automated contrast and semantics check of the HTML report.

---

## 11. Milestones

| Phase | Deliverable | Pri |
|-------|-------------|-----|
| 1. Foundation | Scaffold, Python guard, models, manifest parsing, PyPI and OSV signals, scoring, `scan` prints a real ranked table. | P0 |
| 2. Usage | AST scanner with patch detection, import mapping, coupling score. | P0 |
| 3. Gemma | Client, schemas, grounding validator, triage, replacement, migration and test-gen jobs, candidate validation. | P0 |
| 4. Execution | Sandbox, baseline vs candidate, differential tests, 3.12 and 3.13 matrix, flake guard. | P0 |
| 5. Compare and capsule | Gap analysis, capsule builder, JSON Schema, MD and HTML renderers, hashes, `verify`. | P0/P1 |
| 6. Polish | Dashboard, README, docs, CI, demo script. | P1/P2 |

**Scope triage:** P0 = phases 1 to 5 working on at least three dependencies with honest `NOT_EXECUTED` handling. P1 = HTML polish and `verify`. P2 = web server, Docker runner, performance delta.

---

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemma hallucinates packages or APIs | Wrong migration advice | Deterministic validation of every candidate; grounding validator; AI labels. |
| Gemma API rate limits or outages | Stalled run | Backoff, request budget, offline mode with AI sections marked "not generated". |
| Gemma 4 model ID or SDK behaviour differs from assumptions | Integration failure | Read official docs and list models first; model ID configurable. |
| Repo tests don't cover a dependency | Weak evidence | Differential tests on the exact APIs used; record `NOT_EXECUTED` or `NOT_VERIFIED` honestly. |
| Old pins won't install on 3.12/3.13 (for example `nose==1.3.7`) | Baseline fails | Record as an observed finding; it is itself a risk signal. |
| Executing untrusted or AI-written code | Security | Sandbox, scrubbed env, timeouts, optional Docker, documented threat model. |
| Python 3.13 interpreter missing | Matrix gap | Detect and skip with a recorded reason. |
| Scope too large for the time available | Incomplete demo | P0/P1/P2 triage; the thin end-to-end path comes first. |
| Overfitting to LinkWatch | Fails "dynamic" requirement | No special-casing or embedded answers; fixture repo tests prove generality. |

---

## 13. Traceability to the Hackathon Brief

| Brief requirement | Covered by |
|-------------------|------------|
| Original, open-source AI-powered developer tool | Section 1, NFR-10 |
| Works on the organizer repo, dynamic analysis, no pre-written outputs | FR-1.x, FR-2.x, FR-8.6, Risk "Overfitting" |
| Gemma 4 meaningful; model, version, access method and terms documented | FR-8.1 to FR-8.8, Section 9 |
| Req. 1 Identify at-risk dependencies | FR-2.x |
| Req. 2 Usage of all identified dependencies | FR-3.x, FR-2.13 |
| Req. 3 Replacement and migration for all | FR-4.x |
| Req. 4 Execute tests on original and replacement | FR-5.x |
| Req. 5 Compare results, gaps, risks | FR-6.x |
| Req. 6 Dependency Exit Capsule with all listed sections | FR-7.x |
| AI recommendations separated from verified information | G7, FR-7.5, FR-7.6, Section 7.4 |
| Python 3.12 and 3.13 only | NFR-1, FR-1.4 |

---

## 14. Open Questions

1. Exact Gemma 4 model ID and any structured-output support on the hosted API (confirm from official docs and the models list).
2. Should the default licence be Apache-2.0 or MIT?
3. Is Docker available in the demo environment, or is the venv sandbox the only option?
4. Will `design.md` define dark mode and a component library for the HTML report?
5. Is a hosted dashboard desirable, or is the static HTML report enough for judging?

---

## 15. Definition of Done

- [ ] `exitwise run https://github.com/rishrek/LinkWatch` completes on Python 3.12 and 3.13, and fails cleanly on 3.14.
- [ ] Risk indicators come from live data and local checks, including a manifest-drift finding and a monkey-patch usage finding.
- [ ] Every flagged dependency gets usage locations, a validated replacement proposal and a capsule.
- [ ] Real executed baseline-vs-candidate results exist for at least some dependencies; the rest state why not.
- [ ] Hallucinated replacements are caught and recorded as rejected.
- [ ] Every capsule item has a provenance tag; the HTML shows the trust summary and legend.
- [ ] `exitwise verify` reproduces or flags drift.
- [ ] Gemma model ID, access method and terms are documented; the model ID appears in every capsule.
- [ ] No secrets in the repo, logs or capsules. CI green on 3.12 and 3.13. Self-audit clean.
- [ ] README, docs, demo script and LICENSE complete.
