"""Live PyPI JSON API client with offline caching and metadata extraction."""

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import httpx
from packaging.version import Version, parse as parse_version

from exitwise.models import Evidence


@dataclass
class PyPIMetadata:
    """Structured PyPI metadata for a package."""

    name: str
    latest_version: str
    release_date: str | None = None
    days_since_last_release: int | None = None
    pinned_version_yanked: bool = False
    pinned_yanked_reason: str | None = None
    requires_python: str | None = None
    classifiers: list[str] = field(default_factory=list)
    is_deprecated_or_unmaintained: bool = False
    deprecation_notes: list[str] = field(default_factory=list)
    project_urls: dict[str, str] = field(default_factory=dict)
    all_versions: list[str] = field(default_factory=list)
    evidence_id: str = ""
    is_offline_cached: bool = False


# Local in-memory / disk cache
_CACHE_DIR = Path.home() / ".cache" / "exitwise" / "pypi"


def get_cached_pypi(package_name: str) -> dict[str, Any] | None:
    """Read cached PyPI response from disk if present."""
    cache_file = _CACHE_DIR / f"{package_name.lower()}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def set_cached_pypi(package_name: str, data: dict[str, Any]) -> None:
    """Save PyPI response to disk cache."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = _CACHE_DIR / f"{package_name.lower()}.json"
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def fetch_pypi_metadata(
    package_name: str,
    pinned_version: str | None = None,
    evidence_counter: int = 1,
    offline_mode: bool = False,
) -> tuple[PyPIMetadata, Evidence]:
    """Query live PyPI JSON API with offline caching and fallback."""
    raw_data: dict[str, Any] | None = None
    is_cached = False

    if not offline_mode:
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            resp = httpx.get(url, timeout=10.0, follow_redirects=True)
            if resp.status_code == 200:
                raw_data = resp.json()
                set_cached_pypi(package_name, raw_data)
        except Exception:
            raw_data = get_cached_pypi(package_name)
            is_cached = True
    else:
        raw_data = get_cached_pypi(package_name)
        is_cached = True

    if not raw_data:
        # Fallback offline metadata
        ev_id = f"EV-PYPI-{evidence_counter:04d}"
        ev = Evidence(
            id=ev_id,
            source="pypi_api",
            kind="metadata_unavailable",
            observed_value={"package": package_name, "status": "offline_or_not_found"},
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        return (
            PyPIMetadata(
                name=package_name,
                latest_version=pinned_version or "unknown",
                evidence_id=ev_id,
                is_offline_cached=True,
            ),
            ev,
        )

    info = raw_data.get("info", {})
    releases = raw_data.get("releases", {})
    latest_ver = info.get("version", "unknown")
    requires_python = info.get("requires_python")
    classifiers = info.get("classifiers", [])
    project_urls = info.get("project_urls") or {}

    # Check for deprecation keywords in summary, description or classifiers
    deprecation_notes: list[str] = []
    summary = (info.get("summary") or "").lower()
    description = (info.get("description") or "")[:2000].lower()

    if any("7 - inactive" in c.lower() for c in classifiers):
        deprecation_notes.append("Classifier: Development Status :: 7 - Inactive")

    unmaintained_terms = [
        "deprecated",
        "no longer maintained",
        "not maintained",
        "unmaintained",
        "archive",
        "end of life",
        "moved to",
    ]
    for term in unmaintained_terms:
        if term in summary or term in description:
            deprecation_notes.append(f"Description/Summary mentions '{term}'")
            break

    # Check release dates & yanked flag
    latest_release_date = None
    days_since = None
    pinned_yanked = False
    pinned_yank_reason = None

    # Check pinned release files for yanked
    if pinned_version and pinned_version in releases:
        pinned_files = releases[pinned_version]
        for f in pinned_files:
            if f.get("yanked", False):
                pinned_yanked = True
                pinned_yank_reason = f.get("yanked_reason") or "Yanked on PyPI"
                break

    # Determine latest release date
    if latest_ver in releases and releases[latest_ver]:
        upload_time_str = releases[latest_ver][0].get("upload_time_iso_8601")
        if upload_time_str:
            try:
                dt = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
                latest_release_date = dt.strftime("%Y-%m-%d")
                days_since = (datetime.datetime.now(datetime.timezone.utc) - dt).days
            except Exception:
                pass

    ev_id = f"EV-PYPI-{evidence_counter:04d}"
    evidence = Evidence(
        id=ev_id,
        source="pypi_api",
        kind="package_metadata",
        observed_value={
            "package": package_name,
            "latest_version": latest_ver,
            "pinned_version": pinned_version,
            "release_date": latest_release_date,
            "days_since_last_release": days_since,
            "pinned_version_yanked": pinned_yanked,
            "requires_python": requires_python,
            "classifiers": classifiers,
            "deprecation_notes": deprecation_notes,
        },
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    meta = PyPIMetadata(
        name=package_name,
        latest_version=latest_ver,
        release_date=latest_release_date,
        days_since_last_release=days_since,
        pinned_version_yanked=pinned_yanked,
        pinned_yanked_reason=pinned_yank_reason,
        requires_python=requires_python,
        classifiers=classifiers,
        is_deprecated_or_unmaintained=bool(deprecation_notes),
        deprecation_notes=deprecation_notes,
        project_urls=project_urls,
        all_versions=list(releases.keys()),
        evidence_id=ev_id,
        is_offline_cached=is_cached,
    )
    return meta, evidence
