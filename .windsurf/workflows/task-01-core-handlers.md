---
description: nl2cad-core Handler implementieren — FileInputHandler und MassenHandler
---

# Task 01 — Core Handler (nl2cad-core)

## Kontext

Die Handler-Pipeline in `nl2cad-core` hat bereits die Basis-Klassen (`BaseCADHandler`,
`CADHandlerPipeline`). Es fehlen die konkreten Handler, die cad-hub als nächstes braucht.

## Schritt 1 — Status prüfen

```bash
uv run pytest -v
uv run ruff check packages/nl2cad-core/
```

Prüfe welche Handler-Dateien in `packages/nl2cad-core/src/nl2cad/core/handlers/` bereits existieren.
Aktuell vorhanden: `base.py`. Fehlend: `file_input.py`, `massen.py`, `room_analysis.py`.

## Schritt 2 — FileInputHandler implementieren

**Zieldatei:** `packages/nl2cad-core/src/nl2cad/core/handlers/file_input.py`

Klasse: `FileInputHandler(BaseCADHandler)`

```python
# Spezifikation:
name = "FileInputHandler"
required_inputs = []  # Akzeptiert file_path ODER file_content+filename
optional_inputs = ["file_path", "file_content", "filename"]

# execute() muss:
# 1. file_path oder (file_content + filename) aus input_data lesen
# 2. Format erkennen via pathlib.Path(filename).suffix.lower()
# 3. Bei .ifc → IFCParser().parse() oder parse_bytes() aufrufen
# 4. Bei .dxf/.dwg → DXFParser().parse() oder parse_bytes() aufrufen
# 5. Bei unbekanntem Format → UnsupportedFormatError raisen (NICHT fangen)
# 6. result.data schreiben:
#    - "format": "ifc" oder "dxf"
#    - "source_file": str(path oder filename)
#    - "ifc_model": IFCModel (nur bei IFC)
#    - "dxf_model": DXFModel (nur bei DXF)
```

## Schritt 3 — FileInputHandler Tests

**Zieldatei:** `packages/nl2cad-core/tests/test_file_input_handler.py`

Mindest-Test-Cases (alle ohne echte IFC/DXF-Dateien — Mocks für Parser erlaubt):
1. `test_detect_ifc_format()` — .ifc Extension → format == "ifc"
2. `test_detect_dxf_format()` — .dxf Extension → format == "dxf"
3. `test_unsupported_format_raises()` — .pdf → UnsupportedFormatError
4. `test_missing_input_fails()` — leeres input_data → result.success == False
5. `test_pipeline_integration()` — FileInputHandler in Pipeline → Context enthält "format"

```python
# Pattern für Mock-Test:
from unittest.mock import patch, MagicMock
from nl2cad.core.handlers.file_input import FileInputHandler
from nl2cad.core.models.ifc import IFCModel

def test_detect_ifc_format():
    handler = FileInputHandler()
    mock_model = IFCModel(project_name="Test")
    with patch("nl2cad.core.handlers.file_input.IFCParser") as MockParser:
        MockParser.return_value.parse_bytes.return_value = mock_model
        result = handler.run({
            "file_content": b"fake ifc content",
            "filename": "gebaeude.ifc",
        })
    assert result.success
    assert result.data["format"] == "ifc"
    assert "ifc_model" in result.data
```

## Schritt 4 — MassenHandler implementieren

**Zieldatei:** `packages/nl2cad-core/src/nl2cad/core/handlers/massen.py`

Klasse: `MassenHandler(BaseCADHandler)`

```python
# Spezifikation:
name = "MassenHandler"
required_inputs = []  # Braucht entweder "ifc_model" oder "dxf_model"

# execute() muss:
# 1. ifc_model oder dxf_model aus input_data lesen
# 2. Bei IFCModel:
#    - Gesamtfläche: sum(room.area_m2 for room in model.rooms)
#    - Wandflächen: sum(wall.area_m2 for wall in model.walls)
#    - Deckenflächen: sum(slab.area_m2 for slab in model.slabs)
#    - Gesamtvolumen: sum(room.area_m2 * room.height_m for room in model.rooms)
# 3. Bei DXFModel:
#    - Gesamtfläche: sum(room.area_m2 for room in model.rooms)
#    - Volumen: nicht berechenbar → 0.0 mit Warnung
# 4. result.data["massen"] schreiben:
#    {
#      "raumflaeche_gesamt_m2": float,
#      "wandflaeche_gesamt_m2": float,
#      "deckenflaeche_gesamt_m2": float,
#      "volumen_gesamt_m3": float,
#      "raum_count": int,
#    }
```

## Schritt 5 — MassenHandler Tests

**Zieldatei:** `packages/nl2cad-core/tests/test_massen_handler.py`

Mindest-Test-Cases:
1. `test_massen_from_ifc()` — IFCModel mit 2 Räumen → korrekte Summen
2. `test_massen_from_dxf()` — DXFModel → Fläche ok, Volumen 0 + Warnung
3. `test_no_model_fails()` — Kein model in input → result.success == False
4. `test_empty_model()` — IFCModel ohne Räume → alle Werte 0.0
5. `test_pipeline_after_file_input()` — FileInput → Massen Pipeline-Test

## Schritt 6 — handlers/__init__.py aktualisieren

```python
# packages/nl2cad-core/src/nl2cad/core/handlers/__init__.py
from nl2cad.core.handlers.base import BaseCADHandler, CADHandlerPipeline, HandlerResult, HandlerStatus
from nl2cad.core.handlers.file_input import FileInputHandler
from nl2cad.core.handlers.massen import MassenHandler

__all__ = [
    "BaseCADHandler", "CADHandlerPipeline", "HandlerResult", "HandlerStatus",
    "FileInputHandler", "MassenHandler",
]
```

## Schritt 7 — nl2cad-core __init__.py erweitern

Füge `FileInputHandler` und `MassenHandler` zur Public API in
`packages/nl2cad-core/src/nl2cad/core/__init__.py` hinzu.

## Schritt 8 — Abschluss-Check

```bash
uv run pytest packages/nl2cad-core/ -v
uv run pytest tests/integration/ -v
uv run ruff check packages/nl2cad-core/
uv run ruff format packages/nl2cad-core/
```

Alle Tests grün → CHANGELOG.md `[Unreleased]` updaten → fertig.

## Definition of Done

- [ ] `FileInputHandler` implementiert
- [ ] `MassenHandler` implementiert  
- [ ] Mindestens 10 neue Tests grün
- [ ] `uv run pytest -v` → alle Tests grün (keine Regression)
- [ ] `uv run ruff check packages/` → 0 Errors
- [ ] `CHANGELOG.md` aktualisiert
