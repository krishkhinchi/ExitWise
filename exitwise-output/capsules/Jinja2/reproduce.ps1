# Exitwise Reproduction Script for Windows PowerShell
Write-Host "=== Reproducing test verification for Jinja2 ===" -ForegroundColor Cyan
Write-Host "Running baseline suite on Python 3.13..." -ForegroundColor Green
C:\Program Files\Python313\python.exe -m pytest
Write-Host "Running candidate suite on Python 3.13..." -ForegroundColor Green
C:\Program Files\Python313\python.exe -m pytest
