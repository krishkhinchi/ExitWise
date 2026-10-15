"""Scan non-Python files (templates, configuration files, Dockerfile, Makefile) for dependency references."""

import re
from pathlib import Path
from exitwise.models import UsageLocation, Provenance
from exitwise.usage.ast_scanner import extract_snippet

_SKIP_PARTS = {".venv", "venv", ".git", "exitwise-output"}
_NON_PY_PATTERNS = ["*.j2", "*.jinja", "*.toml", "Dockerfile*", "Makefile*"]

# Cache: repo_dir -> list of (file_path, rel_path, lines)
_NON_PY_CACHE: dict[Path, list[tuple[Path, str, list[str]]]] = {}


def _get_non_python_files(repo_dir: Path) -> list[tuple[Path, str, list[str]]]:
    """Walk and read all non-Python config/template files once per repo."""
    if repo_dir in _NON_PY_CACHE:
        return _NON_PY_CACHE[repo_dir]

    result: list[tuple[Path, str, list[str]]] = []
    for pat in _NON_PY_PATTERNS:
        for file_path in repo_dir.rglob(pat):
            if any(part in _SKIP_PARTS for part in file_path.parts):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                rel_path = str(file_path.relative_to(repo_dir)).replace("\\", "/")
                result.append((file_path, rel_path, content.splitlines()))
            except Exception:
                continue

    _NON_PY_CACHE[repo_dir] = result
    return result


def scan_non_python_references(repo_dir: Path, dist_name: str) -> list[UsageLocation]:
    """Search Jinja templates, TOML files, Dockerfiles, and Makefiles for dependency mentions."""
    locations: list[UsageLocation] = []
    names_to_search = [dist_name, dist_name.replace("-", "_")]
    patterns = [re.compile(rf"\b{re.escape(n)}\b", re.IGNORECASE) for n in names_to_search]

    for file_path, rel_path, lines in _get_non_python_files(repo_dir):
        for idx, line in enumerate(lines, start=1):
            for i, pat in enumerate(patterns):
                if pat.search(line):
                    locations.append(
                        UsageLocation(
                            file=rel_path,
                            line=idx,
                            col=0,
                            symbol=names_to_search[i],
                            kind="template_or_config_ref",
                            snippet=extract_snippet(file_path, idx, _lines_cache=lines),
                            context="config_or_template",
                            provenance=Provenance.OBSERVED,
                        )
                    )
                    break

    return locations
