"""Mapping between Python top-level import names and PyPI distribution names."""

import sys
from importlib.metadata import packages_distributions
from packaging.utils import canonicalize_name

# Static fallback map for popular packages where import name != PyPI package name
COMMON_IMPORT_TO_DIST: dict[str, str] = {
    "dateutil": "python-dateutil",
    "yaml": "pyyaml",
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "google.genai": "google-genai",
    "genai": "google-genai",
    "jose": "python-jose",
    "magic": "python-magic",
    "serial": "pyserial",
    "jwt": "pyjwt",
    "websocket": "websocket-client",
    "crypto": "pycryptodome",
    "Crypto": "pycryptodome",
    "OpenSSL": "pyopenssl",
    "git": "gitpython",
}

# Inverted mapping: PyPI dist name -> set of known import package names
COMMON_DIST_TO_IMPORT: dict[str, set[str]] = {
    "python-dateutil": {"dateutil"},
    "pyyaml": {"yaml"},
    "pillow": {"PIL"},
    "beautifulsoup4": {"bs4"},
    "jinja2": {"jinja2", "Jinja2"},
    "google-genai": {"google.genai", "genai"},
    "setuptools": {"setuptools", "pkg_resources", "distutils"},
}


_IMPORT_TO_DIST_CACHE: dict[str, list[str]] | None = None


def get_import_to_dist_map() -> dict[str, list[str]]:
    """Return top-level import name to distribution name mappings (cached)."""
    global _IMPORT_TO_DIST_CACHE
    if _IMPORT_TO_DIST_CACHE is None:
        try:
            _IMPORT_TO_DIST_CACHE = packages_distributions()
        except Exception:
            _IMPORT_TO_DIST_CACHE = {}
    return _IMPORT_TO_DIST_CACHE


def normalize_distribution_name(import_or_dist_name: str) -> str:
    """Normalize import or distribution name to standard PyPI canonical name."""
    lowered = import_or_dist_name.strip()
    if lowered in COMMON_IMPORT_TO_DIST:
        return canonicalize_name(COMMON_IMPORT_TO_DIST[lowered])

    # Check packages_distributions
    pkgs = get_import_to_dist_map()
    if lowered in pkgs and pkgs[lowered]:
        return canonicalize_name(pkgs[lowered][0])

    return canonicalize_name(lowered)


def get_import_names_for_dist(dist_name: str) -> set[str]:
    """Get candidate Python import module names for a given PyPI distribution."""
    canonical = canonicalize_name(dist_name)
    names = {canonical, canonical.replace("-", "_"), dist_name}

    if canonical in COMMON_DIST_TO_IMPORT:
        names.update(COMMON_DIST_TO_IMPORT[canonical])

    # Check reversed packages_distributions
    pkgs = get_import_to_dist_map()
    for imp_name, dist_list in pkgs.items():
        for d in dist_list:
            if canonicalize_name(d) == canonical:
                names.add(imp_name)

    return names
