# AGENTS.md — nl2cad Coding Agent Guide

## Repo-Zweck

`nl2cad` ist eine **reine Python-Library** (kein Django, kein Web-Framework, kein HTTP-Server)
für BIM/CAD-Verarbeitung in der deutschen Baubranche.

Domänen: IFC-Parsing, DXF-Verarbeitung, DIN 277, WoFlV, Brandschutz, GAEB-Export, NL2CAD.

Downstream-Konsumenten: `cad-hub` (Django), zukünftige Apps.

---

## Package-Übersicht & strikte Grenzen

| Package | PyPI-Name | Zweck | Erlaubte Deps |
|---------|-----------|-------|---------------|
| `nl2cad/core` | `nl2cad-core` | IFC/DXF Parser, Dataclasses, Handler-Base | ifcopenshell, ezdxf |
| `nl2cad/areas` | `nl2cad-areas` | DIN 277, WoFlV Rechner | nl2cad-core |
| `nl2cad/brandschutz` | `nl2cad-brandschutz` | Brandschutz-Analyse, Regelwerk-Checks | nl2cad-core, nl2cad-areas |
| `nl2cad/gaeb` | `nl2cad-gaeb` | GAEB X81-X85 Generator | nl2cad-core, openpyxl |
| `nl2cad/nlp` | `nl2cad-nlp` | Intent, NL2DXF, Learning | nl2cad-core, httpx, pydantic |

### VERBOTENE Abhängigkeiten pro Package

```
nl2cad-core       → KEIN pydantic, KEIN httpx, KEIN LLM
nl2cad-areas      → KEIN httpx, KEIN LLM, KEIN openpyxl
nl2cad-brandschutz → KEIN httpx, KEIN LLM direkt
nl2cad-gaeb       → KEIN httpx, KEIN LLM
```

---

## Coding-Konventionen (STRIKT)

### Dataclasses in `core`, `areas`, `gaeb`, `brandschutz`
```python
# ✅ RICHTIG — stdlib dataclass, zero deps
from dataclasses import dataclass, field

@dataclass
class IFCRoom:
    name: str
    area_m2: float = 0.0
    height_m: float = 0.0
    din277_code: str = ""
```

```python
# ❌ FALSCH — kein Pydantic in core/areas/gaeb
from pydantic import BaseModel
class IFCRoom(BaseModel): ...
```

### Pydantic nur in `nl2cad-nlp`
```python
# ✅ Erlaubt in nl2cad/nlp/
from pydantic import BaseModel
class NLQueryResult(BaseModel): ...
```

### Feldnamen — immer mit Einheit-Suffix
```python
# ✅ RICHTIG
area_m2: float
height_m: float
thickness_m: float
perimeter_m: float

# ❌ FALSCH
area: float
height: float
```

### Logging — immer strukturiert
```python
# ✅ RICHTIG
import logging
logger = logging.getLogger(__name__)
logger.info("[RoomAnalysis] %d Räume gefunden", len(rooms))

# ❌ FALSCH
print(f"Räume: {rooms}")
```

### Fehlerbehandlung — eigene Exceptions
```python
# ✅ Exceptions in nl2cad/core/exceptions.py definieren
from nl2cad.core.exceptions import IFCParseError, UnsupportedFormatError

raise IFCParseError(f"Datei konnte nicht gelesen werden: {path}")
```

---

## Neue Funktion hinzufügen — Workflow

1. **Model/Dataclass** in `models.py` des jeweiligen Packages definieren
2. **Service/Handler** in `services/` oder `handlers/` implementieren
3. **Test** mit realem Fixture aus `tests/fixtures/` schreiben — KEINE Mocks für Parsing
4. **`__init__.py`** des Packages updaten (Public API)
5. **CHANGELOG.md** Eintrag unter `[Unreleased]`
6. **`__version__`** nicht manuell ändern — wird von `pyproject.toml` gelesen

---

## Tests — Regeln

```python
# tests/fixtures/ enthält echte .ifc und .dxf Dateien
# Diese MÜSSEN für Parser-Tests verwendet werden

# ✅ RICHTIG — echter Parser-Test
def test_ifc_room_parsing(fixture_ifc_simple):
    parser = IFCParser()
    result = parser.parse(fixture_ifc_simple)
    assert len(result.rooms) > 0
    assert result.rooms[0].area_m2 > 0

# ❌ FALSCH — Mock statt echtem Parse
def test_ifc_room_parsing(mocker):
    mocker.patch("nl2cad.core.parsers.ifcopenshell.open", ...)
```

### Test-Commands
```bash
# Alle Tests
uv run pytest

# Ein Package
uv run pytest packages/nl2cad-core/

# Mit Coverage
uv run pytest --cov=packages --cov-report=term-missing

# Nur Integration Tests
uv run pytest tests/integration/
```

---

## Release-Prozess

Releases werden über GitHub Tags getriggert — ein Tag pro Package:

```bash
git tag nl2cad-core@0.1.0
git tag nl2cad-areas@0.1.0
git push --tags
```

CI/CD published dann automatisch das betroffene Package zu PyPI.

### Versioning — Semantic Versioning (SemVer)
- `MAJOR`: Breaking API change
- `MINOR`: Neue Features, backward compatible
- `PATCH`: Bugfixes

---

## Verboten (für alle Packages)

- `print()` statt `logging`
- `requests` statt `httpx`
- Django ORM, Celery, Redis Imports
- JSONB / Datenbank-Logik
- Hardcoded Strings für Regelwerk-Codes (→ Konstanten in `constants.py`)
- `except Exception: pass` ohne Logging
- Mutable default arguments in Dataclasses (→ `field(default_factory=list)`)

---

## Wo liegt was?

```
packages/nl2cad-core/src/nl2cad/core/
├── __init__.py          # Public API des Packages
├── models/              # Dataclasses (IFCRoom, DXFLayer, ...)
├── parsers/             # ifcopenshell + ezdxf wrapper
├── handlers/            # BaseCADHandler, Pipeline
├── services/            # CADLoader, Konverter
├── exceptions.py        # Alle nl2cad Exceptions
└── constants.py         # DIN-Codes, Layer-Keywords, ...

packages/nl2cad-areas/src/nl2cad/areas/
├── __init__.py
├── din277.py            # DIN277Calculator
├── woflv.py             # WoFlVCalculator
└── models.py            # AreaResult, WoFlVResult

packages/nl2cad-brandschutz/src/nl2cad/brandschutz/
├── __init__.py
├── analyzer.py          # BrandschutzAnalyzer (Haupt-Einstiegspunkt)
├── models.py            # BrandschutzAnalyse, Fluchtweg, Brandabschnitt, ...
├── rules/               # Regelwerk-Checks
│   ├── asr_a23.py       # Fluchtweg-Regeln (ASR A2.3)
│   └── din4102.py       # Feuerwiderstand
└── constants.py         # Layer-Keywords, Feuerwiderstandsklassen

packages/nl2cad-gaeb/src/nl2cad/gaeb/
├── __init__.py
├── models.py            # Position, LosGruppe, Leistungsverzeichnis
├── generator.py         # GAEBGenerator XML/Excel
├── converter.py         # IFCX83Converter
└── constants.py         # GAEB Phasen, Namespace

packages/nl2cad-nlp/src/nl2cad/nlp/
├── __init__.py
├── intent.py            # IntentClassifier
├── nl2dxf.py            # NL2DXFGenerator
├── learning.py          # NLLearningStore
└── models.py            # Pydantic Models
```
