# Dependency Exit Capsule: `appdirs`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:04:59.279369+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 20
- **Observed (deterministic / static / registry):** 9 (`OBSERVED`)
- **Verified by Sandbox Execution:** 2 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 9 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `appdirs`
- **Pinned Version:** `1.4.4`
- **Raw Specifier:** `appdirs==1.4.4`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `1.4.4`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0020` | **HIGH** | No new PyPI release in 2348 days (~6.4 years, last: 2020-05-11) | EV-PYPI-0016 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 3
- **Dynamic patching:** No
- **Coupling Score:** 2.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/cache.py` | 4 | `appdirs.user_cache_dir` | import_from | runtime | `OBSERVED` |
| `linkwatch/cache.py` | 10 | `appdirs.user_cache_dir` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 14 | `appdirs` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `platformdirs` (PyPI)
- **Validation Status:** `ACCEPTED` (Verified on PyPI (latest: 4.13.0))
- **Trade-offs:** Actively maintained community fork of appdirs; Direct API compatibility
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] 1. Replace 'appdirs' with 'platformdirs' in pyproject.toml / requirements.txt
2. [AI_GENERATED] 2. Update import statements in repository modules
3. [AI_GENERATED] 3. Run automated tests in sandbox environment

### Migration Diff
> Applied cleanly: `False`

```diff
--- a/linkwatch/cache.py
+++ b/linkwatch/cache.py
@@ -1,4 +1,4 @@
-import appdirs
+import platformdirs as appdirs
```

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[HIGH] GAP-0090:** Automated migration diff failed to apply cleanly: error: corrupt patch at line 6 (`OBSERVED`)
  *Suggested Resolution:* Review the unified diff manually and resolve conflicting hunk offsets.
- **[MEDIUM] GAP-0091:** Differential API test 'test_diff_compat_appdirs.py' failed against candidate 'platformdirs'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.