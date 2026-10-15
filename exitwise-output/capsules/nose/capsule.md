# Dependency Exit Capsule: `nose`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:02:30.253474+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 22
- **Observed (deterministic / static / registry):** 9 (`OBSERVED`)
- **Verified by Sandbox Execution:** 2 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 11 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `nose`
- **Pinned Version:** `1.3.7`
- **Raw Specifier:** `nose==1.3.7`
- **Source Manifests:** requirements-dev.txt
- **Latest PyPI Version:** `1.3.7`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0010` | **CRITICAL** | Incompatible with target Python runtimes: nose relies on the 'imp' module removed in Python 3.12 and fails to import/run. | EV-COMPAT-0009 | `OBSERVED` |
| `RISK-0011` | **HIGH** | No new PyPI release in 4153 days (~11.4 years, last: 2015-06-02) | EV-PYPI-0006 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 1
- **Occurrences:** 2
- **Dynamic patching:** No
- **Coupling Score:** 1.2/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `Makefile` | 4 | `nose` | template_or_config_ref | config_or_template | `OBSERVED` |
| `Makefile` | 13 | `nose` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `pytest` (PyPI)
- **Validation Status:** `ACCEPTED` (Verified on PyPI (latest: 9.1.1))
- **Trade-offs:** Industry standard test runner; Full Python 3.12+ compatibility
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] Step 1: Remove nose and nosetests from the Makefile/configuration files.
2. [AI_GENERATED] Step 2: Add pytest to the project dependencies.
3. [AI_GENERATED] Step 3: Replace the 'test-nose' target in the Makefile with a 'test' target that uses pytest.
4. [AI_GENERATED] Step 4: Run 'pytest' to verify that all tests pass.
5. [AI_GENERATED] Step 5: Remove any nose-specific configuration files like 'nose.cfg' or '.noserc' if they exist.

### Migration Diff
> Applied cleanly: `False`

```diff
--- a/Makefile
+++ b/Makefile
@@ -1,13 +1,12 @@
 IMAGE ?= linkwatch
 PYTHON ?= python3.12
 
 .PHONY: setup test docker-build docker-test
 
 setup: 
 	$(PYTHON) -m venv .venv
 
 test: 
 	python -m pytest
 
 docker-build:
```

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[HIGH] GAP-0073:** Automated migration diff failed to apply cleanly: error: corrupt patch at line 16 (`OBSERVED`)
  *Suggested Resolution:* Review the unified diff manually and resolve conflicting hunk offsets.
- **[MEDIUM] GAP-0074:** Differential API test 'test_diff_compat_nose.py' failed against candidate 'pytest'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.