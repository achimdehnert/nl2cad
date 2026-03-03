#!/usr/bin/env bash
# Diagnostics + Tests mit uv-venv (.venv) direkt
set -e

cd "$(dirname "$0")"

echo "=== Suche ifcopenshell ==="
find .venv /home/dehnert -name "ifcopenshell" -type d 2>/dev/null | head -5 || true
find .venv -name "ifcopenshell*.so" 2>/dev/null | head -5 || true

echo "=== uv-venv Python ==="
.venv/bin/python -c "import sys; print(sys.version, sys.executable)"
.venv/bin/python -c "import ifcopenshell; print('ifcopenshell in .venv:', ifcopenshell.version)" 2>&1 || echo "FEHLER: ifcopenshell nicht in .venv"

echo "=== ifcopenshell direkt installieren in .venv ==="
.venv/bin/pip install -q ifcopenshell

echo "=== Nochmal pruefen ==="
.venv/bin/python -c "import ifcopenshell; print('OK:', ifcopenshell.version)"

echo "=== Starte Tests ==="
.venv/bin/pytest \
    --cov=packages \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v 2>&1 | tee test_results.txt

echo "=== Fertig ==="
tail -5 test_results.txt
