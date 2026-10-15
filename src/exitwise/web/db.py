"""SQLite persistence layer for Exitwise dynamic repository analyses and capsules."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AnalysisDB:
    """Thread-safe SQLite storage for analysis jobs, dependencies, and exit capsules."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                commit_sha TEXT DEFAULT '',
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                stage_index INTEGER NOT NULL DEFAULT 1,
                total_stages INTEGER NOT NULL DEFAULT 8,
                progress INTEGER NOT NULL DEFAULT 0,
                discovered_count INTEGER NOT NULL DEFAULT 0,
                analyzed_count INTEGER NOT NULL DEFAULT 0,
                capsule_count INTEGER NOT NULL DEFAULT 0,
                ecosystem TEXT DEFAULT 'Python',
                manifest_files TEXT DEFAULT '[]',
                error TEXT,
                message TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS dependencies (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                name TEXT NOT NULL,
                pinned_version TEXT,
                raw_spec TEXT,
                constraint_spec TEXT,
                latest_version TEXT,
                coupling_score REAL DEFAULT 0.0,
                risk_score REAL DEFAULT 0.0,
                risk_level TEXT DEFAULT 'LOW',
                candidate_name TEXT,
                candidate_kind TEXT,
                verdict TEXT NOT NULL DEFAULT 'NOT EXECUTED',
                trust_obs INTEGER DEFAULT 0,
                trust_ver INTEGER DEFAULT 0,
                trust_ai INTEGER DEFAULT 0,
                has_capsule INTEGER DEFAULT 0,
                capsule_path TEXT,
                data_json TEXT,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id)
            );

            CREATE TABLE IF NOT EXISTS capsules (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                dependency_name TEXT NOT NULL,
                capsule_json TEXT NOT NULL,
                html_content TEXT,
                markdown_content TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id)
            );
            """)

    def create_analysis(
        self,
        analysis_id: str,
        repo_url: str,
        repo_name: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO analyses (
                    id, repo_url, repo_name, status, current_stage, stage_index,
                    total_stages, progress, message, started_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    repo_url,
                    repo_name,
                    "QUEUED",
                    "Validating repository",
                    1,
                    8,
                    5,
                    f"Analysis initialized for {repo_name}",
                    now,
                ),
            )
        return self.get_analysis(analysis_id) or {}

    def update_analysis_stage(
        self,
        analysis_id: str,
        stage_index: int,
        stage_name: str,
        message: str,
        progress: int,
        status: str = "RUNNING",
        commit_sha: str | None = None,
        discovered_count: int | None = None,
        ecosystem: str | None = None,
        manifest_files: list[str] | None = None,
    ):
        with self._get_conn() as conn:
            fields = ["stage_index = ?", "current_stage = ?", "message = ?", "progress = ?", "status = ?"]
            params: list[Any] = [stage_index, stage_name, message, progress, status]

            if commit_sha is not None:
                fields.append("commit_sha = ?")
                params.append(commit_sha)
            if discovered_count is not None:
                fields.append("discovered_count = ?")
                params.append(discovered_count)
            if ecosystem is not None:
                fields.append("ecosystem = ?")
                params.append(ecosystem)
            if manifest_files is not None:
                fields.append("manifest_files = ?")
                params.append(json.dumps(manifest_files))

            params.append(analysis_id)
            query = f"UPDATE analyses SET {', '.join(fields)} WHERE id = ?"
            conn.execute(query, params)

    def complete_analysis(
        self,
        analysis_id: str,
        message: str = "Analysis completed successfully",
        status: str = "COMPLETED",
        analyzed_count: int | None = None,
        capsule_count: int | None = None,
    ):
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            fields = ["status = ?", "progress = 100", "message = ?", "completed_at = ?"]
            params: list[Any] = [status, message, now]
            if analyzed_count is not None:
                fields.append("analyzed_count = ?")
                params.append(analyzed_count)
            if capsule_count is not None:
                fields.append("capsule_count = ?")
                params.append(capsule_count)
            params.append(analysis_id)
            conn.execute(f"UPDATE analyses SET {', '.join(fields)} WHERE id = ?", params)

    def fail_analysis(self, analysis_id: str, error_message: str):
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE analyses
                SET status = 'FAILED', error = ?, message = ?, completed_at = ?
                WHERE id = ?
                """,
                (error_message, f"Failed: {error_message}", now, analysis_id),
            )

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            if res.get("manifest_files"):
                try:
                    res["manifest_files"] = json.loads(res["manifest_files"])
                except Exception:
                    res["manifest_files"] = []
            return res

    def list_analyses(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM analyses ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("manifest_files"):
                    try:
                        item["manifest_files"] = json.loads(item["manifest_files"])
                    except Exception:
                        item["manifest_files"] = []
                results.append(item)
            return results

    def save_dependency(
        self,
        analysis_id: str,
        name: str,
        pinned_version: str | None,
        raw_spec: str,
        constraint_spec: str | None,
        latest_version: str | None,
        coupling_score: float,
        risk_score: float,
        risk_level: str,
        candidate_name: str | None,
        candidate_kind: str | None,
        verdict: str,
        trust_obs: int,
        trust_ver: int,
        trust_ai: int,
        has_capsule: bool,
        capsule_path: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ):
        dep_id = f"{analysis_id}_{name}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dependencies (
                    id, analysis_id, name, pinned_version, raw_spec, constraint_spec,
                    latest_version, coupling_score, risk_score, risk_level,
                    candidate_name, candidate_kind, verdict, trust_obs, trust_ver,
                    trust_ai, has_capsule, capsule_path, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dep_id,
                    analysis_id,
                    name,
                    pinned_version,
                    raw_spec,
                    constraint_spec,
                    latest_version,
                    coupling_score,
                    risk_score,
                    risk_level,
                    candidate_name,
                    candidate_kind,
                    verdict,
                    trust_obs,
                    trust_ver,
                    trust_ai,
                    1 if has_capsule else 0,
                    capsule_path,
                    json.dumps(extra_data) if extra_data else None,
                ),
            )

    def get_dependencies_for_analysis(self, analysis_id: str) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dependencies
                WHERE analysis_id = ?
                ORDER BY risk_score DESC, name ASC
                """,
                (analysis_id,),
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["has_capsule"] = bool(item["has_capsule"])
                if item.get("data_json"):
                    try:
                        item["extra"] = json.loads(item["data_json"])
                    except Exception:
                        item["extra"] = {}
                results.append(item)
            return results

    def save_capsule(
        self,
        analysis_id: str,
        dependency_name: str,
        capsule_data: dict[str, Any],
        html_content: str | None = None,
        markdown_content: str | None = None,
    ):
        capsule_id = f"{analysis_id}_{dependency_name}"
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO capsules (
                    id, analysis_id, dependency_name, capsule_json,
                    html_content, markdown_content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    capsule_id,
                    analysis_id,
                    dependency_name,
                    json.dumps(capsule_data),
                    html_content,
                    markdown_content,
                    now,
                ),
            )
            # Mark dependency has_capsule
            conn.execute(
                """
                UPDATE dependencies
                SET has_capsule = 1, capsule_path = ?
                WHERE analysis_id = ? AND name = ?
                """,
                (f"capsules/{dependency_name}/capsule.html", analysis_id, dependency_name),
            )

    def get_capsule(self, analysis_id: str, dependency_name: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM capsules
                WHERE (analysis_id = ? AND dependency_name = ?)
                   OR (dependency_name = ? AND analysis_id = (SELECT id FROM analyses ORDER BY started_at DESC LIMIT 1))
                LIMIT 1
                """,
                (analysis_id, dependency_name, dependency_name),
            ).fetchone()
            if not row:
                row2 = conn.execute(
                    "SELECT * FROM capsules WHERE dependency_name = ? ORDER BY created_at DESC LIMIT 1",
                    (dependency_name,),
                ).fetchone()
                if not row2:
                    return None
                row = row2

            item = dict(row)
            try:
                item["data"] = json.loads(item["capsule_json"])
            except Exception:
                item["data"] = {}
            return item

    def seed_from_disk(self, capsule_dir: Path):
        """Seed database from existing capsules on disk if database is currently empty."""
        with self._get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            if count > 0:
                return

        caps_folder = capsule_dir / "capsules"
        if not caps_folder.is_dir():
            return

        initial_id = "initial_analysis"
        self.create_analysis(
            analysis_id=initial_id,
            repo_url="https://github.com/rishrek/LinkWatch",
            repo_name="rishrek/LinkWatch",
        )

        capsule_count = 0
        for sub in caps_folder.iterdir():
            if not sub.is_dir():
                continue
            cap_json_file = sub / "capsule.json"
            if not cap_json_file.is_file():
                continue
            try:
                cap_data = json.loads(cap_json_file.read_text(encoding="utf-8"))
                dep = cap_data.get("dependency", {})
                dep_name = dep.get("name", sub.name)
                pinned = dep.get("pinned_version")
                raw = dep.get("raw_spec", "")
                latest = dep.get("latest_version")
                verdict = cap_data.get("overall_verdict", "NOT EXECUTED")
                rep = cap_data.get("proposed_replacement")
                cand_name = rep.get("name") if rep else "None (Monitor)"
                cand_kind = rep.get("kind") if rep else "none"
                ts = cap_data.get("provenance_summary", {})
                obs = ts.get("observed_count", 0)
                ver = ts.get("verified_by_execution_count", 0)
                ai = ts.get("ai_generated_count", 0)
                usage = cap_data.get("usage_summary", {})
                coupling = float(usage.get("coupling_score", 0.0))

                html_file = sub / "capsule.html"
                md_file = sub / "capsule.md"
                html_str = html_file.read_text(encoding="utf-8") if html_file.is_file() else ""
                md_str = md_file.read_text(encoding="utf-8") if md_file.is_file() else ""

                self.save_dependency(
                    analysis_id=initial_id,
                    name=dep_name,
                    pinned_version=pinned,
                    raw_spec=raw,
                    constraint_spec=dep.get("constraint"),
                    latest_version=latest,
                    coupling_score=coupling,
                    risk_score=coupling,
                    risk_level="HIGH" if coupling > 5 else "LOW",
                    candidate_name=cand_name,
                    candidate_kind=cand_kind,
                    verdict=verdict,
                    trust_obs=obs,
                    trust_ver=ver,
                    trust_ai=ai,
                    has_capsule=True,
                    capsule_path=f"capsules/{dep_name}/capsule.html",
                )

                self.save_capsule(
                    analysis_id=initial_id,
                    dependency_name=dep_name,
                    capsule_data=cap_data,
                    html_content=html_str,
                    markdown_content=md_str,
                )
                capsule_count += 1
            except Exception:
                continue

        self.complete_analysis(
            analysis_id=initial_id,
            message="Initial capsules loaded from disk",
            status="COMPLETED",
            analyzed_count=capsule_count,
            capsule_count=capsule_count,
        )
