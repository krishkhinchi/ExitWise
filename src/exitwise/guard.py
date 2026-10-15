"""Runtime Python version guard for Exitwise.

Strict constraint: Python >= 3.12, < 3.14.
Fails cleanly with exit code 2 if running on unsupported Python (e.g. 3.14 or < 3.12).
"""

import sys


def check_python_version() -> None:
    """Enforce runtime Python version >= 3.12 and < 3.14. Exits with code 2 on mismatch."""
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 12) or (major, minor) >= (3, 14):
        sys.stderr.write(
            f"ERROR [Exitwise Environment Guard]: Incompatible Python version {major}.{minor}.{sys.version_info.micro}.\n"
            f"Exitwise strictly supports Python 3.12 and 3.13 only. Python 3.14+ is NOT supported.\n"
        )
        sys.exit(2)
