# nl2cad — Python Library Coding Rules

## Was dieses Repo ist

Reine Python-Library für BIM/CAD-Verarbeitung.
**Kein Django. Kein Web-Framework. Kein HTTP-Server.**

Downstream-Konsumenten (cad-hub, etc.) integrieren die Library.
Die Library selbst bleibt framework-agnostisch.

---

## Package-Grenzen (nie verletzen)

| Package | Erlaubte externe Deps |
|---------|----------------------|
| nl2cad-core | ifcopenshell, ezdxf — sonst nichts |
| nl2cad-areas | nur nl2cad-core |
| nl2cad-brandschutz | nl2cad-core, nl2cad-areas |
| nl2cad-gaeb | nl2cad-core, openpyxl |
| nl2cad-nlp | nl2cad-core, pydantic, httpx |

**Verboten in allen Packages:**
- `from django.*` — nie
- `from celery.*` — nie
- `import requests` — httpx verwenden wenn nötig
- `import redis` — nie

---

## Dataclasses — Pflicht in core/areas/gaeb/brandschutz

```python
# ✅ RICHTIG
from dataclasses import dataclass, field

@dataclass
class IFCRoom:
    name: str
    area_m2: float = 0.0      # ← Einheit-Suffix!
    height_m: float = 0.0     # ← Einheit-Suffix!
    perimeter_m: float = 0.0  # ← Einheit-Suffix!
    properties: dict = field(default_factory=dict)  # ← field() für mutable!

# ❌ FALSCH
class IFCRoom:
    area: float  # kein Suffix
    properties: dict = {}  # mutable default!
```

---

## Maßfelder — immer mit Einheits-Suffix

```python
# ✅ RICHTIG
area_m2: float
height_m: float
thickness_m: float
perimeter_m: float
length_m: float
volume_m3: float

# ❌ FALSCH
area: float
height: float
thickness: float
```

---

## Logging — immer strukturiert

```python
# ✅ RICHTIG — am Anfang jeder Datei
import logging
logger = logging.getLogger(__name__)

logger.info("[ClassName] %d items processed", count)
logger.warning("[ClassName] Fallback: %s", reason)
logger.error("[ClassName] Failed: %s", error)

# ❌ VERBOTEN
print(f"Processed {count} items")
print("Error:", error)
```

---

## Exceptions — eigene Klassen, nie silent catch

```python
# ✅ RICHTIG
from nl2cad.core.exceptions import IFCParseError

try:
    result = parse_ifc(path)
except SpecificError as e:
    raise IFCParseError(f"Konnte nicht parsen: {path}") from e

# ❌ FALSCH
try:
    result = parse_ifc(path)
except Exception:
    pass  # niemals!
```

---

## Handler-Pattern

```python
# ✅ RICHTIG — Handler gibt immer HandlerResult zurück
from nl2cad.core.handlers.base import BaseCADHandler, HandlerResult, HandlerStatus

class MyHandler(BaseCADHandler):
    name = "MyHandler"
    required_inputs = ["ifc_model"]

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name,
                               status=HandlerStatus.RUNNING)
        try:
            # ... Logik ...
            result.data["output_key"] = computed_value
            result.status = HandlerStatus.SUCCESS
        except Exception as e:
            result.add_error(str(e))  # ← add_error setzt success=False
        return result
```

---

## Tests — Regeln

```python
# ✅ RICHTIG — keine Mocks für reine Daten-Tests
def test_din277_berechnung():
    calc = DIN277Calculator()
    result = calc.calculate([{"name": "Büro", "area_m2": 25.0}])
    assert result.nutzungsflaeche_m2 == pytest.approx(25.0)

# ✅ RICHTIG — Mocks für LLM/HTTP in nlp-Tests erlaubt
def test_nl2dxf_with_mock_llm():
    with patch("nl2cad.nlp.nl2dxf.httpx.post") as mock:
        mock.return_value.json.return_value = [...]
        gen = NL2DXFGenerator(llm_client=mock)
        result = gen.generate("Raum 5x4")

# ❌ FALSCH — Parser mit Mocks testen
def test_ifc_parse():
    with patch("ifcopenshell.open") as mock:  # Nicht so!
        ...
# Stattdessen: echte .ifc Testdatei in tests/fixtures/ ablegen
```

---

## __init__.py — Public API explizit deklarieren

Jedes Package-`__init__.py` deklariert seine Public API explizit:

```python
# ✅ RICHTIG
from nl2cad.areas.din277 import DIN277Calculator, DIN277Result
from nl2cad.areas.woflv import WoFlVCalculator, WoFlVResult

__all__ = ["DIN277Calculator", "DIN277Result", "WoFlVCalculator", "WoFlVResult"]

# ❌ FALSCH — implizite Wildcard-Exports
```

---

## Nach jeder Implementierung

```bash
uv run pytest -v                    # Alle Tests grün
uv run ruff check packages/         # 0 Errors
uv run ruff format packages/        # Format korrekt
```

CHANGELOG.md `[Unreleased]` updaten.
