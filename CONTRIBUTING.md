# Contributing to nl2cad

## Setup

```bash
git clone https://github.com/achimdehnert/nl2cad.git
cd nl2cad

# uv installieren
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alle Packages als Editable installieren
uv sync --all-packages
```

## Development Workflow

```bash
# Tests laufen lassen
uv run pytest

# Nur ein Package testen
uv run pytest packages/nl2cad-areas/

# Linting
uv run ruff check packages/
uv run ruff format packages/

# Typ-Checks
uv run mypy packages/ --ignore-missing-imports
```

## Package hinzufügen

1. Verzeichnis `packages/nl2cad-<name>/` anlegen
2. `pyproject.toml` nach Muster der anderen Packages
3. `src/nl2cad/<name>/__init__.py` mit Public API
4. Tests in `packages/nl2cad-<name>/tests/`
5. Eintrag in Root-`README.md`
6. Eintrag in `CHANGELOG.md`

## Coding-Konventionen

Lies [AGENTS.md](AGENTS.md) — gilt für Menschen und Coding Agents gleichermaßen.

## Release

```bash
# Tag setzen (löst PyPI-Publish aus)
git tag nl2cad-core@0.2.0
git push --tags
```
