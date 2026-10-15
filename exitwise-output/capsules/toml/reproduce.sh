#!/usr/bin/env bash
# Exitwise Reproduction Script
set -euo pipefail

echo "=== Reproducing test verification for toml ==="
echo "Running baseline suite on Python 3.13..."
C:\Program Files\Python313\python.exe -m pytest
echo "Running candidate suite on Python 3.13..."
C:\Program Files\Python313\python.exe -m pytest
