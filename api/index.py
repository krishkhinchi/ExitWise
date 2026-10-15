"""Vercel serverless entry point for the Exitwise dashboard.

Provides full REST API and static viewing capabilities for Dependency Exit Capsules.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="Exitwise Dashboard", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve capsule directory relative to this file so it works on Vercel's filesystem
CAPSULE_DIR = Path(__file__).resolve().parent.parent / "exitwise-output"


def _read_all_disk_capsules() -> list[dict]:
    """Load all capsule JSON files stored on disk."""
    capsules = []
    caps_folder = CAPSULE_DIR / "capsules"
    if caps_folder.is_dir():
        for sub in sorted(caps_folder.iterdir()):
            cap_json = sub / "capsule.json"
            if cap_json.is_file():
                try:
                    data = json.loads(cap_json.read_text(encoding="utf-8"))
                    capsules.append(data)
                except Exception:
                    continue
    return capsules


def _extract_dep_summary(data: dict) -> dict:
    """Extract table summary fields from raw capsule dict."""
    dep = data.get("dependency", {})
    ts = data.get("provenance_summary", {})
    usage = data.get("usage_summary", {})
    rep = data.get("proposed_replacement")
    coupling = float(usage.get("coupling_score", 0.0))

    return {
        "name": dep.get("name", "Unknown"),
        "pinned_version": dep.get("pinned_version"),
        "raw_spec": dep.get("raw_spec", ""),
        "constraint_spec": dep.get("constraint"),
        "latest_version": dep.get("latest_version"),
        "coupling_score": coupling,
        "risk_score": coupling,
        "risk_level": "HIGH" if coupling > 5 else "LOW",
        "candidate_name": rep.get("name") if rep else "None (Monitor)",
        "candidate_kind": rep.get("kind") if rep else "none",
        "verdict": data.get("overall_verdict", "NOT EXECUTED"),
        "trust_obs": ts.get("observed_count", 0),
        "trust_ver": ts.get("verified_by_execution_count", 0),
        "trust_ai": ts.get("ai_generated_count", 0),
        "has_capsule": True,
        "capsule_path": f"capsules/{dep.get('name')}/capsule.html",
    }


class AnalyzeRequest(BaseModel):
    url: str


@app.post("/api/repositories/analyze")
async def analyze_repository(req: AnalyzeRequest):
    """Trigger or simulate repository analysis for serverless runtime."""
    url = req.url.strip()
    return {
        "analysis_id": "current",
        "status": "COMPLETED",
        "repo_url": url,
        "repo_name": url.split("/")[-1] if "/" in url else url,
        "message": f"Pre-computed resilience capsules loaded for {url}",
    }


@app.get("/api/analyses")
async def list_analyses():
    """List available repository analyses."""
    return [
        {
            "id": "current",
            "repo_url": "https://github.com/rishrek/LinkWatch",
            "repo_name": "rishrek/LinkWatch",
            "status": "COMPLETED",
            "current_stage": "Exit Capsules verified and stored",
            "stage_index": 8,
            "total_stages": 8,
            "progress": 100,
            "discovered_count": 5,
            "analyzed_count": 5,
            "capsule_count": 5,
            "ecosystem": "Python",
            "message": "Resilience capsules verified and ready",
        }
    ]


@app.get("/api/analyses/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Retrieve status, current stage, and metrics for an analysis."""
    return {
        "id": analysis_id,
        "repo_url": "https://github.com/rishrek/LinkWatch",
        "repo_name": "rishrek/LinkWatch",
        "status": "COMPLETED",
        "current_stage": "Exit Capsules verified and stored",
        "stage_index": 8,
        "total_stages": 8,
        "progress": 100,
        "discovered_count": 5,
        "analyzed_count": 5,
        "capsule_count": 5,
        "ecosystem": "Python",
        "message": "Resilience capsules verified and ready",
    }


@app.get("/api/analyses/{analysis_id}/dependencies")
async def get_analysis_dependencies(analysis_id: str):
    """Retrieve discovered dependencies with resilience metrics."""
    raw_capsules = _read_all_disk_capsules()
    return [_extract_dep_summary(c) for c in raw_capsules]


@app.get("/api/analyses/{analysis_id}/capsules/{dependency_id}")
async def get_dependency_capsule(analysis_id: str, dependency_id: str):
    """Retrieve full capsule data for a dependency."""
    cap_file = CAPSULE_DIR / "capsules" / dependency_id / "capsule.json"
    if not cap_file.is_file():
        raise HTTPException(status_code=404, detail=f"Capsule for '{dependency_id}' not found")
    try:
        data = json.loads(cap_file.read_text(encoding="utf-8"))
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read capsule: {e!s}")


@app.get("/api/analyses/{analysis_id}/export")
async def export_analysis(
    analysis_id: str,
    format: str = Query("json", description="Export format: json or markdown"),
    dependency: str | None = Query(None, description="Optional dependency name for single capsule export"),
):
    """Export analysis report or single capsule as JSON or Markdown."""
    if dependency:
        cap_file = CAPSULE_DIR / "capsules" / dependency / "capsule.json"
        if not cap_file.is_file():
            raise HTTPException(status_code=404, detail=f"Capsule for '{dependency}' not found")

        if format == "markdown":
            md_file = CAPSULE_DIR / "capsules" / dependency / "capsule.md"
            content = md_file.read_text(encoding="utf-8") if md_file.is_file() else f"# Capsule: {dependency}"
            return PlainTextResponse(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=exitwise-capsule-{dependency}.md"},
            )
        else:
            data = json.loads(cap_file.read_text(encoding="utf-8"))
            return JSONResponse(
                content=data,
                headers={"Content-Disposition": f"attachment; filename=exitwise-capsule-{dependency}.json"},
            )

    raw_capsules = _read_all_disk_capsules()
    deps = [_extract_dep_summary(c) for c in raw_capsules]

    if format == "markdown":
        lines = [
            "# Exitwise Resilience Report: LinkWatch",
            "- **Target:** `https://github.com/rishrek/LinkWatch`",
            "- **Total Discovered Dependencies:** 5",
            "- **Engine:** Gemma 4 (26B-A4B-IT)",
            "",
            "## Evaluated Dependencies",
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
            headers={"Content-Disposition": "attachment; filename=exitwise-resilience-report.md"},
        )
    else:
        return JSONResponse(
            content={
                "repository": "rishrek/LinkWatch",
                "exported_at": datetime.now(UTC).isoformat(),
                "dependencies": deps,
                "capsules": raw_capsules,
            },
            headers={"Content-Disposition": "attachment; filename=exitwise-analysis.json"},
        )


@app.get("/api/capsules")
async def list_capsules():
    """Legacy capsule listing endpoint."""
    raw_capsules = _read_all_disk_capsules()
    return [_extract_dep_summary(c) for c in raw_capsules]


@app.get("/api/capsules/{name}")
async def get_capsule(name: str):
    """Legacy capsule detail endpoint."""
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
