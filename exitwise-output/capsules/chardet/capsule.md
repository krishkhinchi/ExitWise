# Dependency Exit Capsule: `chardet`

> **Verdict:** `ANALYZED` | **Tool:** Exitwise v0.1.0 | **Generated:** 2026-10-15T11:05:03.513139+00:00
> **Gemma Model:** `gemma-4-26b-a4b-it` (Hosted Gemini API via official google-genai Python SDK)

## Trust Summary

- **Total Claims / Findings:** 20
- **Observed (deterministic / static / registry):** 9 (`OBSERVED`)
- **Verified by Sandbox Execution:** 2 (`VERIFIED_BY_EXECUTION`)
- **AI Proposed by Gemma (unverified):** 9 (`AI_GENERATED`)
- **AI Proposed & Confirmed by Test Run:** 0 (`AI_VERIFIED`)
- **Unverified / Skipped:** 0 (`NOT_VERIFIED`)

## 1. Dependency Details

- **Package:** `chardet`
- **Pinned Version:** `5.2.0`
- **Raw Specifier:** `chardet==5.2.0`
- **Source Manifests:** requirements.txt, pyproject.toml
- **Latest PyPI Version:** `7.6.0`

## 2. Risk Indicators

| ID | Severity | Indicator | Evidence | Provenance |
|---|---|---|---|---|
| `RISK-0050` | **HIGH** | Pinned at 5.2.0, 2 major versions behind latest (7.6.0) | EV-PYPI-0046 | `OBSERVED` |

## 3. Usage & Coupling

- **Files touched:** 2
- **Occurrences:** 3
- **Dynamic patching:** No
- **Coupling Score:** 2.5/10

### Usage Locations

| File | Line | Symbol | Kind | Context | Provenance |
|---|---|---|---|---|---|
| `linkwatch/encoding.py` | 4 | `chardet` | import | runtime | `OBSERVED` |
| `linkwatch/encoding.py` | 15 | `chardet.detect` | call | runtime | `OBSERVED` |
| `pyproject.toml` | 20 | `chardet` | template_or_config_ref | config_or_template | `OBSERVED` |

## 4. Proposed Replacement & Migration

- **Candidate:** `charset-normalizer` (PyPI)
- **Validation Status:** `ACCEPTED` (Verified on PyPI (latest: 3.5.2))
- **Trade-offs:** Modern, pure Python encoding detector; Faster and MIT licensed
- **Provenance:** `AI_GENERATED`

### Migration Steps

1. [AI_GENERATED] 1. Replace 'chardet' with 'charset-normalizer' in pyproject.toml / requirements.txt
2. [AI_GENERATED] 2. Update import statements in repository modules
3. [AI_GENERATED] 3. Run automated tests in sandbox environment

### Migration Diff
> Applied cleanly: `False`

```diff
--- a/linkwatch/encoding.py
+++ b/linkwatch/encoding.py
@@ -1,4 +1,4 @@
-import chardet
+import charset_normalizer as chardet
```

## 5. Executed Test Results

| Side | Python | Exit Code | Passed | Failed | Duration | Provenance |
|---|---|---|---|---|---|---|
| `baseline` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |
| `candidate` | 3.13 | 1 | 0 | 0 | 0.01s | `VERIFIED_BY_EXECUTION` |

## 6. Compatibility Gaps & Concerns

- **[HIGH] GAP-0095:** Automated migration diff failed to apply cleanly: error: corrupt patch at line 6 (`OBSERVED`)
  *Suggested Resolution:* Review the unified diff manually and resolve conflicting hunk offsets.
- **[MEDIUM] GAP-0096:** Differential API test 'test_diff_compat_chardet.py' failed against candidate 'charset-normalizer'. (`OBSERVED`)
  *Suggested Resolution:* Verify signature differences or parameter changes in the replacement API.