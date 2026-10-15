# Exitwise 🔬

> **Gemma 4 Powered Dependency Exit Capsule Generator**  
> *Resilient Open-Source Software — Track 1: Gemma 4 · Dependency Resilience*

[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)](#testing)

**Exitwise** is an open-source CLI + local web dashboard that:

1. **Analyses** a real Python repository — scanning every manifest, AST, template and config file  
2. **Signals** dependency health across 5 dimensions: PyPI staleness · OSV CVEs · GitHub abandonment · Python 3.12/3.13 compatibility · version pinning  
3. **Characterises** how every at-risk dependency is used — including monkey-patching, inheritance, and transitive imports  
4. **Proposes** a validated replacement candidate using **Gemma 4** via the Google AI API  
5. **Generates** a migration plan + unified diff — and *executes* both baseline and candidate test suites in an isolated sandbox  
6. **Records** everything into a cryptographically-signed **Dependency Exit Capsule** (JSON + Markdown + HTML) where every claim is tagged as `OBSERVED`, `VERIFIED_BY_EXECUTION`, `AI_GENERATED`, or `NOT_VERIFIED` — never mixing facts with speculation

---

## Core Principle

> *Gemma proposes; the machine verifies; the capsule records which is which.*

All AI-generated content carries `provenance=AI_GENERATED`. All test results carry `provenance=VERIFIED_BY_EXECUTION`. All signal data from PyPI/OSV carries `provenance=OBSERVED`. Hallucinated replacement packages are **deterministically rejected** by grounded validation against live PyPI and stdlib before any AI content reaches the capsule.

---

## Demo: LinkWatch

Exitwise was developed against [`rishrek/LinkWatch`](https://github.com/rishrek/LinkWatch), a real Python project with rich dependency risk signals including:

- `pydantic==1.10.13` pinned in `requirements.txt` but `>=2` in `pyproject.toml` → **manifest drift**
- `idna==2.7` → **4 CVEs** (CVSS HIGH)
- `setuptools==75.8.0` → **3 CVEs + 9 major versions behind**
- `requests` with dynamic **monkey-patching** in `linkwatch/http_patch.py` → coupling score **8.5/10**
- `nose` → **incompatible with Python 3.12+** (removed `imp` module)

---

## Quickstart

### Requirements

- Python 3.12 or 3.13 (**not** 3.11, **not** 3.14)
- A `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/)
- Git (for repository cloning)

### Installation

```bash
git clone https://github.com/rishrek/exitwise
cd exitwise
pip install -e ".[dev]"
```

### Set your API key

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-key-here"

# Linux / macOS
export GEMINI_API_KEY="your-key-here"
```

Or copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`.

### Run

```bash
# Stage 1 — Scan signals & rank risk
python -m exitwise scan https://github.com/rishrek/LinkWatch

# Stage 2 — Map AST usage & coupling
python -m exitwise usage https://github.com/rishrek/LinkWatch

# Full pipeline — Gemma proposes, sandbox verifies, capsule records
python -m exitwise run https://github.com/rishrek/LinkWatch --output ./capsules

# Launch web dashboard
python -m exitwise dashboard ./capsules

# Verify capsule integrity (SHA-256)
python -m exitwise verify ./capsules/requests
```

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stage 1 · Ingest & Signals                                                  │
│  prepare_workspace()  ──►  scan_all_manifests()  ──►  fetch_pypi_metadata() │
│  query_osv_vulnerabilities()  ──►  fetch_github_health()                    │
│  evaluate_python_compatibility()  ──►  assess_dependency_risk()             │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ RiskIndicator[] (provenance=OBSERVED)
┌────────────────────────────────────▼───────────────────────────────────────┐
│ Stage 2 · Usage Analysis                                                    │
│  scan_repo_usage_for_dependency()  (alias tracking, patch detection)        │
│  scan_non_python_references()  (Jinja2, TOML, YAML, Dockerfile)            │
│  compute_usage_coupling()  ──►  UsageSummary (coupling_score, is_patched)  │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ UsageLocation[] (provenance=OBSERVED)
┌────────────────────────────────────▼───────────────────────────────────────┐
│ Stage 3 · Gemma AI Jobs (AI_GENERATED)                                      │
│  ① characterize_usage()           → narrative + hazards                     │
│  ② propose_replacement()          → ValidatedCandidate[] (grounded check)  │
│  ③ generate_migration_plan()      → ordered steps + unified diff            │
│  ④ generate_differential_tests()  → pytest file exercising both APIs        │
│  ⑤ explain_results()             → editorial summary for capsule           │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ MigrationPlan + diff
┌────────────────────────────────────▼───────────────────────────────────────┐
│ Stage 4 · Sandbox Execution (VERIFIED_BY_EXECUTION)                         │
│  execute_patch_with_repair()  (bounded retry loop)                          │
│  run_repo_suite(baseline)     ──►  TestRunResult                            │
│  run_repo_suite(candidate)    ──►  TestRunResult                            │
│  run_differential_test()      ──►  baseline_passed / candidate_passed       │
│  compare_test_runs()          ──►  DiffSummary (regression map)             │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ DiffSummary
┌────────────────────────────────────▼───────────────────────────────────────┐
│ Stage 5 · Capsule Assembly & Rendering                                      │
│  build_dependency_capsule()  ──►  DependencyCapsule (Pydantic v2)           │
│  verify_capsule_directory()  ──►  SHA-256 hash manifest                     │
│  render_capsule_markdown()   ──►  capsule.md                                │
│  render_capsule_html()       ──►  capsule.html (self-contained, dark theme) │
│  render_index_html()         ──►  index.html dashboard                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Provenance System

Every field in every output carries a `provenance` tag:

| Tag | Meaning |
|-----|---------|
| `OBSERVED` | Fetched from a deterministic API (PyPI, OSV, GitHub) — no AI |
| `VERIFIED_BY_EXECUTION` | Confirmed by actually running the test suite in an isolated venv |
| `AI_GENERATED` | Produced by Gemma 4 — treat as a suggestion, not a fact |
| `AI_VERIFIED` | AI claim that was subsequently verified by execution |
| `NOT_VERIFIED` | Could not be confirmed by either execution or a live API |

AI-proposed replacement packages are **grounded** — validated against live PyPI and stdlib before appearing in the capsule. Hallucinated package names never reach the output.

---

## Output Files

For each analysed dependency, `exitwise run` produces a directory:

```
capsules/
├── index.html                    ← Full-run dashboard (self-contained HTML)
├── requests/
│   ├── capsule.json              ← Machine-readable Dependency Exit Capsule
│   ├── capsule.schema.json       ← JSON Schema for validation
│   ├── capsule.md                ← Markdown report with provenance tags
│   ├── capsule.html              ← Self-contained dark-theme HTML report
│   ├── sha256.manifest           ← Hash of every evidence file
│   ├── verify.sh / verify.ps1   ← Reproducibility scripts
│   └── evidence/
│       ├── EV-PYPI-0001.json     ← Raw PyPI API response
│       ├── EV-OSV-0002.json      ← Raw OSV vulnerability data
│       └── EV-EXEC-BASE-0003.json ← Baseline test run result
```

---

## CLI Reference

```
python -m exitwise [OPTIONS] COMMAND [ARGS]

Commands:
  scan        Stage 1 only — signals and risk table
  usage       Stage 2 only — AST usage and coupling map
  run         Full pipeline — generates Exit Capsules
  verify      SHA-256 integrity check + reproducibility test
  dashboard   Start local FastAPI server for live dashboard

Options for `run`:
  --only TEXT        Comma-separated list of deps to process
  --model TEXT       Gemini model ID (default: gemini-2.0-flash)
  --output PATH      Output directory (default: ./exitwise-output)
  --offline-signals  Use cached PyPI/OSV data (no network)
  --top N            Maximum high-risk deps to analyse (default: 5)
```

---

## Testing

```bash
# Unit tests (no API key required)
pytest tests/ -v -m "not live"

# Live integration tests (requires GEMINI_API_KEY)
pytest tests/ -v -m live
```

**Test coverage areas:**

- Manifest parsing (requirements.txt, pyproject.toml PEP-621, Poetry, setup.py AST)
- Manifest drift detection
- AST scanner: imports, aliases, monkey-patch detection, inheritance
- Coupling score calculation
- Python 3.12/3.13 compatibility evaluation
- Provenance enforcement (every model field validated)
- Grounding validator: hallucinated packages rejected, stdlib always accepted
- Capsule schema validation

---

## Architecture Notes

### Why not `with tempfile.TemporaryDirectory()`?

The sandbox execution stage previously used a context manager for the candidate workspace — but variables captured *inside* the `with` block (test results, diff summaries) would be garbage-collected before the capsule builder could read them. Exitwise now uses `tempfile.mkdtemp()` with an explicit `finally: shutil.rmtree(...)` to guarantee cleanup while keeping all results live until capsule assembly completes.

### Monkey-Patch Risk Detection

`ast_scanner.py` uses a two-pass AST walk:
1. First pass: collect all import aliases (`import requests as req` → `req`)
2. Second pass: detect `Assign` nodes where the target is an `Attribute` chain rooted on an imported alias → flagged as `kind="patch"` with full dotted symbol name

This is how `requests.Session.request = _request` in LinkWatch is reliably caught.

### Hallucination Guard

`grounding.py` performs three deterministic checks **before** any AI-proposed replacement enters the capsule:
1. Is the package name a Python stdlib module? → `ACCEPTED` as `kind=stdlib`
2. Does the package exist on PyPI? (live HTTP check or cache) → `REJECTED` if 404
3. Is the package itself vulnerable or deprecated? → downgraded to `DEGRADED`

---

## License

[Apache 2.0](LICENSE) — open-source, attribution required, no warranty.

---

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting. The CLI strips all API keys and sensitive environment variables before spawning child processes.
