"""Python 3.12 and 3.13 compatibility evaluation."""

import datetime
from dataclasses import dataclass
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from exitwise.models import Evidence


@dataclass
class PythonCompatResult:
    """Evaluation of package compatibility with Python 3.12 and 3.13."""

    compatible_312: bool = True
    compatible_313: bool = True
    incompat_reason: str | None = None
    tested_via: str = "specifiers_and_classifiers"  # or smoke_test
    evidence_id: str = ""


# Known legacy packages broken on Python >=3.12 due to removed stdlib modules (e.g. imp)
KNOWN_BROKEN_ON_312_PLUS = {
    "nose": "nose relies on the 'imp' module removed in Python 3.12 and fails to import/run.",
}


def evaluate_python_compatibility(
    package_name: str,
    requires_python: str | None,
    classifiers: list[str],
    evidence_counter: int = 1,
) -> tuple[PythonCompatResult, Evidence]:
    """Check whether a package supports Python 3.12 and 3.13."""
    ev_id = f"EV-COMPAT-{evidence_counter:04d}"
    compat_312 = True
    compat_313 = True
    reason = None

    # Check known broken packages
    canonical = package_name.lower().replace("-", "_")
    if canonical in KNOWN_BROKEN_ON_312_PLUS:
        compat_312 = False
        compat_313 = False
        reason = KNOWN_BROKEN_ON_312_PLUS[canonical]

    # Check requires_python specifier
    if requires_python and (compat_312 or compat_313):
        try:
            spec = SpecifierSet(requires_python)
            v312 = Version("3.12.0")
            v313 = Version("3.13.0")

            if v312 not in spec:
                compat_312 = False
                reason = f"requires-python '{requires_python}' excludes Python 3.12"
            if v313 not in spec:
                compat_313 = False
                reason = f"requires-python '{requires_python}' excludes Python 3.13"
        except Exception:
            pass

    # Check classifiers if no specific python 3 classifier exists
    py3_classifiers = [c for c in classifiers if "Programming Language :: Python :: 3" in c]
    has_312_classifier = any("3.12" in c for c in py3_classifiers)
    has_313_classifier = any("3.13" in c for c in py3_classifiers)

    ev = Evidence(
        id=ev_id,
        source="python_compat_evaluator",
        kind="python_version_support",
        observed_value={
            "package": package_name,
            "compatible_312": compat_312,
            "compatible_313": compat_313,
            "incompat_reason": reason,
            "has_312_classifier": has_312_classifier,
            "has_313_classifier": has_313_classifier,
            "requires_python": requires_python,
        },
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    result = PythonCompatResult(
        compatible_312=compat_312,
        compatible_313=compat_313,
        incompat_reason=reason,
        evidence_id=ev_id,
    )
    return result, ev
