"""Comprehensive AST scanner detecting imports, call sites, inheritance, type annotations, and dynamic patching."""

import ast
import linecache
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from packaging.utils import canonicalize_name

from exitwise.models import UsageLocation, Evidence, Provenance
from exitwise.usage.importmap import get_import_names_for_dist, normalize_distribution_name

STDLIB_MODULE_NAMES = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()


def extract_snippet(
    file_path: Path,
    line_number: int,
    context_lines: int = 3,
    _lines_cache: list[str] | None = None,
) -> str:
    """Extract code snippet centered at line_number with surrounding context."""
    try:
        lines = _lines_cache if _lines_cache is not None else file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        snippet_lines = []
        for idx in range(start, end):
            curr_lineno = idx + 1
            marker = " >" if curr_lineno == line_number else "  "
            snippet_lines.append(f"{marker} {curr_lineno:4d} | {lines[idx]}")
        return "\n".join(snippet_lines)
    except Exception:
        return f"Line {line_number}"


class RepoASTVisitor(ast.NodeVisitor):
    """AST Visitor that tracks module aliases, usage sites, and dynamic patching."""

    def __init__(self, file_path: Path, rel_path: str, target_import_names: set[str], lines_cache: list[str] | None = None):
        self.file_path = file_path
        self.rel_path = rel_path
        self.target_names = {name.lower() for name in target_import_names}
        self.locations: list[UsageLocation] = []
        self._lines = lines_cache

        # Local alias tracking within the file
        # alias -> root module name (e.g. 'req' -> 'requests')
        self.module_aliases: dict[str, str] = {}
        # imported symbol alias -> (root module, qualified symbol) (e.g. 'S' -> ('requests', 'Session'))
        self.symbol_aliases: dict[str, tuple[str, str]] = {}

        self.context = "test" if "test" in rel_path.lower() else "runtime"

    def _matches_target(self, root_name: str) -> bool:
        return root_name.lower() in self.target_names

    def _snippet(self, lineno: int) -> str:
        return extract_snippet(self.file_path, lineno, _lines_cache=self._lines)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if self._matches_target(root):
                as_name = alias.asname or alias.name
                self.module_aliases[as_name] = root
                self.locations.append(
                    UsageLocation(
                        file=self.rel_path,
                        line=node.lineno,
                        col=node.col_offset,
                        symbol=alias.name,
                        kind="import",
                        snippet=self._snippet(node.lineno),
                        context=self.context,
                        provenance=Provenance.OBSERVED,
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root = node.module.split(".")[0]
            if self._matches_target(root):
                for alias in node.names:
                    as_name = alias.asname or alias.name
                    full_symbol = f"{node.module}.{alias.name}"
                    self.symbol_aliases[as_name] = (root, full_symbol)
                    self.locations.append(
                        UsageLocation(
                            file=self.rel_path,
                            line=node.lineno,
                            col=node.col_offset,
                            symbol=full_symbol,
                            kind="import_from",
                            snippet=self._snippet(node.lineno),
                            context=self.context,
                            provenance=Provenance.OBSERVED,
                        )
                    )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect dynamic patching: e.g. requests.Session.request = _request."""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                chain = self._resolve_attribute_chain(target)
                if chain:
                    root_name = chain[0]
                    if root_name in self.module_aliases and self._matches_target(self.module_aliases[root_name]):
                        self.locations.append(UsageLocation(
                            file=self.rel_path, line=node.lineno, col=node.col_offset,
                            symbol=".".join(chain), kind="patch",
                            snippet=self._snippet(node.lineno), context="patching",
                            provenance=Provenance.OBSERVED,
                        ))
                    elif root_name in self.symbol_aliases:
                        root, full_sym = self.symbol_aliases[root_name]
                        if self._matches_target(root):
                            self.locations.append(UsageLocation(
                                file=self.rel_path, line=node.lineno, col=node.col_offset,
                                symbol=f"{full_sym}.{'.'.join(chain[1:])}", kind="patch",
                                snippet=self._snippet(node.lineno), context="patching",
                                provenance=Provenance.OBSERVED,
                            ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect direct function calls on target symbols or modules."""
        chain = self._resolve_attribute_chain(node.func)
        if chain:
            root_name = chain[0]
            if root_name in self.module_aliases and self._matches_target(self.module_aliases[root_name]):
                self.locations.append(UsageLocation(
                    file=self.rel_path, line=node.lineno, col=node.col_offset,
                    symbol=".".join(chain), kind="call",
                    snippet=self._snippet(node.lineno), context=self.context,
                    provenance=Provenance.OBSERVED,
                ))
            elif root_name in self.symbol_aliases:
                root, full_sym = self.symbol_aliases[root_name]
                if self._matches_target(root):
                    self.locations.append(UsageLocation(
                        file=self.rel_path, line=node.lineno, col=node.col_offset,
                        symbol=full_sym, kind="call",
                        snippet=self._snippet(node.lineno), context=self.context,
                        provenance=Provenance.OBSERVED,
                    ))
        elif isinstance(node.func, ast.Name) and node.func.id in self.symbol_aliases:
            root, full_sym = self.symbol_aliases[node.func.id]
            if self._matches_target(root):
                self.locations.append(UsageLocation(
                    file=self.rel_path, line=node.lineno, col=node.col_offset,
                    symbol=full_sym, kind="call",
                    snippet=self._snippet(node.lineno), context=self.context,
                    provenance=Provenance.OBSERVED,
                ))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Detect class inheritance from dependency classes (e.g. BaseModel)."""
        for base in node.bases:
            chain = self._resolve_attribute_chain(base)
            if chain:
                root_name = chain[0]
                if root_name in self.module_aliases and self._matches_target(self.module_aliases[root_name]):
                    self.locations.append(UsageLocation(
                        file=self.rel_path, line=node.lineno, col=node.col_offset,
                        symbol=f"class {node.name}({'.'.join(chain)})", kind="inheritance",
                        snippet=self._snippet(node.lineno), context=self.context,
                        provenance=Provenance.OBSERVED,
                    ))
                elif root_name in self.symbol_aliases:
                    root, full_sym = self.symbol_aliases[root_name]
                    if self._matches_target(root):
                        self.locations.append(UsageLocation(
                            file=self.rel_path, line=node.lineno, col=node.col_offset,
                            symbol=f"class {node.name}({full_sym})", kind="inheritance",
                            snippet=self._snippet(node.lineno), context=self.context,
                            provenance=Provenance.OBSERVED,
                        ))
            elif isinstance(base, ast.Name) and base.id in self.symbol_aliases:
                root, full_sym = self.symbol_aliases[base.id]
                if self._matches_target(root):
                    self.locations.append(UsageLocation(
                        file=self.rel_path, line=node.lineno, col=node.col_offset,
                        symbol=f"class {node.name}({full_sym})", kind="inheritance",
                        snippet=self._snippet(node.lineno), context=self.context,
                        provenance=Provenance.OBSERVED,
                    ))
        self.generic_visit(node)

    def _resolve_attribute_chain(self, node: ast.AST) -> list[str] | None:
        """Resolve a.b.c attribute access sequence."""
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
            parts.reverse()
            return parts
        return None


_SKIP_PARTS = {".venv", "venv", "__pycache__", ".git", "exitwise-output"}

# Pre-parsed repo cache: repo_dir -> list of (py_file, rel_path, lines, tree)
_REPO_AST_CACHE: dict[Path, list[tuple[Path, str, list[str], ast.AST]]] = {}


def _get_repo_parsed_files(repo_dir: Path) -> list[tuple[Path, str, list[str], ast.AST]]:
    """Parse all Python files in repo once and cache the result."""
    if repo_dir in _REPO_AST_CACHE:
        return _REPO_AST_CACHE[repo_dir]

    parsed: list[tuple[Path, str, list[str], ast.AST]] = []
    for py_file in repo_dir.rglob("*.py"):
        if any(part in _SKIP_PARTS for part in py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            tree = ast.parse(content, filename=str(py_file))
            rel_path = str(py_file.relative_to(repo_dir)).replace("\\", "/")
            parsed.append((py_file, rel_path, lines, tree))
        except Exception:
            continue

    _REPO_AST_CACHE[repo_dir] = parsed
    return parsed


def scan_repo_usage_for_dependency(
    repo_dir: Path,
    dist_name: str,
    evidence_counter: int = 1,
) -> tuple[list[UsageLocation], Evidence]:
    """Scan all Python files in the repo for references to a given dependency distribution."""
    target_names = get_import_names_for_dist(dist_name)
    all_locations: list[UsageLocation] = []

    for py_file, rel_path, lines, tree in _get_repo_parsed_files(repo_dir):
        try:
            visitor = RepoASTVisitor(py_file, rel_path, target_names, lines_cache=lines)
            visitor.visit(tree)
            all_locations.extend(visitor.locations)
        except Exception:
            continue

    ev_id = f"EV-AST-{evidence_counter:04d}"
    evidence = Evidence(
        id=ev_id,
        source="ast_scanner",
        kind="usage_mapping",
        observed_value={
            "dependency": dist_name,
            "target_import_names": list(target_names),
            "match_count": len(all_locations),
            "files": list({loc.file for loc in all_locations}),
            "has_dynamic_patch": any(loc.kind == "patch" for loc in all_locations),
        },
        timestamp="2026-10-15T00:00:00Z",
    )
    return all_locations, evidence


def find_undeclared_imports(repo_dir: Path, declared_distributions: set[str]) -> list[tuple[str, str, int]]:
    """Surface external packages imported in Python files that are not declared in manifests."""
    declared_canonical = {canonicalize_name(d) for d in declared_distributions}
    undeclared: list[tuple[str, str, int]] = []

    for py_file, rel_path, _lines, tree in _get_repo_parsed_files(repo_dir):
        try:
            for node in ast.walk(tree):
                root_pkg = None
                lineno = getattr(node, "lineno", 1)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_pkg = alias.name.split(".")[0]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    root_pkg = node.module.split(".")[0]

                if root_pkg and root_pkg not in STDLIB_MODULE_NAMES:
                    dist = normalize_distribution_name(root_pkg)
                    is_internal = (repo_dir / root_pkg).is_dir() or (repo_dir / f"{root_pkg}.py").is_file()
                    if not is_internal and dist not in declared_canonical:
                        undeclared.append((dist, rel_path, lineno))
        except Exception:
            continue

    return undeclared
