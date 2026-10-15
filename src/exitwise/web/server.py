"""FastAPI local web dashboard with Server-Sent Events for live progress."""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Exitwise Local Dashboard", version="0.1.0")

CAPSULE_DIR = Path("exitwise-output")


@app.get("/api/capsules")
async def list_capsules():
    """List all available Dependency Exit Capsules."""
    capsules = []
    caps_folder = CAPSULE_DIR / "capsules"
    if caps_folder.is_dir():
        for sub in caps_folder.iterdir():
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
async def get_capsule_detail(name: str):
    """Retrieve full JSON for a specific dependency capsule."""
    cap_json = CAPSULE_DIR / "capsules" / name / "capsule.json"
    if not cap_json.exists():
        raise HTTPException(status_code=404, detail="Capsule not found")
    return json.loads(cap_json.read_text(encoding="utf-8"))


@app.get("/capsule/{name}", response_class=HTMLResponse)
async def view_capsule_html(name: str):
    """Serve self-contained HTML for a capsule."""
    html_file = CAPSULE_DIR / "capsules" / name / "capsule.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Capsule HTML not found")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the root index.html."""
    idx_file = CAPSULE_DIR / "index.html"
    if idx_file.exists():
        return HTMLResponse(content=idx_file.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<html><body style='background:#09090b;color:#fafafa;padding:40px;font-family:sans-serif;'>"
        "<h1>Exitwise Dashboard</h1>"
        "<p>No capsules found. Run <code>exitwise run &lt;repo&gt;</code> first to generate capsules.</p>"
        "</body></html>"
    )


def start_dashboard(port: int = 8000, capsule_dir: Path | None = None):
    """Launch the FastAPI dashboard server via uvicorn."""
    global CAPSULE_DIR
    if capsule_dir:
        CAPSULE_DIR = capsule_dir

    caps_static = CAPSULE_DIR / "capsules"
    if caps_static.is_dir():
        app.mount("/capsules", StaticFiles(directory=str(caps_static)), name="capsules")

    print(f"Starting Exitwise Dashboard at http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
