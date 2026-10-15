"""Tests for dashboard mock progress engine and wiring."""

import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from exitwise.web.server import app

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "exitwise-output" / "mock-progress-engine.js"
INDEX = ROOT / "exitwise-output" / "index.html"
NODE_TEST = Path(__file__).resolve().parent / "mock_progress_engine.test.mjs"

client = TestClient(app)


def test_mock_progress_engine_js_served():
    response = client.get("/mock-progress-engine.js")
    assert response.status_code == 200
    assert "MockProgressEngine" in response.text
    assert "computeMockProgressState" in response.text


def test_index_includes_demo_mode_and_engine_script():
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="demo-mode-toggle"' in html
    assert "DEMO MODE" in html
    assert "/mock-progress-engine.js" in html
    assert "schedulePolling" in html
    assert "applyMockProgressState" in html
    assert "stopAnalysisSession" in html


def test_node_mock_progress_engine_suite():
    if not ENGINE.is_file():
        raise AssertionError(f"Missing engine script: {ENGINE}")
    result = subprocess.run(
        ["node", "--test", str(NODE_TEST)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
    assert result.returncode == 0, "node mock progress tests failed"
