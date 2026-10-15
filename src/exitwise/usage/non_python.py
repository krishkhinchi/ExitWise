"""Scan non-Python files (templates, configuration files, Dockerfile, Makefile) for dependency references."""

import re
from pathlib import Path
from exitwise.models import UsageLocation, Provenance
from exitwise.usage.ast_scanner import extract_snippet


def scan_non_python_references(repo_dir: Path, dist_name: str) -> list[UsageLocation]:
    """Search Jinja templates, TOML files, Dockerfiles, and Makefiles for dependency mentions."""
    locations: list[UsageLocation] = []
    patterns = ["*.j2", "*.jinja", "*.toml", "Dockerfile*", "Makefile*"]
    names_to_search = [dist_name, dist_name.replace("-", "_")]

    for pat in patterns:
        for file_path in repo_dir.rglob(pat):
            if any(part in file_path.parts for part in (".venv", "venv", ".git", "exitwise-output")):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                rel_path = str(file_path.relative_to(repo_dir)).replace("\\", "/")
                for idx, line in enumerate(content.splitlines(), start=1):
                    for name in names_to_search:
                        if re.search(rf"\b{re.escape(name)}\b", line, re.IGNORECASE):
                            locations.append(
                                UsageLocation(
                                    file=rel_path,
                                    line=idx,
                                    col=0,
                                    symbol=name,
                                    kind="template_or_config_ref",
                                    snippet=extract_snippet(file_path, idx),
                                    context="config_or_template",
                                    provenance=Provenance.OBSERVED,
                                )
                            )
                            break
            except Exception:
                continue

    return locations
