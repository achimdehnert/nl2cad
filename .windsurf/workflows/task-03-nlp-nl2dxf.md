---
description: NL2DXF Generator aus cad-hub in nl2cad-nlp portieren — ohne Django
---

# Task 03 — NL2DXF portieren (nl2cad-nlp)

## Kontext

In `cad-hub/apps/dxf/services/nl2dxf.py` existiert ein NL2DXFGenerator.
Dieser soll als **framework-agnostische Library** in `nl2cad-nlp` landen.

Wichtige Unterschiede zum Original:
- **Kein Django** — kein `from django.conf import settings`
- **LLM-Client injizierbar** — kein hardcoded Client-Import
- **Gibt `list[CADCommand]` zurück** — aus `nl2cad.core.models.dxf`

## Schritt 1 — Original-Code verstehen

Lies den Original-Code in `cad-hub/apps/dxf/services/nl2dxf.py` durch.
Identifiziere:
- Welche Teile sind Django-abhängig? (Settings, ORM, Request)
- Welche Teile sind reine Logik?
- Was ist der LLM-System-Prompt?

## Schritt 2 — NL2DXFGenerator implementieren

**Zieldatei:** `packages/nl2cad-nlp/src/nl2cad/nlp/nl2dxf.py`

```python
# Spezifikation:

from nl2cad.core.models.dxf import CADCommand, CADCommandType
from dataclasses import dataclass, field

@dataclass
class NL2DXFResult:
    success: bool
    commands: list[CADCommand] = field(default_factory=list)
    raw_llm_response: str = ""
    error: str = ""
    used_fallback: bool = False   # True wenn kein LLM → Regex-Fallback


class NL2DXFGenerator:
    """
    Konvertiert natürlichsprachliche Beschreibungen in CAD-Befehle.

    Zwei Modi:
    1. Mit LLM-Client: Vollständige NL-Interpretation via LLM
    2. Ohne LLM-Client (llm_client=None): Regex-basiertes Fallback-Parsing

    Usage:
        # Mit LLM
        gen = NL2DXFGenerator(llm_client=my_client)
        result = gen.generate("Ein Raum 5m x 4m mit Fenster Nord")

        # Ohne LLM (Fallback)
        gen = NL2DXFGenerator()
        result = gen.generate("Rechteck 5x4")
        # → CADCommand(command="RECT", params={"x":0,"y":0,"width":5,"height":4})
    """

    SYSTEM_PROMPT = """..."""  # System-Prompt aus Original übernehmen

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def generate(self, description: str, use_llm: bool = True) -> NL2DXFResult:
        """Hauptmethode: NL-Beschreibung → CAD-Befehle."""
        if self.llm_client and use_llm:
            return self._generate_with_llm(description)
        return self._generate_fallback(description)

    def _generate_with_llm(self, description: str) -> NL2DXFResult:
        """LLM-basierte Generierung."""
        ...

    def _generate_fallback(self, description: str) -> NL2DXFResult:
        """
        Regex-basiertes Fallback ohne LLM.
        Muster die erkannt werden sollen:
        - "Rechteck N x M" / "Raum NxM" → RECT
        - "Kreis Radius N" → CIRCLE
        - "Linie von (x1,y1) nach (x2,y2)" → LINE
        """
        ...

    def parse_llm_response(self, json_str: str) -> list[CADCommand]:
        """Parsed LLM-JSON-Response in CADCommand-Liste."""
        # JSON-Array von Dicts → list[CADCommand]
        # Fehlerbehandlung: ungültiges JSON → leere Liste + Logging
        ...
```

## Schritt 3 — Fallback-Parser implementieren (kritisch für Tests)

Der Fallback-Parser muss ohne LLM getestet werden können:

```python
# Regex-Patterns für Fallback:
import re

PATTERNS = [
    # "Rechteck 5m x 4m" oder "Raum 5x4" oder "5 x 4"
    (r"(?:rechteck|raum|room)?\s*(\d+\.?\d*)\s*[mx×]\s*(\d+\.?\d*)",
     lambda m: CADCommand("RECT", {"x": 0, "y": 0,
                                    "width": float(m.group(1)),
                                    "height": float(m.group(2))}, "Rooms")),
    # "Kreis Radius 3" oder "circle r=3"
    (r"(?:kreis|circle).*?(\d+\.?\d*)",
     lambda m: CADCommand("CIRCLE", {"cx": 0, "cy": 0,
                                      "radius": float(m.group(1))}, "Objects")),
]
```

## Schritt 4 — Tests

**Zieldatei:** `packages/nl2cad-nlp/tests/test_nl2dxf.py`

Alle Tests OHNE echten LLM-Client:

```python
class TestNL2DXFFallback:

    def test_rechteck_erkannt(self):
        gen = NL2DXFGenerator()  # kein LLM
        result = gen.generate("Rechteck 5m x 4m")
        assert result.success
        assert result.used_fallback
        assert len(result.commands) >= 1
        rect = result.commands[0]
        assert rect.command == "RECT"
        assert rect.params["width"] == pytest.approx(5.0)
        assert rect.params["height"] == pytest.approx(4.0)

    def test_raum_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Raum 6x5")
        assert result.success

    def test_kreis_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Kreis Radius 3m")
        assert result.success
        assert result.commands[0].command == "CIRCLE"
        assert result.commands[0].params["radius"] == pytest.approx(3.0)

    def test_unbekannte_beschreibung(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Irgendwas ohne Maße")
        # Kein Crash, leere Liste ok
        assert result.used_fallback
        assert isinstance(result.commands, list)

    def test_parse_llm_response_valid_json(self):
        gen = NL2DXFGenerator()
        json_str = '[{"command": "RECT", "params": {"x":0,"y":0,"width":5,"height":4}, "layer": "Rooms"}]'
        commands = gen.parse_llm_response(json_str)
        assert len(commands) == 1
        assert commands[0].params["width"] == 5

    def test_parse_llm_response_invalid_json(self):
        gen = NL2DXFGenerator()
        commands = gen.parse_llm_response("kein json {{{")
        assert commands == []  # Kein Crash
```

## Schritt 5 — IntentClassifier erweitern

In `packages/nl2cad-nlp/src/nl2cad/nlp/intent.py` fehlen noch einige Keywords.
Ergänze die `_INTENT_PATTERNS`:

```python
# Fehlende Pattern ergänzen:
(NLIntent.RAUMANALYSE, [
    "raum", "räume", "fläche", "grundriss", "raumliste",
    "wie viele räume", "raumbuch", "raumgrößen"   # ← ergänzen
]),
(NLIntent.BRANDSCHUTZ, [
    "brandschutz", "brandabschnitt", "f30", "f60", "f90",
    "feuerwiderstand", "brandmeldung", "sprinkler"   # ← ergänzen
]),
# Neues Pattern für Abstandsflächen:
(NLIntent.ABSTANDSFLAECHEN, ["abstandsfläche", "abstand", "baulinie", "bauwich"]),
# NLIntent.ABSTANDSFLAECHEN in Enum ergänzen
```

## Schritt 6 — Abschluss-Check

```bash
uv run pytest packages/nl2cad-nlp/ -v     # mind. 8 Tests erwartet
uv run pytest -v                           # alle Tests, keine Regression
uv run ruff check packages/nl2cad-nlp/
```

## Definition of Done

- [ ] `NL2DXFGenerator` ohne LLM-Dependency testbar
- [ ] Fallback-Parser für RECT, CIRCLE, LINE implementiert
- [ ] `parse_llm_response` mit Error-Handling
- [ ] ≥ 8 Tests grün
- [ ] Kein Django-Import in nl2cad-nlp
- [ ] `CHANGELOG.md` aktualisiert
