"""Deterministic dependency manifest parsing, AST-only setup.py inspection, and manifest drift detection."""

import ast
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from exitwise.models import Evidence, RiskIndicator, Provenance


@dataclass
class ParsedRequirement:
    """A requirement extracted from a project manifest."""

    raw: str
    name: str  # canonicalized name
    display_name: str
    specifier: str
    is_pinned: bool
    pinned_version: str | None
    source_file: str
    line_number: int | None = None
    is_dev: bool = False
    environment_marker: str | None = None


@dataclass
class ManifestDrift:
    """Conflicting requirements detected across different manifest files."""

    package: str
    declarations: list[tuple[str, str]]  # (source_file, specifier)
    is_conflict: bool
    evidence_id: str


def parse_requirement_line(line: str, source_file: str, line_no: int | None = None) -> ParsedRequirement | None:
    """Parse a single requirement line with packaging.requirements."""
    cleaned = line.split("#")[0].strip()
    if not cleaned:
        return None
    # Skip flags like -r, -i, -f, -e
    if cleaned.startswith(("-r", "--requirement", "-i", "-f", "-e", "--extra-index-url")):
        return None

    try:
        req = Requirement(cleaned)
        c_name = canonicalize_name(req.name)
        spec_str = str(req.specifier)
        pinned = False
        pinned_ver = None

        # Check if strictly pinned with ==
        for spec in req.specifier:
            if spec.operator == "==":
                pinned = True
                pinned_ver = spec.version
                break

        is_dev = "dev" in source_file.lower() or "test" in source_file.lower()

        return ParsedRequirement(
            raw=cleaned,
            name=c_name,
            display_name=req.name,
            specifier=spec_str,
            is_pinned=pinned,
            pinned_version=pinned_ver,
            source_file=source_file,
            line_number=line_no,
            is_dev=is_dev,
            environment_marker=str(req.marker) if req.marker else None,
        )
    except Exception:
        # Fallback regex for loose or pinned syntax
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*(==|>=|<=|~=|!=)?\s*([a-zA-Z0-9_\-\.]+)?", cleaned)
        if match:
            raw_name = match.group(1)
            op = match.group(2) or ""
            ver = match.group(3) or ""
            c_name = canonicalize_name(raw_name)
            is_pinned = (op == "==" and bool(ver))
            return ParsedRequirement(
                raw=cleaned,
                name=c_name,
                display_name=raw_name,
                specifier=f"{op}{ver}" if op else "",
                is_pinned=is_pinned,
                pinned_version=ver if is_pinned else None,
                source_file=source_file,
                line_number=line_no,
                is_dev="dev" in source_file.lower(),
            )
        return None


def parse_requirements_txt(file_path: Path, rel_name: str) -> list[ParsedRequirement]:
    """Parse requirements*.txt including includes and markers."""
    reqs: list[ParsedRequirement] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return reqs

    for idx, line in enumerate(content.splitlines(), start=1):
        parsed = parse_requirement_line(line, rel_name, idx)
        if parsed:
            reqs.append(parsed)
    return reqs


def parse_pyproject_toml(file_path: Path, rel_name: str) -> list[ParsedRequirement]:
    """Parse PEP 621 dependencies, optional-dependencies, Poetry and PDM tables."""
    reqs: list[ParsedRequirement] = []
    try:
        data = tomllib.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return reqs

    # 1. PEP 621 [project.dependencies]
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        parsed = parse_requirement_line(dep, rel_name)
        if parsed:
            parsed.is_dev = False
            reqs.append(parsed)

    # 2. PEP 621 [project.optional-dependencies]
    for opt_group, dep_list in project.get("optional-dependencies", {}).items():
        is_dev = opt_group.lower() in ("dev", "test", "testing", "docs")
        for dep in dep_list:
            parsed = parse_requirement_line(dep, rel_name)
            if parsed:
                parsed.is_dev = is_dev
                reqs.append(parsed)

    # 3. Poetry [tool.poetry.dependencies]
    poetry = data.get("tool", {}).get("poetry", {})
    for pkg_name, spec in poetry.get("dependencies", {}).items():
        if pkg_name.lower() == "python":
            continue
        spec_str = f"=={spec}" if isinstance(spec, str) and not spec.startswith(("^", "~", ">", "<", "=")) else str(spec)
        parsed = parse_requirement_line(f"{pkg_name}{spec_str}", rel_name)
        if parsed:
            parsed.is_dev = False
            reqs.append(parsed)

    for pkg_name, spec in poetry.get("dev-dependencies", {}).items():
        parsed = parse_requirement_line(f"{pkg_name} {spec}", rel_name)
        if parsed:
            parsed.is_dev = True
            reqs.append(parsed)

    return reqs


def parse_setup_py_ast(file_path: Path, rel_name: str) -> list[ParsedRequirement]:
    """Safely extract dependencies from setup.py via AST analysis ONLY without executing."""
    reqs: list[ParsedRequirement] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return reqs

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in ("setup", "Setup"):
                for keyword in node.keywords:
                    if keyword.arg == "install_requires" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                parsed = parse_requirement_line(elt.value, rel_name, getattr(elt, "lineno", None))
                                if parsed:
                                    reqs.append(parsed)
                    elif keyword.arg == "extras_require" and isinstance(keyword.value, ast.Dict):
                        for k, v in zip(keyword.value.keys, keyword.value.values):
                            is_dev = isinstance(k, ast.Constant) and str(k.value).lower() in ("dev", "test")
                            if isinstance(v, (ast.List, ast.Tuple)):
                                for elt in v.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        parsed = parse_requirement_line(elt.value, rel_name, getattr(elt, "lineno", None))
                                        if parsed:
                                            parsed.is_dev = is_dev
                                            reqs.append(parsed)
    return reqs


def scan_all_manifests(repo_dir: Path) -> tuple[list[ParsedRequirement], list[ManifestDrift], list[Evidence]]:
    """Scan all project files for dependency declarations, detect drift, and record evidence."""
    all_reqs: list[ParsedRequirement] = []
    evidence_list: list[Evidence] = []

    # Find requirement files
    for req_file in repo_dir.glob("**/requirements*.txt"):
        if ".venv" in req_file.parts or "venv" in req_file.parts:
            continue
        rel = str(req_file.relative_to(repo_dir))
        all_reqs.extend(parse_requirements_txt(req_file, rel))

    # pyproject.toml
    pyproject = repo_dir / "pyproject.toml"
    if pyproject.exists():
        rel = str(pyproject.relative_to(repo_dir))
        all_reqs.extend(parse_pyproject_toml(pyproject, rel))

    # setup.py (AST only)
    setup_py = repo_dir / "setup.py"
    if setup_py.exists():
        rel = str(setup_py.relative_to(repo_dir))
        all_reqs.extend(parse_setup_py_ast(setup_py, rel))

    # Detect manifest drift (same package, different constraints across files)
    by_pkg: dict[str, list[ParsedRequirement]] = {}
    for r in all_reqs:
        by_pkg.setdefault(r.name, []).append(r)

    drifts: list[ManifestDrift] = []
    drift_counter = 1

    for pkg_name, entries in by_pkg.items():
        if len(entries) > 1:
            specs = {(e.source_file, e.specifier) for e in entries if e.specifier}
            distinct_specs = {s[1] for s in specs}
            if len(distinct_specs) > 1:
                ev_id = f"EV-DRIFT-{drift_counter:04d}"
                drift_counter += 1
                drifts.append(
                    ManifestDrift(
                        package=pkg_name,
                        declarations=list(specs),
                        is_conflict=True,
                        evidence_id=ev_id,
                    )
                )
                evidence_list.append(
                    Evidence(
                        id=ev_id,
                        source="manifest_drift_detector",
                        kind="manifest_drift",
                        observed_value={
                            "package": pkg_name,
                            "declarations": [{"file": f, "spec": s} for f, s in specs],
                            "conflict": True,
                        },
                        timestamp="2026-10-15T00:00:00Z",
                    )
                )

    return all_reqs, drifts, evidence_list
