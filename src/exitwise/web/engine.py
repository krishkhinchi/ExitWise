"""Analysis engine for Exitwise dynamic repository inspection, security validation, and capsule building."""

import ipaddress
import json
import re
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from exitwise.ai.client import GemmaClient
from exitwise.ai.grounding import validate_replacement_candidate
from exitwise.capsule.builder import build_dependency_capsule
from exitwise.capsule.render import (
    render_capsule_html,
    render_capsule_markdown,
    render_index_html,
)
from exitwise.capsule.schema import get_capsule_json_schema
from exitwise.capsule.verify import write_manifest_and_scripts
from exitwise.compare.diff import compare_test_runs
from exitwise.compare.gaps import surface_compatibility_gaps
from exitwise.config import DEFAULT_GEMMA_MODEL
from exitwise.ingest.manifests import scan_all_manifests
from exitwise.ingest.repo import prepare_workspace
from exitwise.models import (
    DependencyRecord,
    DifferentialTest,
    Limitation,
    MigrationStep,
    Provenance,
)
from exitwise.sandbox.envs import discover_python_interpreters
from exitwise.sandbox.patching import execute_patch_with_repair
from exitwise.sandbox.runner import run_differential_test, run_repo_suite
from exitwise.signals.github import fetch_github_health
from exitwise.signals.osv import query_osv_vulnerabilities
from exitwise.signals.py_compat import evaluate_python_compatibility
from exitwise.signals.pypi import fetch_pypi_metadata
from exitwise.signals.scoring import assess_dependency_risk
from exitwise.usage.ast_scanner import scan_repo_usage_for_dependency, _get_repo_parsed_files
from exitwise.usage.coupling import compute_usage_coupling
from exitwise.usage.non_python import scan_non_python_references, _get_non_python_files
from exitwise.web.db import AnalysisDB

RE_GITHUB_PATH = re.compile(r"^/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$")
RESERVED_GITHUB_PATHS = {
    "settings", "organizations", "orgs", "explore", "topics", "trending",
    "collections", "events", "features", "security", "enterprise", "pricing",
    "login", "join", "about", "contact", "marketplace", "pulls", "issues",
}


def validate_github_url(raw_url: str) -> tuple[bool, str, str, str]:
    if not raw_url or not isinstance(raw_url, str):
        return False, "Repository URL cannot be empty.", "", ""

    url_str = raw_url.strip()

    if "@" in url_str.split("/")[0] or "@" in urlparse(url_str).netloc:
        return False, "Personal access tokens or credentials must not be included in the URL.", "", ""

    try:
        parsed = urlparse(url_str)
    except Exception:
        return False, "Invalid URL structure.", "", ""

    if parsed.scheme.lower() not in ("https", "http"):
        return False, "Only HTTP/HTTPS URLs are supported.", "", ""

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL missing host name.", "", ""

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False, "Private network and localhost addresses are prohibited.", "", ""
    except ValueError:
        pass

    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        return False, "Localhost and internal cloud metadata addresses are prohibited.", "", ""

    if hostname not in ("github.com", "www.github.com"):
        return False, f"Only GitHub repositories (github.com) are supported. Found: {hostname}", "", ""

    path = parsed.path
    match = RE_GITHUB_PATH.match(path)
    if not match:
        return False, "Invalid GitHub repository path. Expected format: https://github.com/owner/repository", "", ""

    owner, repo = match.groups()
    if owner.lower() in RESERVED_GITHUB_PATHS:
        return False, f"'{owner}' is a reserved GitHub path, not a repository owner.", "", ""

    repo = repo.removesuffix(".git")
    normalized_url = f"https://github.com/{owner}/{repo}"
    return True, normalized_url, owner, repo


def detect_project_ecosystem(repo_dir: Path) -> dict[str, Any]:
    python_manifests = []
    python_patterns = [
        "requirements*.txt", "pyproject.toml", "setup.py", "setup.cfg",
        "Pipfile", "Pipfile.lock", "poetry.lock", "pdm.lock",
    ]
    for pat in python_patterns:
        python_manifests.extend([p.name for p in repo_dir.glob(pat)])

    js_patterns = ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
    js_manifests = [p.name for pat in js_patterns for p in repo_dir.glob(pat)]
    rust_manifests = [p.name for p in repo_dir.glob("Cargo.toml")]
    go_manifests = [p.name for p in repo_dir.glob("go.mod")]

    if python_manifests or any(repo_dir.glob("*.py")) or any(repo_dir.glob("**/*.py")):
        return {
            "ecosystem": "Python", "supported": True, "manifests": python_manifests,
            "has_tests": (repo_dir / "tests").is_dir() or any(repo_dir.glob("**/test_*.py")),
        }
    elif js_manifests:
        return {"ecosystem": "JavaScript / Node.js", "supported": False, "manifests": js_manifests,
                "reason": "Exitwise currently supports deep Python dependency resilience analysis. Node.js support is coming in v2."}
    elif rust_manifests:
        return {"ecosystem": "Rust", "supported": False, "manifests": rust_manifests,
                "reason": "Rust ecosystem detected. Deep capsule generation currently targets Python."}
    elif go_manifests:
        return {"ecosystem": "Go", "supported": False, "manifests": go_manifests,
                "reason": "Go ecosystem detected. Deep capsule generation currently targets Python."}
    else:
        return {"ecosystem": "Generic / Unknown", "supported": False, "manifests": [],
                "reason": "No supported dependency manifests discovered in repository root."}


def _fetch_signals_for_dep(disp_name: str, pinned_version: str | None, ev_base: int) -> dict[str, Any]:
    """Fetch PyPI + OSV + GitHub signals concurrently for one dependency."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_pypi = pool.submit(fetch_pypi_metadata, disp_name, pinned_version, ev_base, False)
        f_osv = pool.submit(query_osv_vulnerabilities, disp_name, pinned_version, ev_base + 1, False)
        pypi, pypi_ev = f_pypi.result(timeout=15)
        f_gh = pool.submit(fetch_github_health, disp_name, pypi.project_urls, ev_base + 2, False)
        vulns, osv_ev = f_osv.result(timeout=15)
        gh, gh_ev = f_gh.result(timeout=15)
    return {"pypi": pypi, "pypi_ev": pypi_ev, "vulns": vulns, "osv_ev": osv_ev, "gh": gh}


def run_repository_analysis(
    analysis_id: str,
    repo_url: str,
    db: AnalysisDB,
    output_dir: Path,
):
    """Execute real dynamic analysis across all 8 stages for a GitHub repository."""
    try:
        # STAGE 1
        db.update_analysis_stage(analysis_id, stage_index=1, stage_name="Validating repository",
            message="Validating GitHub repository URL and security boundaries...", progress=10)

        is_valid, val_res, owner, repo = validate_github_url(repo_url)
        if not is_valid:
            db.fail_analysis(analysis_id, f"Validation error: {val_res}")
            return
        normalized_url = val_res

        # STAGE 2
        db.update_analysis_stage(analysis_id, stage_index=2, stage_name="Retrieving repository contents",
            message=f"Cloning {owner}/{repo} (depth 1) into isolated workspace...", progress=20)

        with tempfile.TemporaryDirectory(prefix=f"exitwise_job_{analysis_id}_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            try:
                repo_info = prepare_workspace(normalized_url, tmp_path)
            except Exception as clone_err:
                db.fail_analysis(analysis_id, f"Failed to retrieve repository from GitHub: {clone_err}")
                return

            commit_sha = repo_info.commit_sha
            db.update_analysis_stage(analysis_id, stage_index=2, stage_name="Retrieving repository contents",
                message=f"Retrieved commit {commit_sha[:8]} successfully.", progress=30, commit_sha=commit_sha)

            # STAGE 3
            db.update_analysis_stage(analysis_id, stage_index=3, stage_name="Detecting dependency manifests",
                message="Scanning repository for dependency manifests and lockfiles...", progress=35)

            eco = detect_project_ecosystem(tmp_path)
            if not eco["supported"]:
                db.update_analysis_stage(analysis_id, stage_index=3, stage_name="Detecting dependency manifests",
                    message=f"Detected ecosystem: {eco['ecosystem']}. {eco.get('reason', '')}",
                    progress=100, status="COMPLETED_WITH_WARNINGS",
                    ecosystem=eco["ecosystem"], manifest_files=eco.get("manifests", []))
                db.complete_analysis(analysis_id,
                    message=f"Analysis completed: {eco['ecosystem']} ecosystem detected. Deep Python analysis engine skipped.",
                    status="COMPLETED_WITH_WARNINGS")
                return

            reqs, drifts, drift_evs = scan_all_manifests(tmp_path)
            manifest_names = [p.name for p in repo_info.manifest_files]

            if not reqs:
                db.update_analysis_stage(analysis_id, stage_index=3, stage_name="Detecting dependency manifests",
                    message="No Python dependencies discovered in manifests.", progress=100, status="COMPLETED",
                    ecosystem="Python", manifest_files=manifest_names, discovered_count=0)
                db.complete_analysis(analysis_id, message="Repository inspected. No external dependencies declared.",
                    status="COMPLETED", analyzed_count=0, capsule_count=0)
                return

            by_dep: dict[str, list] = {}
            for r in reqs:
                by_dep.setdefault(r.name, []).append(r)

            discovered_count = len(by_dep)
            db.update_analysis_stage(analysis_id, stage_index=3, stage_name="Detecting dependency manifests",
                message=f"Discovered {discovered_count} dependencies across {len(manifest_names)} manifests.",
                progress=45, ecosystem="Python", manifest_files=manifest_names, discovered_count=discovered_count)

            # STAGE 4: parallel signal fetch for all deps
            db.update_analysis_stage(analysis_id, stage_index=4, stage_name="Inspecting dependencies",
                message=f"Fetching PyPI + OSV + GitHub signals for {discovered_count} dependencies in parallel...",
                progress=50)

            gemma = GemmaClient(model_id=DEFAULT_GEMMA_MODEL)
            interpreters = discover_python_interpreters()
            available_interpreters = [i for i in interpreters if i.is_available]

            ev_counter = 1
            dep_ev_bases: dict[str, int] = {}
            for dep_name in by_dep:
                dep_ev_bases[dep_name] = ev_counter
                ev_counter += 8

            signal_results: dict[str, dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=min(8, discovered_count)) as pool:
                futures = {
                    pool.submit(
                        _fetch_signals_for_dep,
                        by_dep[dep_name][0].display_name,
                        by_dep[dep_name][0].pinned_version,
                        dep_ev_bases[dep_name],
                    ): dep_name
                    for dep_name in by_dep
                }
                for fut in as_completed(futures):
                    dep_name = futures[fut]
                    try:
                        signal_results[dep_name] = fut.result()
                    except Exception as sig_err:
                        from exitwise.signals.pypi import PyPIMetadata
                        from exitwise.models import Evidence
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc).isoformat()
                        eb = dep_ev_bases[dep_name]
                        signal_results[dep_name] = {
                            "pypi": PyPIMetadata(name=dep_name, latest_version="unknown"),
                            "pypi_ev": Evidence(id=f"EV-PYPI-{eb:04d}", source="pypi_api", kind="error",
                                                observed_value={"error": str(sig_err)}, timestamp=now),
                            "vulns": [],
                            "osv_ev": Evidence(id=f"EV-OSV-{eb+1:04d}", source="osv_api", kind="error",
                                               observed_value={}, timestamp=now),
                            "gh": None,
                        }

            # STAGE 5
            db.update_analysis_stage(analysis_id, stage_index=5, stage_name="Gathering risk evidence",
                message=f"Risk signals collected for {discovered_count} dependencies.", progress=60)

            # STAGE 6: warm caches once, then map usage per dep
            db.update_analysis_stage(analysis_id, stage_index=6, stage_name="Mapping dependency usage",
                message="Parsing repository source files (one-time AST walk)...", progress=65)

            _get_repo_parsed_files(tmp_path)
            _get_non_python_files(tmp_path)

            dep_scan_results: list[dict[str, Any]] = []
            total_deps = len(by_dep)

            for dep_idx, (dep_name, r_list) in enumerate(by_dep.items()):
                first_r = r_list[0]
                disp_name = first_r.display_name

                stage6_pct = 65 + int(((dep_idx + 1) / total_deps) * 10)
                db.update_analysis_stage(analysis_id, stage_index=6, stage_name="Mapping dependency usage",
                    message=f"Mapping usage [{dep_idx + 1}/{total_deps}]: {disp_name}",
                    progress=min(stage6_pct, 74))

                sigs = signal_results.get(dep_name, {})
                pypi = sigs.get("pypi")
                pypi_ev = sigs.get("pypi_ev")
                osv_ev = sigs.get("osv_ev")
                vulns = sigs.get("vulns", [])
                gh = sigs.get("gh")
                eb = dep_ev_bases[dep_name]

                py_compat, _ = evaluate_python_compatibility(
                    disp_name,
                    pypi.requires_python if pypi else None,
                    pypi.classifiers if pypi else [],
                    eb + 3,
                )
                conflict_evs = [d.evidence_id for d in drifts if d.package == dep_name]
                indicators, risk_score, risk_level = assess_dependency_risk(
                    disp_name, first_r.pinned_version, pypi, vulns, gh, py_compat,
                    conflict_evs, is_runtime_dependency=(not first_r.is_dev),
                    risk_counter_start=eb + 4,
                )

                ast_locs, ast_ev = scan_repo_usage_for_dependency(tmp_path, disp_name, eb + 5)
                non_py_locs = scan_non_python_references(tmp_path, disp_name)
                all_locs = ast_locs + non_py_locs
                usage_summary = compute_usage_coupling(all_locs)

                dep_scan_results.append({
                    "dep_name": dep_name, "disp_name": disp_name,
                    "r_list": r_list, "first_r": first_r,
                    "pypi": pypi, "pypi_ev": pypi_ev, "osv_ev": osv_ev,
                    "indicators": indicators, "risk_score": risk_score, "risk_level": risk_level,
                    "all_locs": all_locs, "ast_ev": ast_ev, "usage_summary": usage_summary, "eb": eb,
                })

            dep_scan_results.sort(key=lambda x: x["risk_score"], reverse=True)

            # STAGES 7 & 8: replacement eval + capsule generation with per-dep progress
            caps_out_dir = output_dir / "capsules"
            caps_out_dir.mkdir(parents=True, exist_ok=True)
            capsule_limit = min(max(len(dep_scan_results), 3), 8)
            total_capsule_deps = len(dep_scan_results)
            all_capsules: list = []

            for idx, item in enumerate(dep_scan_results):
                disp_name = item["disp_name"]
                first_r = item["first_r"]
                r_list = item["r_list"]
                pypi = item["pypi"]
                pypi_ev = item["pypi_ev"]
                osv_ev = item["osv_ev"]
                indicators = item["indicators"]
                risk_score = item["risk_score"]
                risk_level = item["risk_level"]
                all_locs = item["all_locs"]
                ast_ev = item["ast_ev"]
                usage_summary = item["usage_summary"]
                eb = item["eb"]

                # Per-dep progress: Stage 7 (75->85%), Stage 8 (85->97%)
                half = (total_capsule_deps // 2) or 1
                if idx < half:
                    stage_idx, stage_nm = 7, "Evaluating replacement candidates"
                    pct = 75 + int((idx / total_capsule_deps) * 10)
                else:
                    stage_idx, stage_nm = 8, "Preparing Dependency Exit Capsules"
                    pct = 85 + int((idx / total_capsule_deps) * 12)
                db.update_analysis_stage(analysis_id, stage_index=stage_idx, stage_name=stage_nm,
                    message=f"[{idx + 1}/{total_capsule_deps}] {disp_name} — {risk_level} ({risk_score:.1f})",
                    progress=min(pct, 97))

                should_build_capsule = (idx < capsule_limit) or (risk_score >= 3.0)
                primary_candidate = None
                validated_candidates = []
                migration_steps = []
                patch_attempt = None
                diff_test = None
                test_runs: list = []
                gaps: list = []
                concerns: list = []
                limits: list = []
                verdict = "NOT EXECUTED"
                snippets = [loc.snippet for loc in all_locs if loc.snippet]

                if should_build_capsule:
                    try:
                        gemma.triage_risk(disp_name, first_r.pinned_version or "",
                            [r.source_file for r in r_list],
                            [pypi_ev.model_dump(), osv_ev.model_dump()])
                    except Exception:
                        pass

                    try:
                        usage_char = gemma.characterize_usage(
                            disp_name, ast_ev.id, usage_summary.total_files,
                            usage_summary.is_monkey_patched, snippets)
                        usage_summary.ai_characterization = usage_char.narrative_summary
                        usage_summary.ai_characterization_evidence_ids = usage_char.cited_evidence_ids
                        hazards = list(usage_char.hazard_notes)
                    except Exception:
                        hazards = []

                    if usage_summary.is_monkey_patched:
                        hazards.append(f"Dynamic monkey-patching of '{disp_name}' detected.")

                    try:
                        rep_out = gemma.propose_replacement(
                            disp_name, first_r.pinned_version or "",
                            usage_summary.coupling_score,
                            usage_summary.ai_characterization or "",
                            hazards, ast_ev.id)
                        for cand in rep_out.candidates:
                            val_cand = validate_replacement_candidate(cand.name, ast_ev.id, offline_mode=False)
                            val_cand.tradeoffs = cand.tradeoffs
                            validated_candidates.append(val_cand)
                            if val_cand.status == "ACCEPTED" and primary_candidate is None:
                                primary_candidate = val_cand
                    except Exception:
                        pass

                    if primary_candidate:
                        try:
                            mig_plan = gemma.generate_migration_plan(
                                disp_name, primary_candidate.name,
                                primary_candidate.kind == "stdlib", snippets)
                            for s_idx, s in enumerate(mig_plan.ordered_steps, start=1):
                                migration_steps.append(MigrationStep(
                                    order=s_idx, description=s, provenance=Provenance.AI_GENERATED))

                            if repo_info.has_tests and available_interpreters:
                                exec_tmp = tempfile.mkdtemp(prefix=f"exitwise_exec_{disp_name}_")
                                exec_path = Path(exec_tmp)
                                try:
                                    shutil.copytree(tmp_path, exec_path, dirs_exist_ok=True)
                                    patch_attempt = execute_patch_with_repair(
                                        exec_path, mig_plan.unified_diff, gemma_client=gemma)
                                    curr_py = available_interpreters[0].version_str
                                    py_exe = available_interpreters[0].executable_path
                                    base_ev_id = f"EV-EXEC-BASE-{eb + 6:04d}"
                                    cand_ev_id = f"EV-EXEC-CAND-{eb + 7:04d}"
                                    baseline_run = run_repo_suite(tmp_path, py_exe, repo_info.test_command,
                                        side="baseline", python_ver=curr_py, evidence_id=base_ev_id)
                                    candidate_run = run_repo_suite(exec_path, py_exe, repo_info.test_command,
                                        side="candidate", python_ver=curr_py, evidence_id=cand_ev_id)
                                    test_runs = [baseline_run, candidate_run]
                                    diff_summary = compare_test_runs(baseline_run, candidate_run)
                                    try:
                                        diff_test_out = gemma.generate_differential_tests(
                                            disp_name, primary_candidate.name,
                                            usage_summary.distinct_symbols, snippets)
                                        diff_test = DifferentialTest(
                                            test_name=diff_test_out.test_file_name,
                                            code=diff_test_out.test_code,
                                            target_apis=diff_test_out.exercised_apis,
                                            provenance=Provenance.AI_GENERATED)
                                        base_p, _ = run_differential_test(tmp_path, py_exe, diff_test, curr_py, base_ev_id)
                                        cand_p, _ = run_differential_test(exec_path, py_exe, diff_test, curr_py, cand_ev_id)
                                        diff_test.baseline_passed = base_p
                                        diff_test.candidate_passed = cand_p
                                    except Exception:
                                        pass
                                    gaps, concerns, limits = surface_compatibility_gaps(
                                        disp_name, primary_candidate.name, patch_attempt,
                                        diff_summary, [diff_test] if diff_test else [],
                                        gap_counter_start=eb + 8)
                                    if baseline_run.exit_code == 0 and candidate_run.exit_code == 0:
                                        verdict = "READY"
                                    elif candidate_run.failed > 0:
                                        verdict = "READY WITH GAPS"
                                    else:
                                        verdict = "ANALYZED"
                                except Exception as ex_err:
                                    limits.append(Limitation(
                                        description=f"Sandbox test run failed: {ex_err}",
                                        category="sandbox_execution", provenance=Provenance.OBSERVED))
                                    verdict = "NOT EXECUTED"
                                finally:
                                    shutil.rmtree(exec_tmp, ignore_errors=True)
                            else:
                                limits.append(Limitation(
                                    description="Repository tests not configured or execution environment restricted.",
                                    category="execution_skipped", provenance=Provenance.OBSERVED))
                                verdict = "ANALYZED" if risk_score < 5 else "RISK DETECTED"
                        except Exception:
                            verdict = "NEEDS REVIEW"

                    if not gaps and not concerns and not limits:
                        gaps, concerns, limits = surface_compatibility_gaps(
                            disp_name,
                            primary_candidate.name if primary_candidate else "None",
                            patch_attempt, None, [], gap_counter_start=eb + 8)

                    dep_rec = DependencyRecord(
                        name=disp_name, raw_spec=first_r.raw,
                        source_manifests=[r.source_file for r in r_list],
                        pinned_version=first_r.pinned_version, constraint=first_r.specifier,
                        latest_version=pypi.latest_version, provenance=Provenance.OBSERVED)

                    capsule = build_dependency_capsule(
                        dependency_record=dep_rec, target_repo_url=normalized_url,
                        target_commit_sha=commit_sha,
                        tested_python_versions=[i.version_str for i in available_interpreters],
                        gemma_model_id=gemma.model_id, risk_indicators=indicators,
                        usage_summary=usage_summary, usage_locations=all_locs,
                        proposed_replacement=primary_candidate,
                        replacement_candidates=validated_candidates,
                        migration_steps=migration_steps, patch_attempt=patch_attempt,
                        suggested_tests=[diff_test] if diff_test else [],
                        executed_test_results=test_runs, compatibility_gaps=gaps,
                        open_concerns=concerns, limitations=limits)

                    if verdict != "NOT EXECUTED":
                        capsule.overall_verdict = verdict

                    cap_dir = caps_out_dir / disp_name
                    cap_dir.mkdir(parents=True, exist_ok=True)
                    (cap_dir / "evidence").mkdir(exist_ok=True)
                    cap_json_str = capsule.model_dump_json(indent=2)
                    cap_html_str = render_capsule_html(capsule)
                    cap_md_str = render_capsule_markdown(capsule)
                    (cap_dir / "capsule.json").write_text(cap_json_str, encoding="utf-8")
                    (cap_dir / "capsule.schema.json").write_text(
                        json.dumps(get_capsule_json_schema(), indent=2), encoding="utf-8")
                    (cap_dir / "capsule.md").write_text(cap_md_str, encoding="utf-8")
                    (cap_dir / "capsule.html").write_text(cap_html_str, encoding="utf-8")
                    write_manifest_and_scripts(cap_dir, capsule)

                    db.save_capsule(analysis_id=analysis_id, dependency_name=disp_name,
                        capsule_data=capsule.model_dump(),
                        html_content=cap_html_str, markdown_content=cap_md_str)
                    all_capsules.append(capsule)

                    ts = capsule.provenance_summary
                    obs_count = ts.observed_count
                    ver_count = ts.verified_by_execution_count
                    ai_count = ts.ai_generated_count
                    has_cap = True
                    cand_display = primary_candidate.name if primary_candidate else "None (Monitor)"
                    cand_kind = primary_candidate.kind if primary_candidate else "none"
                else:
                    obs_count = len(indicators) + len(all_locs)
                    ver_count = 0
                    ai_count = 0
                    verdict = "RISK DETECTED" if risk_score >= 5 else "ANALYZED"
                    cand_display = "None (Monitor)"
                    cand_kind = "none"
                    has_cap = False

                db.save_dependency(
                    analysis_id=analysis_id, name=disp_name,
                    pinned_version=first_r.pinned_version, raw_spec=first_r.raw,
                    constraint_spec=first_r.specifier,
                    latest_version=pypi.latest_version if pypi else "Unknown",
                    coupling_score=usage_summary.coupling_score,
                    risk_score=risk_score, risk_level=risk_level,
                    candidate_name=cand_display, candidate_kind=cand_kind,
                    verdict=verdict, trust_obs=obs_count, trust_ver=ver_count, trust_ai=ai_count,
                    has_capsule=has_cap,
                    capsule_path=f"capsules/{disp_name}/capsule.html" if has_cap else None,
                    extra_data={
                        "indicators": [ind.model_dump() for ind in indicators],
                        "usage_files": usage_summary.total_files,
                        "usage_occurrences": usage_summary.total_occurrences,
                    },
                )

            if all_capsules:
                (output_dir / "index.json").write_text(
                    json.dumps([c.model_dump() for c in all_capsules], indent=2), encoding="utf-8")
                (output_dir / "index.html").write_text(
                    render_index_html(all_capsules, normalized_url), encoding="utf-8")

            db.complete_analysis(analysis_id,
                message=f"Analysis complete. {discovered_count} dependencies inspected, {len(all_capsules)} capsules ready.",
                status="COMPLETED", analyzed_count=discovered_count, capsule_count=len(all_capsules))

    except Exception as e:
        db.fail_analysis(analysis_id, f"Analysis unexpected failure: {e}")

