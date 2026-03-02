---
description: Neues nl2cad-* Package anlegen — vollständiges Template
---

# Neues nl2cad-Package anlegen

## Eingabe benötigt

Bevor du startest, frage: **Wie soll das neue Package heißen?**
Format: `nl2cad-<name>` (z.B. `nl2cad-viewer`, `nl2cad-report`)

Setze im folgenden `<name>` überall auf den gewählten Namen.

## Schritt 1 — Verzeichnisstruktur anlegen

```bash
mkdir -p packages/nl2cad-<name>/src/nl2cad/<name>
mkdir -p packages/nl2cad-<name>/tests
```

## Schritt 2 — pyproject.toml anlegen

**Zieldatei:** `packages/nl2cad-<name>/pyproject.toml`

Vorlage (anpassen!):
```toml
[project]
name = "nl2cad-<name>"
version = "0.1.0"
description = "BESCHREIBUNG des Packages"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Achim Dehnert", email = "achim@dehnert.com" }]
keywords = ["bim", "cad", "nl2cad", "WEITERE-KEYWORDS"]

dependencies = [
    "nl2cad-core>=0.1.0",
    # Weitere Dependencies — nur was wirklich nötig ist
    # KEIN Django, KEIN httpx (außer für nlp-ähnliche Packages)
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4", "mypy>=1.10"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/nl2cad"]   # Namespace — NICHT ändern
```

## Schritt 3 — __init__.py mit Public API

**Zieldatei:** `packages/nl2cad-<name>/src/nl2cad/<name>/__init__.py`

```python
"""
nl2cad-<name> — KURZBESCHREIBUNG.

Usage:
    from nl2cad.<name>.main_class import MainClass
"""

__version__ = "0.1.0"

# Alle Public-API-Klassen hier importieren:
# from nl2cad.<name>.xyz import XYZ
# __all__ = ["XYZ"]
```

## Schritt 4 — Erste Klasse implementieren

Erstelle die Hauptklasse des Packages.
Halte dich an AGENTS.md:
- Dataclasses für Daten
- Logging statt print()
- Einheits-Suffix bei Maßfeldern
- Kein Django

## Schritt 5 — Tests anlegen

**Zieldatei:** `packages/nl2cad-<name>/tests/test_<name>.py`

Mindestens 5 sinnvolle Tests bevor das Package als "done" gilt.

```python
"""Tests für nl2cad-<name>."""
import pytest
# from nl2cad.<name>.xyz import XYZ

class Test<Name>:

    def test_basic_usage(self):
        ...

    def test_edge_case(self):
        ...
```

## Schritt 6 — README.md

**Zieldatei:** `packages/nl2cad-<name>/README.md`

```markdown
# nl2cad-<name>

KURZBESCHREIBUNG.

## Installation

\`\`\`bash
pip install nl2cad-<name>
\`\`\`

## Usage

\`\`\`python
from nl2cad.<name> import MainClass
\`\`\`
```

## Schritt 7 — Integration prüfen

```bash
# Package in Workspace registrieren (passiert automatisch via uv workspace)
uv sync --all-packages

# Tests laufen lassen
uv run pytest packages/nl2cad-<name>/ -v

# Alle Tests (keine Regression)
uv run pytest -v

# Linting
uv run ruff check packages/nl2cad-<name>/
```

## Schritt 8 — Root-Dateien updaten

1. `README.md` (Root): Package in Tabelle eintragen
2. `CHANGELOG.md`: Unter `[Unreleased]` eintragen
3. `AGENTS.md`: Package-Grenzen-Tabelle erweitern

## Definition of Done

- [ ] `packages/nl2cad-<name>/` angelegt
- [ ] `pyproject.toml` korrekt (Name, Deps, keine unnötigen Deps)
- [ ] `__init__.py` mit Public API
- [ ] Mindestens 5 Tests grün
- [ ] `uv run pytest -v` → alle Tests grün (keine Regression)
- [ ] `README.md`, `CHANGELOG.md`, `AGENTS.md` aktualisiert
