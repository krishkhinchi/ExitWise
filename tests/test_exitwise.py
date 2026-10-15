"""Unit tests for manifest parsing, drift detection, and AST scanner."""

import ast
import tempfile
from pathlib import Path
import pytest
from exitwise.ingest.manifests import (
    parse_requirement_line,
    parse_requirements_txt,
    parse_pyproject_toml,
    parse_setup_py_ast,
    scan_all_manifests,
)
from exitwise.usage.ast_scanner import scan_repo_usage_for_dependency
from exitwise.usage.coupling import compute_usage_coupling
from exitwise.signals.scoring import assess_dependency_risk
from exitwise.signals.py_compat import evaluate_python_compatibility, KNOWN_BROKEN_ON_312_PLUS
from exitwise.models import Provenance


# ─────────────────────────────────────────────
# Manifest Parsing Tests
# ─────────────────────────────────────────────

def test_parse_pinned_requirement():
    r = parse_requirement_line("requests==2.31.0", "requirements.txt", 1)
    assert r is not None
    assert r.name == "requests"
    assert r.is_pinned is True
    assert r.pinned_version == "2.31.0"


def test_parse_unpinned_requirement():
    r = parse_requirement_line("click>=7", "requirements.txt", 1)
    assert r is not None
    assert r.name == "click"
    assert r.is_pinned is False


def test_parse_comment_line_returns_none():
    r = parse_requirement_line("# This is a comment", "requirements.txt", 1)
    assert r is None


def test_parse_empty_line_returns_none():
    r = parse_requirement_line("   ", "requirements.txt", 1)
    assert r is None


def test_parse_flag_line_returns_none():
    r = parse_requirement_line("-r other.txt", "requirements.txt", 1)
    assert r is None


def test_requirements_txt_multi_line():
    with tempfile.TemporaryDirectory() as tmp:
        req_file = Path(tmp) / "requirements.txt"
        req_file.write_text("requests==2.31.0\n# comment\nappdirs==1.4.4\n\n")
        reqs = parse_requirements_txt(req_file, "requirements.txt")
        assert len(reqs) == 2
        assert reqs[0].name == "requests"
        assert reqs[1].name == "appdirs"


def test_pyproject_toml_pep621():
    with tempfile.TemporaryDirectory() as tmp:
        pf = Path(tmp) / "pyproject.toml"
        pf.write_text(
            '[project]\ndependencies = ["requests>=2.0", "pydantic>=2"]\n'
        )
        reqs = parse_pyproject_toml(pf, "pyproject.toml")
        names = [r.name for r in reqs]
        assert "requests" in names
        assert "pydantic" in names


def test_setup_py_ast_extraction():
    with tempfile.TemporaryDirectory() as tmp:
        sp = Path(tmp) / "setup.py"
        sp.write_text(
            "from setuptools import setup\n"
            "setup(name='myapp', install_requires=['requests>=2.0', 'click'])\n"
        )
        reqs = parse_setup_py_ast(sp, "setup.py")
        names = [r.name for r in reqs]
        assert "requests" in names
        assert "click" in names


def test_manifest_drift_detection():
    """Pydantic specified as >=2 in pyproject.toml but ==1.10.13 in requirements.txt — must flag drift."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "requirements.txt").write_text("pydantic==1.10.13\n")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["pydantic>=2"]\n'
        )
        all_reqs, drifts, _ = scan_all_manifests(tmp_path)
        assert len(drifts) >= 1
        drift_names = [d.package for d in drifts]
        assert "pydantic" in drift_names


# ─────────────────────────────────────────────
# AST Scanner Tests
# ─────────────────────────────────────────────

def _write_py_file(tmp_dir: Path, filename: str, content: str) -> Path:
    f = tmp_dir / filename
    f.write_text(content, encoding="utf-8")
    return f


def test_ast_scan_import():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(tmp_path, "app.py", "import requests\nrequests.get('http://example.com')\n")
        locs, ev = scan_repo_usage_for_dependency(tmp_path, "requests")
        kinds = {l.kind for l in locs}
        assert "import" in kinds


def test_ast_scan_import_from():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(tmp_path, "app.py", "from requests import Session\ns = Session()\n")
        locs, ev = scan_repo_usage_for_dependency(tmp_path, "requests")
        kinds = {l.kind for l in locs}
        assert "import_from" in kinds


def test_ast_scan_monkey_patch_detection():
    """Dynamic assignment `requests.Session.request = _request` must be detected as 'patch'."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(
            tmp_path,
            "http_patch.py",
            "import requests\n"
            "_original = requests.Session.request\n"
            "def _request(self, method, url, **kwargs): pass\n"
            "requests.Session.request = _request\n",
        )
        locs, ev = scan_repo_usage_for_dependency(tmp_path, "requests")
        patch_locs = [l for l in locs if l.kind == "patch"]
        assert len(patch_locs) >= 1
        assert any("requests.Session.request" in l.symbol for l in patch_locs)


def test_ast_scan_inheritance():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(
            tmp_path,
            "models.py",
            "from pydantic import BaseModel\nclass User(BaseModel):\n    name: str\n",
        )
        locs, ev = scan_repo_usage_for_dependency(tmp_path, "pydantic")
        kinds = {l.kind for l in locs}
        assert "inheritance" in kinds


# ─────────────────────────────────────────────
# Coupling Score Tests
# ─────────────────────────────────────────────

def test_coupling_score_monkey_patch_premium():
    from exitwise.models import UsageLocation, Provenance
    locs = [
        UsageLocation(file="a.py", line=1, symbol="requests", kind="import", snippet="", context="runtime"),
        UsageLocation(file="a.py", line=5, symbol="requests.Session.request", kind="patch", snippet="", context="patching"),
    ]
    summary = compute_usage_coupling(locs)
    assert summary.is_monkey_patched is True
    # Patching adds 3.5 to coupling score
    assert summary.coupling_score >= 3.5


def test_coupling_score_test_only_halved():
    from exitwise.models import UsageLocation
    locs = [
        UsageLocation(file="tests/test_foo.py", line=1, symbol="pytest", kind="import", snippet="", context="test"),
    ]
    summary = compute_usage_coupling(locs)
    assert summary.is_test_only is True
    assert summary.coupling_score <= 5.0


# ─────────────────────────────────────────────
# Python Compatibility Tests
# ─────────────────────────────────────────────

def test_nose_known_broken_on_312():
    result, ev = evaluate_python_compatibility("nose", None, [], 1)
    assert result.compatible_312 is False
    assert result.compatible_313 is False
    assert "nose" in (result.incompat_reason or "").lower() or "imp" in (result.incompat_reason or "").lower()


def test_package_with_permissive_requires_python_is_compatible():
    result, ev = evaluate_python_compatibility("requests", ">=2.28", [], 1)
    assert result.compatible_312 is True
    assert result.compatible_313 is True


# ─────────────────────────────────────────────
# Provenance Enforcement Tests
# ─────────────────────────────────────────────

def test_capsule_provenance_required_fields():
    """Every leaf in risk indicators must carry a provenance tag."""
    from exitwise.models import RiskIndicator, Provenance
    ri = RiskIndicator(
        id="RISK-0001",
        dependency="requests",
        severity="HIGH",
        source="test",
        observed_value="test value",
    )
    # Provenance must have a default value, never None
    assert ri.provenance is not None
    assert ri.provenance == Provenance.OBSERVED


def test_capsule_schema_validates_provenance():
    """A DependencyCapsule with missing gemma_model_id in meta must fail validation."""
    from exitwise.capsule.schema import validate_capsule_dict
    bad_capsule = {"meta": {"gemma_model_id": ""}, "dependency": {}, "risk_indicators": []}
    ok, err = validate_capsule_dict(bad_capsule)
    # Pydantic validation will fail on missing required fields
    assert ok is False


# ─────────────────────────────────────────────
# Grounding Validator Tests
# ─────────────────────────────────────────────

def test_grounding_validator_catches_unknown_evidence_ids():
    from exitwise.ai.grounding import validate_grounded_evidence
    valid_ids = {"EV-PYPI-0001", "EV-OSV-0002"}
    cited = ["EV-PYPI-0001", "EV-HALLUCINATED-9999"]
    accepted, rejected = validate_grounded_evidence(cited, valid_ids)
    assert "EV-PYPI-0001" in accepted
    assert "EV-HALLUCINATED-9999" in rejected


def test_hallucinated_package_rejected_by_validator():
    """A completely made-up package name must be rejected by deterministic PyPI validation."""
    from exitwise.ai.grounding import validate_replacement_candidate
    cand = validate_replacement_candidate("totally-fake-pkg-xyzabc123", "EV-FAKE-0001", offline_mode=False)
    assert cand.status == "REJECTED"
    assert cand.validation.exists_on_pypi_or_stdlib is False


def test_stdlib_module_always_accepted():
    from exitwise.ai.grounding import validate_replacement_candidate
    cand = validate_replacement_candidate("tomllib", "EV-PYPI-0001", offline_mode=False)
    assert cand.status == "ACCEPTED"
    assert cand.validation.is_stdlib is True


# ─────────────────────────────────────────────
# Integration Test (mocked Gemma)
# ─────────────────────────────────────────────

def test_scan_fixture_repo_finds_drift(tmp_path):
    """Fixture: repo with pydantic==1.10.13 in requirements.txt and >=2 in pyproject.toml detects drift."""
    (tmp_path / "requirements.txt").write_text("pydantic==1.10.13\n")
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["pydantic>=2"]\n')
    reqs, drifts, evs = scan_all_manifests(tmp_path)
    assert any(d.package == "pydantic" and d.is_conflict for d in drifts)
    assert any(e.kind == "manifest_drift" for e in evs)


@pytest.mark.live
def test_live_scan_linkwatch():
    """Live test: run on real LinkWatch repo. Requires GEMINI_API_KEY in environment."""
    import os
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("No API key in environment — skipping live test")

    from exitwise.ingest.repo import prepare_workspace
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        repo = prepare_workspace("https://github.com/rishrek/LinkWatch", Path(tmp))
        reqs, drifts, _ = scan_all_manifests(Path(tmp))
        assert len(reqs) > 0
        assert any(d.package == "pydantic" for d in drifts), "Expected pydantic drift not found"
