#!/usr/bin/env bash
# publish.sh — Baut und publiziert alle nl2cad Sub-Packages auf PyPI.
# Token wird sicher via Umgebungsvariable oder interaktiver Eingabe gelesen.
# Niemals Token als CLI-Argument übergeben (Shell-History).
set -euo pipefail

PACKAGES=(nl2cad-core nl2cad-areas nl2cad-brandschutz nl2cad-gaeb nl2cad-nlp)

# Token aus Umgebung oder interaktiv lesen
if [ -z "${PYPI_TOKEN:-}" ]; then
    read -r -s -p "PyPI API Token (pypi-...): " PYPI_TOKEN
    echo
fi

if [ -z "$PYPI_TOKEN" ]; then
    echo "ERROR: Kein Token angegeben." >&2
    exit 1
fi

# dist/ leeren um alte Builds zu vermeiden
rm -rf dist/
mkdir -p dist/

for pkg in "${PACKAGES[@]}"; do
    echo "\n=== Build: $pkg ==="
    uv build --package "$pkg"
done

echo "\n=== Publish: alle Packages ==="
uv publish dist/* --token "$PYPI_TOKEN"

echo "\nFertig. Packages publiziert:"
for pkg in "${PACKAGES[@]}"; do
    echo "  https://pypi.org/project/$pkg/"
done
