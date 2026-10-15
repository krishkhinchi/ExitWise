"""Vercel serverless entry point for the Exitwise dashboard."""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Exitwise Dashboard")

# Resolve capsule directory relative to this file so it works on Vercel's filesystem
CAPSULE_DIR = Path(__file__).resolve().parent.parent / "exitwise-output"


@app.get("/api/capsules")
async def list_capsules():
    capsules = []
    caps_folder = CAPSULE_DIR / "capsules"
    if caps_folder.is_dir():
        for sub in sorted(caps_folder.iterdir()):
            cap_json = sub / "capsule.json"
            if cap_json.is_file():
                try:
                    data = json.loads(cap_json.read_text(encoding="utf-8"))
                    capsules.append({
                        "name": data.get("dependency", {}).get("name", sub.name),
                        "pinned": data.get("dependency", {}).get("pinned_version"),
                        "latest": data.get("dependency", {}).get("latest_version"),
                        "verdict": data.get("overall_verdict", "NOT EXECUTED"),
                        "candidate": data.get("proposed_replacement", {}).get("name") if data.get("proposed_replacement") else "None",
                        "trust": data.get("provenance_summary", {}),
                    })
                except Exception:
                    continue
    return capsules


@app.get("/api/capsules/{name}")
async def get_capsule(name: str):
    cap_json = CAPSULE_DIR / "capsules" / name / "capsule.json"
    if not cap_json.exists():
        raise HTTPException(status_code=404, detail="Capsule not found")
    return json.loads(cap_json.read_text(encoding="utf-8"))


@app.get("/capsule/{name}", response_class=HTMLResponse)
async def view_capsule(name: str):
    html_file = CAPSULE_DIR / "capsules" / name / "capsule.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Capsule not found")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/capsules/{name}/capsule.html", response_class=HTMLResponse)
async def view_capsule_static(name: str):
    html_file = CAPSULE_DIR / "capsules" / name / "capsule.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Capsule not found")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    idx_file = CAPSULE_DIR / "index.html"
    if idx_file.exists():
        return HTMLResponse(content=idx_file.read_text(encoding="utf-8"))
    return HTMLResponse("<html><body><h1>Exitwise</h1><p>No capsules found.</p></body></html>")
