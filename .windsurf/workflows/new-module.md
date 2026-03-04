---
description: Neues nl2cad-* Modul anlegen — ADR + Package-Skeleton + modules.json + Konfigurator-Eintrag
---

## Voraussetzungen

- `MODULE_ID` = Python-Identifier, lowercase, kein Bindestrich (z.B. `schallschutz`)
- `PACKAGE_NAME` = PyPI-Name mit Bindestrich (z.B. `nl2cad-schallschutz`)
- `ADR_NR` = nächste freie ADR-Nummer (z.B. `006`)
- Coding-Konventionen aus `AGENTS.md` gelten uneingeschränkt

---

## Schritt 1 — ADR anlegen

Erstelle `docs/adr/ADR-{ADR_NR}-{MODULE_ID}-package.md` nach diesem Template:

```markdown
# ADR-{ADR_NR}: {PACKAGE_NAME} — Scope, Pflicht-Use-Cases und Architektur

| Attribut      | Wert |
| ------------- | ---- |
| **Status**    | Draft |
| **Datum**     | {HEUTE} |
| **Autoren**   | Achim Dehnert |
| **Packages**  | `{PACKAGE_NAME}` (primary), `nl2cad-core` |
| **Verknüpft** | ADR-001 (Brandschutz/Basis), ... |

## 1. Kontext und Problemstellung
[Fachliche Begründung: warum dieses Modul, welche Norm, welche Zielgruppe]

## 2. Entscheidung
[3 Ausbaustufen Milestone 1/2/3]

## 3. Pflicht-Use-Cases (Milestone 1)

### UC-01: [Haupt-Use-Case]
**Norm:** [z.B. DIN 4109:2018]
**Eingabe:** `IFCModel`
**Ausgabe:**
```python
@dataclass
class [Result]:
    ...  # Feldnamen mit Einheit-Suffix: area_m2, height_m
    norm_version: str  # Pflicht: z.B. "DIN-4109-2018"
```
**Implementierungsort:** `nl2cad/{MODULE_ID}/[modul].py`

## 4. Architektur
### 4.1 Modulstruktur
```
packages/{PACKAGE_NAME}/src/nl2cad/{MODULE_ID}/
├── __init__.py
├── models.py
├── analyzer.py
├── constants.py
└── rules/
```

### 4.2 Abhängigkeits-Regel
```
{PACKAGE_NAME} darf IMPORTIEREN:
  nl2cad-core
  nl2cad-areas  (nur wenn Flächenbezug nötig)

{PACKAGE_NAME} darf NICHT importieren:
  pydantic, httpx, Django ORM, nl2cad-nlp
```

## 5. Abgelehnte Alternativen
[...]

## 6. Nicht-Ziele
[...]
```

---

## Schritt 2 — Package-Skeleton anlegen

// turbo
```bash
PACKAGE_NAME="nl2cad-schallschutz"  # ANPASSEN
MODULE_ID="schallschutz"            # ANPASSEN
PKG_DIR="packages/${PACKAGE_NAME}"

mkdir -p "${PKG_DIR}/src/nl2cad/${MODULE_ID}/rules"
mkdir -p "${PKG_DIR}/tests/fixtures"
```

Erstelle `packages/{PACKAGE_NAME}/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{PACKAGE_NAME}"
version = "0.1.0"
description = "[Kurzbeschreibung]"
requires-python = ">=3.11"
dependencies = [
    "nl2cad-core>=0.1.0",
    # "nl2cad-areas>=0.1.0",  # nur wenn nötig
]

[tool.hatch.build.targets.wheel]
packages = ["src/nl2cad"]
```

Erstelle `packages/{PACKAGE_NAME}/src/nl2cad/{MODULE_ID}/__init__.py`:
```python
"""
{PACKAGE_NAME} — [Kurzbeschreibung].

Downstream-Konsumenten: cad-hub (Django), Behörden-Portale.
ADR: docs/adr/ADR-{ADR_NR}-{MODULE_ID}-package.md
"""
from nl2cad.{MODULE_ID}.models import [HauptResult]
from nl2cad.{MODULE_ID}.analyzer import [HauptAnalyzer]

__all__ = ["[HauptResult]", "[HauptAnalyzer]"]
```

Erstelle `packages/{PACKAGE_NAME}/src/nl2cad/{MODULE_ID}/models.py`:
```python
"""Dataclasses für {PACKAGE_NAME}."""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class [HauptResult]:
    """[Beschreibung]."""
    norm_version: str = ""  # z.B. "DIN-XXXX-YYYY"
    # Feldnamen IMMER mit Einheit-Suffix: area_m2, height_m, etc.
```

Erstelle `packages/{PACKAGE_NAME}/src/nl2cad/{MODULE_ID}/constants.py`:
```python
"""Konstanten für {PACKAGE_NAME} — alle Regelwerk-Grenzwerte hier zentralisieren."""

# Norm-Version (für Nachvollziehbarkeit in Reports)
NORM_VERSION = "[z.B. DIN-4109-2018]"

# Grenzwerte (nie hardcoded in Analyselogik)
# BEISPIEL_GRENZWERT_XY = 35.0  # [Quelle: Norm §X Abs.Y]
```

Erstelle leere `packages/{PACKAGE_NAME}/src/nl2cad/{MODULE_ID}/analyzer.py`:
```python
"""Haupt-Analyzer für {PACKAGE_NAME}."""
import logging

from nl2cad.core.handlers.base import BaseCADHandler, HandlerResult

logger = logging.getLogger(__name__)


class [HauptAnalyzer](BaseCADHandler):
    """[Beschreibung]."""

    name = "[HauptAnalyzer]"
    description = "[Kurzbeschreibung]"
    required_inputs: list[str] = ["ifc_model"]

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name)
        # TODO: Implementierung gemäß ADR-{ADR_NR}
        return result
```

Erstelle `packages/{PACKAGE_NAME}/tests/__init__.py` (leer) und
`packages/{PACKAGE_NAME}/tests/test_{MODULE_ID}.py`:
```python
"""Tests für {PACKAGE_NAME} — KEINE Mocks für Parser-Tests (AGENTS.md)."""
import pytest


def test_placeholder():
    """Platzhalter — ersetzen durch echte Tests mit Fixtures."""
    assert True
```

---

## Schritt 3 — modules.json aktualisieren

Füge in `docs/data/modules.json` unter `"modules"` ein neues Objekt ein:

```json
{
  "id": "{MODULE_ID}",
  "package": "{PACKAGE_NAME}",
  "name": "[Anzeigename]",
  "icon": "[Emoji]",
  "color": "#[Hex]",
  "tagline": "[Kurzbeschreibung]",
  "description": "[Langbeschreibung]",
  "features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5", "Feature 6"],
  "deps": ["nl2cad-core"],
  "required": false,
  "pricing": { "setup_eur": 0, "monthly_eur": 49, "label": "49 € / Monat" },
  "pypi": "https://pypi.org/project/{PACKAGE_NAME}/",
  "status": "planned",
  "adr": "docs/adr/ADR-{ADR_NR}-{MODULE_ID}-package.md",
  "workflow": ".windsurf/workflows/new-module.md"
}
```

---

## Schritt 4 — CHANGELOG.md aktualisieren

In `CHANGELOG.md` unter `[Unreleased]` eintragen:
```markdown
### Added
- `{PACKAGE_NAME}` Package-Skeleton (ADR-{ADR_NR})
```

---

## Schritt 5 — CI prüfen

// turbo
```bash
uv run pytest packages/{PACKAGE_NAME}/ -v
```

---

## Schritt 6 — Commit

```bash
git add packages/{PACKAGE_NAME}/ docs/adr/ADR-{ADR_NR}-{MODULE_ID}-package.md docs/data/modules.json CHANGELOG.md
git commit -m "feat({PACKAGE_NAME}): Package-Skeleton + ADR-{ADR_NR} + modules.json Eintrag"
```
