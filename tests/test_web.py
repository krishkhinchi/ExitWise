"""Unit tests for Exitwise FastAPI server and Vercel endpoints."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure api directory is in sys.path
api_dir = str(Path(__file__).resolve().parent.parent / "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

import index as vercel_module

from exitwise.web.server import app as server_app

client_server = TestClient(server_app)
client_vercel = TestClient(vercel_module.app)


def test_server_index():
    response = client_server.get("/")
    assert response.status_code == 200
    assert "Exitwise" in response.text


def test_server_list_analyses():
    response = client_server.get("/api/analyses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_server_dependencies():
    response = client_server.get("/api/analyses/current/dependencies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]
        assert "coupling_score" in data[0]


def test_server_capsule_detail():
    response = client_server.get("/api/analyses/current/capsules/requests")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or "dependency" in data


def test_server_export_json_and_markdown():
    res_json = client_server.get("/api/analyses/current/export?format=json")
    assert res_json.status_code == 200

    res_md = client_server.get("/api/analyses/current/export?format=markdown")
    assert res_md.status_code == 200
    assert "# Exitwise" in res_md.text


def test_server_analyze_validation():
    # Invalid URL
    res_invalid = client_server.post("/api/repositories/analyze", json={"url": "http://localhost:8000"})
    assert res_invalid.status_code == 400

    # Valid GitHub URL
    res_valid = client_server.post("/api/repositories/analyze", json={"url": "https://github.com/testorg/testrepo"})
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "QUEUED"


def test_vercel_index():
    response = client_vercel.get("/")
    assert response.status_code == 200
    assert "Exitwise" in response.text


def test_vercel_dependencies():
    response = client_vercel.get("/api/analyses/current/dependencies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    names = [d["name"] for d in data]
    assert "requests" in names
    assert "idna" in names


def test_vercel_capsule_detail():
    response = client_vercel.get("/api/analyses/current/capsules/requests")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["dependency"]["name"] == "requests"


def test_vercel_export():
    res_json = client_vercel.get("/api/analyses/current/export?format=json")
    assert res_json.status_code == 200

    res_md = client_vercel.get("/api/analyses/current/export?format=markdown")
    assert res_md.status_code == 200
    assert "# Exitwise" in res_md.text
