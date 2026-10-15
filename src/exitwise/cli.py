"""Exitwise CLI: The Gemma 4 Powered Dependency Exit Capsule Generator."""

import json
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from exitwise.guard import check_python_version
from exitwise.config import DEFAULT_GEMMA_MODEL, DEFAULT_OUTPUT_DIR
from exitwise.ingest.repo import prepare_workspace
from exitwise.ingest.manifests import scan_all_manifests
from exitwise.signals.pypi import fetch_pypi_metadata
from exitwise.signals.osv import query_osv_vulnerabilities
from exitwise.signals.github import fetch_github_health
from exitwise.signals.py_compat import evaluate_python_compatibility
from exitwise.signals.scoring import assess_dependency_risk
from exitwise.usage.ast_scanner import scan_repo_usage_for_dependency, find_undeclared_imports
from exitwise.usage.non_python import scan_non_python_references
from exitwise.usage.coupling import compute_usage_coupling
from exitwise.ai.client import GemmaClient
from exitwise.ai.grounding import validate_replacement_candidate
from exitwise.sandbox.envs import discover_python_interpreters, scrub_child_environment
from exitwise.sandbox.patching import execute_patch_with_repair
from exitwise.sandbox.runner import run_repo_suite, run_differential_test
from exitwise.compare.diff import compare_test_runs
from exitwise.compare.gaps import surface_compatibility_gaps
from exitwise.capsule.builder import build_dependency_capsule
from exitwise.capsule.schema import get_capsule_json_schema
from exitwise.capsule.render import (
    render_capsule_html,
    render_capsule_markdown,
    render_index_html,
)
from exitwise.capsule.verify import verify_capsule_directory, write_manifest_and_scripts
from exitwise.models import DependencyRecord, MigrationStep, Provenance

console = Console()


def _fetch_signals(disp_name, pinned_version, ev_counter, offline_signals):
    """Fetch PyPI, OSV, and GitHub signals concurrently for a single dependency."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_pypi = pool.submit(fetch_pypi_metadata, disp_name, pinned_version, ev_counter, offline_signals)
        f_osv = pool.submit(query_osv_vulnerabilities, disp_name, pinned_version, ev_counter + 1, offline_signals)
        # GitHub URL is in PyPI metadata — fetch PyPI first, then GitHub in parallel with OSV
        pypi, pypi_ev = f_pypi.result()
        f_gh = pool.submit(fetch_github_health, disp_name, pypi.project_urls, ev_counter + 2, offline_signals)
        vulns, osv_ev = f_osv.result()
        gh, gh_ev = f_gh.result()
    return pypi, pypi_ev, vulns, osv_ev, gh, gh_ev


@click.group()
@click.version_option(package_name="exitwise")
def cli():
    """Exitwise: AI-assisted Dependency Exit Capsule Generator for Python."""
    # Enforce strict Python runtime guard (>=3.12, <3.14)
    check_python_version()


@cli.command()
@click.argument("target")
@click.option("--only", help="Comma-separated list of dependencies to scan")
@click.option("--offline-signals", is_flag=True, help="Use offline cached data for PyPI/OSV")
def scan(target: str, only: str | None, offline_signals: bool):
    """Stage 1: Scan repository manifests, query PyPI/OSV signals, and rank at-risk dependencies."""
    with tempfile.TemporaryDirectory(prefix="exitwise_scan_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            repo_info = prepare_workspace(target, tmp_path)
        except Exception as e:
            console.print(f"[bold red]Target unreachable or invalid:[/bold red] {e}")
            sys.exit(3)

        reqs, drifts, drift_evs = scan_all_manifests(tmp_path)
        if not reqs:
            console.print("[yellow]No Python dependencies found in target repository manifests.[/yellow]")
            return

        # Filter by --only if provided
        target_names = [x.strip().lower() for x in only.split(",")] if only else None

        table = Table(title=f"Exitwise Risk Scan: {target}", header_style="bold cyan")
        table.add_column("Dependency", style="bold")
        table.add_column("Pinned", style="dim")
        table.add_column("Latest PyPI")
        table.add_column("Risk Score", justify="right")
        table.add_column("Level", justify="center")
        table.add_column("Key Findings")

        seen_deps = set()
        ev_counter = 1

        for r in reqs:
            if r.name in seen_deps:
                continue
            if target_names and r.name not in target_names:
                continue
            seen_deps.add(r.name)

            pypi, pypi_ev, vulns, osv_ev, gh, gh_ev = _fetch_signals(
                r.display_name, r.pinned_version, ev_counter, offline_signals
            )
            ev_counter += 3
            py_compat, compat_ev = evaluate_python_compatibility(r.display_name, pypi.requires_python, pypi.classifiers, ev_counter)
            ev_counter += 1

            conflict_evs = [d.evidence_id for d in drifts if d.package == r.name]
            indicators, score, level = assess_dependency_risk(
                r.display_name,
                r.pinned_version,
                pypi,
                vulns,
                gh,
                py_compat,
                conflict_evs,
                is_runtime_dependency=(not r.is_dev),
                risk_counter_start=ev_counter,
            )

            level_style = {
                "CRITICAL": "bold red",
                "HIGH": "bold orange3",
                "MEDIUM": "bold yellow",
                "LOW": "green",
                "NEGLIGIBLE": "dim",
            }.get(level, "white")

            finding_summary = "; ".join([ind.observed_value for ind in indicators[:2]]) or "No major risks"
            table.add_row(
                r.display_name,
                r.pinned_version or "unpinned",
                pypi.latest_version or "unknown",
                f"{score:.1f}",
                f"[{level_style}]{level}[/{level_style}]",
                finding_summary,
            )

        console.print(table)


@cli.command()
@click.argument("target")
@click.option("--only", help="Filter target dependencies")
def usage(target: str, only: str | None):
    """Stage 2: Map AST usage locations, dynamic patching, and coupling scores."""
    with tempfile.TemporaryDirectory(prefix="exitwise_usage_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            repo_info = prepare_workspace(target, tmp_path)
        except Exception as e:
            console.print(f"[bold red]Target unreachable:[/bold red] {e}")
            sys.exit(3)

        reqs, _, _ = scan_all_manifests(tmp_path)
        target_names = [x.strip().lower() for x in only.split(",")] if only else None
        seen_deps = set()

        table = Table(title="Dependency Usage & Coupling Mapping", header_style="bold magenta")
        table.add_column("Dependency", style="bold")
        table.add_column("Files Touched", justify="right")
        table.add_column("Occurrences", justify="right")
        table.add_column("Dynamic Patch?", justify="center")
        table.add_column("Coupling Score", justify="right")

        for r in reqs:
            if r.name in seen_deps:
                continue
            if target_names and r.name not in target_names:
                continue
            seen_deps.add(r.name)

            ast_locs, _ = scan_repo_usage_for_dependency(tmp_path, r.display_name)
            non_py_locs = scan_non_python_references(tmp_path, r.display_name)
            all_locs = ast_locs + non_py_locs
            summary = compute_usage_coupling(all_locs)

            patch_str = "[bold red]YES[/bold red]" if summary.is_monkey_patched else "[dim]No[/dim]"
            table.add_row(
                r.display_name,
                str(summary.total_files),
                str(summary.total_occurrences),
                patch_str,
                f"{summary.coupling_score:.1f}/10",
            )

        console.print(table)

        # Undeclared imports check
        declared = {r.display_name for r in reqs}
        undeclared = find_undeclared_imports(tmp_path, declared)
        if undeclared:
            console.print("\n[bold yellow]Undeclared Transitive / Missing Imports Discovered:[/bold yellow]")
            for dist, f, l in undeclared:
                console.print(f"  • [bold]{dist}[/bold] imported in [cyan]{f}:{l}[/cyan] but not in manifests")


@cli.command()
@click.argument("target")
@click.option("--only", help="Filter dependencies to process (comma-separated)")
@click.option("--model", default=DEFAULT_GEMMA_MODEL, help="Gemma 4 model ID")
@click.option("--python-ver", "python_ver", default="both", help="Python matrix: 3.12, 3.13, or both")
@click.option("--offline-signals", is_flag=True, help="Disable network calls to PyPI/OSV")
@click.option("--out", "out_dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for capsules")
@click.option("--no-cache", is_flag=True, default=True, help="Bypass cached AI responses")
def run(target: str, only: str | None, model: str, python_ver: str, offline_signals: bool, out_dir: str, no_cache: bool):
    """Execute full Exitwise resilience pipeline and generate Dependency Exit Capsules."""
    console.print(
        f"[bold cyan]Exitwise[/bold cyan] — Gemma 4 Dependency Exit Capsule Pipeline\n"
        f"[dim]Model: {model} | Target: {target} | Output: {out_dir}[/dim]\n"
    )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="exitwise_run_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            repo_info = prepare_workspace(target, tmp_path)
        except Exception as e:
            console.print(f"[bold red]Failed to prepare repository workspace:[/bold red] {e}")
            sys.exit(3)

        reqs, drifts, drift_evs = scan_all_manifests(tmp_path)
        if not reqs:
            console.print("[yellow]No dependencies discovered in repository.[/yellow]")
            return

        # Filter dependencies if --only specified
        target_names = [x.strip().lower() for x in only.split(",")] if only else None
        by_dep: dict[str, list] = {}
        for r in reqs:
            if target_names and r.name not in target_names:
                continue
            by_dep.setdefault(r.name, []).append(r)

        console.print(f"Identified [bold green]{len(by_dep)}[/bold green] unique dependencies to evaluate.\n")

        # Initialize Gemma client & interpreters
        gemma = GemmaClient(model_id=model)
        interpreters = discover_python_interpreters()
        available_interpreters = [i for i in interpreters if i.is_available]

        all_capsules = []
        ev_counter = 1

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            main_task = progress.add_task("[cyan]Processing dependencies...", total=len(by_dep))

            for dep_name, r_list in by_dep.items():
                first_r = r_list[0]
                disp_name = first_r.display_name
                progress.update(main_task, description=f"[cyan]Analyzing [bold]{disp_name}[/bold]...")

                # 1. Signals & Risk Scoring — PyPI + OSV + GitHub fetched concurrently
                pypi, pypi_ev, vulns, osv_ev, gh, gh_ev = _fetch_signals(
                    disp_name, first_r.pinned_version, ev_counter, offline_signals
                )
                ev_counter += 3
                py_compat, compat_ev = evaluate_python_compatibility(disp_name, pypi.requires_python, pypi.classifiers, ev_counter)
                ev_counter += 1

                conflict_evs = [d.evidence_id for d in drifts if d.package == dep_name]
                indicators, score, level = assess_dependency_risk(
                    disp_name,
                    first_r.pinned_version,
                    pypi,
                    vulns,
                    gh,
                    py_compat,
                    conflict_evs,
                    is_runtime_dependency=(not first_r.is_dev),
                    risk_counter_start=ev_counter,
                )

                # Gemma Job 1: Risk Triage
                triage_out = gemma.triage_risk(
                    disp_name,
                    first_r.pinned_version or "",
                    [r.source_file for r in r_list],
                    [pypi_ev.model_dump(), osv_ev.model_dump()],
                )

                # 2. Usage Mapping
                ast_locs, ast_ev = scan_repo_usage_for_dependency(tmp_path, disp_name, ev_counter)
                ev_counter += 1
                non_py_locs = scan_non_python_references(tmp_path, disp_name)
                all_locs = ast_locs + non_py_locs
                usage_summary = compute_usage_coupling(all_locs)

                # Gemma Job 2: Usage Characterization
                snippets = [loc.snippet for loc in all_locs if loc.snippet]
                usage_char = gemma.characterize_usage(
                    disp_name,
                    ast_ev.id,
                    usage_summary.total_files,
                    usage_summary.is_monkey_patched,
                    snippets,
                )
                usage_summary.ai_characterization = usage_char.narrative_summary
                usage_summary.ai_characterization_evidence_ids = usage_char.cited_evidence_ids

                # 3. Gemma Job 3: Propose Replacement Candidates
                hazards = list(usage_char.hazard_notes)  # copy so we don't mutate cached output
                if usage_summary.is_monkey_patched:
                    hazards.append(
                        f"Dynamic monkey-patching of '{disp_name}' detected in repository code: "
                        "migration must preserve patched runtime behaviour."
                    )

                rep_out = gemma.propose_replacement(
                    disp_name,
                    first_r.pinned_version or "",
                    usage_summary.coupling_score,
                    usage_char.narrative_summary,
                    hazards,
                    ast_ev.id,
                )

                # Deterministically validate proposed candidates
                validated_candidates = []
                primary_candidate = None
                for cand in rep_out.candidates:
                    val_cand = validate_replacement_candidate(cand.name, ast_ev.id, offline_signals)
                    val_cand.tradeoffs = cand.tradeoffs
                    validated_candidates.append(val_cand)
                    if val_cand.status == "ACCEPTED" and primary_candidate is None:
                        primary_candidate = val_cand

                # 4. Gemma Job 4: Migration Plan & Diff
                migration_steps = []
                patch_attempt = None
                # Pre-initialize execution result variables so they are always bound
                test_runs: list = []
                diff_test: DifferentialTest | None = None
                gaps: list = []
                concerns: list = []
                limits: list = []

                if primary_candidate:
                    mig_plan = gemma.generate_migration_plan(
                        disp_name,
                        primary_candidate.name,
                        primary_candidate.kind == "stdlib",
                        snippets,
                    )
                    for idx, s in enumerate(mig_plan.ordered_steps, start=1):
                        migration_steps.append(
                            MigrationStep(
                                order=idx,
                                description=s,
                                provenance=Provenance.AI_GENERATED,
                            )
                        )

                    # 5. Sandbox Test Execution (Baseline vs Candidate)
                    # All execution results must be captured before the context manager closes
                    exec_tmp = tempfile.mkdtemp(prefix=f"exitwise_exec_{disp_name}_")
                    exec_path = Path(exec_tmp)
                    try:
                        shutil.copytree(tmp_path, exec_path, dirs_exist_ok=True)

                        patch_attempt = execute_patch_with_repair(
                            exec_path,
                            mig_plan.unified_diff,
                            gemma_client=gemma,
                        )

                        # Determine Python interpreter to use
                        curr_py = available_interpreters[0].version_str if available_interpreters else "3.13"
                        py_exe = available_interpreters[0].executable_path if available_interpreters else sys.executable

                        base_ev_id = f"EV-EXEC-BASE-{ev_counter:04d}"
                        ev_counter += 1
                        baseline_run = run_repo_suite(
                            tmp_path,
                            py_exe,
                            repo_info.test_command,
                            side="baseline",
                            python_ver=curr_py,
                            evidence_id=base_ev_id,
                        )

                        # Run candidate test in exec_path
                        cand_ev_id = f"EV-EXEC-CAND-{ev_counter:04d}"
                        ev_counter += 1
                        candidate_run = run_repo_suite(
                            exec_path,
                            py_exe,
                            repo_info.test_command,
                            side="candidate",
                            python_ver=curr_py,
                            evidence_id=cand_ev_id,
                        )

                        # 6. Gemma Job 5: Differential Tests
                        diff_test_out = gemma.generate_differential_tests(
                            disp_name,
                            primary_candidate.name,
                            usage_summary.distinct_symbols,
                            snippets,
                        )
                        diff_test = DifferentialTest(
                            test_name=diff_test_out.test_file_name,
                            code=diff_test_out.test_code,
                            target_apis=diff_test_out.exercised_apis,
                            provenance=Provenance.AI_GENERATED,
                        )

                        # Execute differential test on both sides
                        base_passed, _base_diff_out = run_differential_test(
                            tmp_path, py_exe, diff_test, curr_py, base_ev_id
                        )
                        cand_passed, _cand_diff_out = run_differential_test(
                            exec_path, py_exe, diff_test, curr_py, cand_ev_id
                        )
                        diff_test.baseline_passed = base_passed
                        diff_test.candidate_passed = cand_passed

                        test_runs = [baseline_run, candidate_run]
                        diff_summary = compare_test_runs(baseline_run, candidate_run)

                        # 7. Gemma Job 6 & Gaps (all results captured; exec_path still alive)
                        gaps, concerns, limits = surface_compatibility_gaps(
                            disp_name,
                            primary_candidate.name,
                            patch_attempt,
                            diff_summary,
                            [diff_test],
                            gap_counter_start=ev_counter,
                        )
                        ev_counter += len(gaps) + 1
                    except Exception as exec_err:
                        # Record execution failure as a NOT_EXECUTED limitation
                        from exitwise.models import Limitation
                        limits.append(
                            Limitation(
                                description=f"Execution stage failed for '{disp_name}': {exec_err}",
                                category="execution_error",
                                provenance=Provenance.OBSERVED,
                            )
                        )
                    finally:
                        # Clean up exec temp dir regardless of success/failure
                        shutil.rmtree(exec_tmp, ignore_errors=True)

                if not gaps and not concerns and not limits:
                    # Always surface at least open concerns and limitations
                    gaps, concerns, limits = surface_compatibility_gaps(
                        disp_name,
                        primary_candidate.name if primary_candidate else "None",
                        patch_attempt,
                        None,
                        [],
                        gap_counter_start=ev_counter,
                    )

                # Assemble Capsule
                dep_rec = DependencyRecord(
                    name=disp_name,
                    raw_spec=first_r.raw,
                    source_manifests=[r.source_file for r in r_list],
                    pinned_version=first_r.pinned_version,
                    constraint=first_r.specifier,
                    latest_version=pypi.latest_version,
                    provenance=Provenance.OBSERVED,
                )

                capsule = build_dependency_capsule(
                    dependency_record=dep_rec,
                    target_repo_url=repo_info.source_url_or_path,
                    target_commit_sha=repo_info.commit_sha,
                    tested_python_versions=[i.version_str for i in available_interpreters],
                    gemma_model_id=gemma.model_id,
                    risk_indicators=indicators,
                    usage_summary=usage_summary,
                    usage_locations=all_locs,
                    proposed_replacement=primary_candidate,
                    replacement_candidates=validated_candidates,
                    migration_steps=migration_steps,
                    patch_attempt=patch_attempt,
                    suggested_tests=[diff_test] if diff_test else [],
                    executed_test_results=test_runs,
                    compatibility_gaps=gaps,
                    open_concerns=concerns,
                    limitations=limits,
                )

                # Write capsule files to disk: capsules/<dependency>/
                cap_dir = out_path / "capsules" / disp_name
                cap_dir.mkdir(parents=True, exist_ok=True)
                (cap_dir / "evidence").mkdir(exist_ok=True)

                # capsule.json
                (cap_dir / "capsule.json").write_text(capsule.model_dump_json(indent=2), encoding="utf-8")
                # capsule.schema.json
                (cap_dir / "capsule.schema.json").write_text(json.dumps(get_capsule_json_schema(), indent=2), encoding="utf-8")
                # capsule.md
                (cap_dir / "capsule.md").write_text(render_capsule_markdown(capsule), encoding="utf-8")
                # capsule.html
                (cap_dir / "capsule.html").write_text(render_capsule_html(capsule), encoding="utf-8")

                # Write MANIFEST.sha256 and reproduce scripts
                write_manifest_and_scripts(cap_dir, capsule)

                all_capsules.append(capsule)
                progress.advance(main_task)

        # Write top-level index.html and index.json
        (out_path / "index.json").write_text(
            json.dumps([c.model_dump() for c in all_capsules], indent=2),
            encoding="utf-8",
        )
        (out_path / "index.html").write_text(
            render_index_html(all_capsules, repo_info.source_url_or_path),
            encoding="utf-8",
        )

        console.print(f"\n[bold green]✓ Pipeline completed successfully![/bold green]")
        console.print(f"Generated [bold]{len(all_capsules)}[/bold] Dependency Exit Capsules in [cyan]{out_path.resolve()}[/cyan]")
        console.print(f"Browse results via: [cyan]{out_path.resolve() / 'index.html'}[/cyan]\n")

        # Summary Table
        summary_table = Table(title="Exitwise Run Summary", header_style="bold cyan")
        summary_table.add_column("Dependency", style="bold")
        summary_table.add_column("Proposed Replacement")
        summary_table.add_column("Overall Verdict")
        summary_table.add_column("Trust Distribution")

        for c in all_capsules:
            ts = c.provenance_summary
            rep_name = c.proposed_replacement.name if c.proposed_replacement else "None (Monitor)"
            v_style = {
                "READY": "green",
                "READY WITH GAPS": "yellow",
                "BLOCKED": "red",
                "NOT EXECUTED": "dim",
            }.get(c.overall_verdict, "white")

            summary_table.add_row(
                c.dependency.name,
                rep_name,
                f"[{v_style}]{c.overall_verdict}[/{v_style}]",
                f"{ts.observed_count} obs · {ts.verified_by_execution_count} exec · {ts.ai_generated_count} ai",
            )

        console.print(summary_table)


@cli.command()
@click.argument("capsule_dir")
def verify(capsule_dir: str):
    """Verify SHA-256 manifest integrity and reproduce test execution for a capsule."""
    c_path = Path(capsule_dir)
    console.print(f"[bold cyan]Verifying capsule integrity in {c_path}...[/bold cyan]")
    is_ok, issues = verify_capsule_directory(c_path)
    if is_ok:
        console.print("[bold green]✓ Capsule verified successfully! Hashes match and results are reproducible.[/bold green]")
    else:
        console.print("[bold red]✗ Capsule drift or integrity issues detected:[/bold red]")
        for iss in issues:
            console.print(f"  • {iss}")
        sys.exit(4)


@cli.command()
@click.option("--port", default=8000, help="Web dashboard server port")
@click.option("--dir", "out_dir", default=str(DEFAULT_OUTPUT_DIR), help="Capsule output directory")
def dashboard(port: int, out_dir: str):
    """Start local web dashboard server for live stage progress and capsule browsing."""
    try:
        from exitwise.web.server import start_dashboard
        start_dashboard(port=port, capsule_dir=Path(out_dir))
    except Exception as e:
        console.print(f"[bold red]Failed to start web server:[/bold red] {e}")


def main():
    cli()


if __name__ == "__main__":
    main()
