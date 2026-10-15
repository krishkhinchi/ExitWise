"""FastAPI web server for Exitwise dynamic repository resilience dashboard."""

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from exitwise.web.db import AnalysisDB
from exitwise.web.engine import (
    run_repository_analysis,
    validate_github_url,
)

app = FastAPI(title="Exitwise Resilience Dashboard", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CAPSULE_DIR = Path("exitwise-output")
db: AnalysisDB | None = None


def get_db() -> AnalysisDB:
    global db
    if db is None:
        db_path = CAPSULE_DIR / "exitwise.db"
        db = AnalysisDB(db_path)
        db.seed_from_disk(CAPSULE_DIR)
    return db


class AnalyzeRequest(BaseModel):
    url: str


@app.post("/api/repositories/analyze")
async def analyze_repository(req: AnalyzeRequest):
    """Start dynamic analysis workflow for a given GitHub repository."""
    is_valid, norm_url_or_err, owner, repo = validate_github_url(req.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=norm_url_or_err)

    norm_url = norm_url_or_err
    analysis_id = f"anl_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    database = get_db()
    database.create_analysis(
        analysis_id=analysis_id,
        repo_url=norm_url,
        repo_name=f"{owner}/{repo}",
    )

    # Launch pipeline in background thread
    worker = threading.Thread(
        target=run_repository_analysis,
        args=(analysis_id, norm_url, database, CAPSULE_DIR),
        daemon=True,
        name=f"worker-{analysis_id}",
    )
    worker.start()

    return {
        "analysis_id": analysis_id,
        "status": "QUEUED",
        "repo_url": norm_url,
        "repo_name": f"{owner}/{repo}",
        "message": f"Analysis queued for {norm_url}",
    }


def resolve_analysis_id(database: AnalysisDB, analysis_id: str) -> str:
    """Resolve 'current' to the latest active or completed analysis that has dependencies."""
    if analysis_id != "current":
        return analysis_id
    analyses = database.list_analyses(limit=10)
    if not analyses:
        raise HTTPException(status_code=404, detail="No analyses found")
    for a in analyses:
        if a.get("status") in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "RUNNING"):
            deps = database.get_dependencies_for_analysis(a["id"])
            if deps:
                return a["id"]
    return analyses[0]["id"]


@app.get("/api/analyses")
async def list_all_analyses(limit: int = 10):
    """List recent repository analyses."""
    database = get_db()
    return database.list_analyses(limit=limit)


@app.get("/api/analyses/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Retrieve status, current stage, and metrics for an analysis."""
    database = get_db()
    actual_id = resolve_analysis_id(database, analysis_id)
    res = database.get_analysis(actual_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return res


@app.get("/api/analyses/{analysis_id}/dependencies")
async def get_analysis_dependencies(analysis_id: str):
    """Retrieve discovered dependencies for an analysis."""
    database = get_db()
    try:
        actual_id = resolve_analysis_id(database, analysis_id)
    except HTTPException:
        return []
    return database.get_dependencies_for_analysis(actual_id)


@app.get("/api/analyses/{analysis_id}/capsules/{dependency_id}")
async def get_dependency_capsule(analysis_id: str, dependency_id: str):
    """Retrieve detailed capsule for one dependency."""
    database = get_db()
    actual_id = resolve_analysis_id(database, analysis_id)

    cap = database.get_capsule(actual_id, dependency_id)
    if not cap:
        # Check disk directly as fallback
        cap_file = CAPSULE_DIR / "capsules" / dependency_id / "capsule.json"
        if cap_file.is_file():
            try:
                data = json.loads(cap_file.read_text(encoding="utf-8"))
                return {"data": data}
            except Exception:
                pass
        raise HTTPException(status_code=404, detail=f"Capsule for '{dependency_id}' not found")
    return cap


@app.get("/api/analyses/{analysis_id}/export")
async def export_analysis(
    analysis_id: str,
    format: str = Query("json", description="Export format: json or markdown"),
    dependency: str | None = Query(None, description="Optional dependency name for single capsule export"),
):
    """Export analysis results or single capsule as JSON or Markdown."""
    database = get_db()
    actual_id = resolve_analysis_id(database, analysis_id)

    if dependency:
        cap = database.get_capsule(actual_id, dependency)
        if not cap:
            raise HTTPException(status_code=404, detail=f"Capsule for '{dependency}' not found")

        if format == "markdown":
            md = cap.get("markdown_content") or ""
            return PlainTextResponse(
                content=md,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=exitwise-capsule-{dependency}.md"},
            )
        else:
            return JSONResponse(
                content=cap.get("data", {}),
                headers={"Content-Disposition": f"attachment; filename=exitwise-capsule-{dependency}.json"},
            )

    # Whole analysis export
    analysis = database.get_analysis(actual_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    deps = database.get_dependencies_for_analysis(actual_id)
    export_payload = {
        "analysis": analysis,
        "dependencies": deps,
        "exported_at": datetime.now(UTC).isoformat(),
    }

    if format == "markdown":
        lines = [
            f"# Exitwise Resilience Report: {analysis['repo_name']}",
            f"- **Repository URL:** {analysis['repo_url']}",
            f"- **Commit SHA:** `{analysis['commit_sha']}`",
            f"- **Status:** `{analysis['status']}`",
            f"- **Total Discovered Dependencies:** {len(deps)}",
            "",
            "## Dependencies Table",
            "",
            "| Dependency | Pinned | Latest | Coupling | Candidate | Verdict | Trust Distribution |",
            "|---|---|---|---|---|---|---|",
        ]
        for d in deps:
            lines.append(
                f"| `{d['name']}` | {d.get('pinned_version') or 'unpinned'} | {d.get('latest_version') or 'Unknown'} | {d.get('coupling_score', 0):.1f}/10 | `{d.get('candidate_name') or 'None'}` | {d.get('verdict')} | {d.get('trust_obs', 0)} obs · {d.get('trust_ver', 0)} ver · {d.get('trust_ai', 0)} ai |"
            )
        return PlainTextResponse(
            content="\n".join(lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=exitwise-report-{analysis_id}.md"},
        )
    else:
        return JSONResponse(
            content=export_payload,
            headers={"Content-Disposition": f"attachment; filename=exitwise-analysis-{analysis_id}.json"},
        )


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
    """Serve the interactive Exitwise Resilience Dashboard."""
    # Check if index.html exists in CAPSULE_DIR
    idx_file = CAPSULE_DIR / "index.html"
    if idx_file.is_file():
        return HTMLResponse(content=idx_file.read_text(encoding="utf-8"))

    # Return fallback shell
    return HTMLResponse(
        "<html><body style='background:#09090b;color:#fafafa;padding:40px;font-family:sans-serif;'>"
        "<h1>Exitwise Dashboard</h1>"
        "<p>Initializing dashboard...</p>"
        "</body></html>"
    )


def start_dashboard(port: int = 8000, capsule_dir: Path | None = None):
    """Launch the FastAPI dashboard server via uvicorn."""
    global CAPSULE_DIR
    if capsule_dir:
        CAPSULE_DIR = capsule_dir

    # Initialize DB
    get_db()

    caps_static = CAPSULE_DIR / "capsules"
    if caps_static.is_dir():
        app.mount("/capsules", StaticFiles(directory=str(caps_static)), name="capsules")

    print(f"Starting Exitwise Dashboard at http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
