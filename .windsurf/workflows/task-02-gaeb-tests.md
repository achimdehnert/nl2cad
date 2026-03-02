---
description: nl2cad-gaeb vollständig testen — GAEBGenerator, IFCX83Converter
---

# Task 02 — GAEB Tests (nl2cad-gaeb)

## Kontext

`nl2cad-gaeb` hat funktionierenden Code (Generator + Converter + Models),
aber 0 Tests. Das muss behoben werden bevor cad-hub diese Library nutzt.

## Schritt 1 — Status prüfen

```bash
uv run pytest packages/nl2cad-gaeb/ -v   # → 0 Tests (expected)
uv run ruff check packages/nl2cad-gaeb/
```

Lies den bestehenden Code durch:
- `packages/nl2cad-gaeb/src/nl2cad/gaeb/models.py`
- `packages/nl2cad-gaeb/src/nl2cad/gaeb/generator.py`
- `packages/nl2cad-gaeb/src/nl2cad/gaeb/converter.py`

## Schritt 2 — Models Tests

**Zieldatei:** `packages/nl2cad-gaeb/tests/test_gaeb_models.py`

```python
# Mindest-Test-Cases:

def test_position_gesamtpreis():
    """EP × Menge = Gesamtpreis."""
    pos = Position(oz="01.001", kurztext="Bodenbelag", menge=Decimal("25.0"),
                   einheitspreis=Decimal("45.00"))
    assert pos.gesamtpreis == Decimal("1125.00")

def test_losgruppe_summe():
    """Summe aller Positionen."""
    ...

def test_leistungsverzeichnis_netto_mwst_brutto():
    """NGF = Netto + 19% MwSt = Brutto."""
    ...

def test_leistungsverzeichnis_phase_default():
    """Default-Phase ist X83."""
    lv = Leistungsverzeichnis(projekt_name="Test")
    assert lv.phase == GAEBPhase.X83

def test_empty_lv():
    """LV ohne Lose → Summen 0."""
    lv = Leistungsverzeichnis(projekt_name="Test")
    assert lv.netto_summe == Decimal("0")
    assert lv.brutto_summe == Decimal("0")
```

## Schritt 3 — GAEBGenerator Tests

**Zieldatei:** `packages/nl2cad-gaeb/tests/test_gaeb_generator.py`

```python
# Mindest-Test-Cases:

def test_generate_xml_returns_bytes():
    """generate_xml gibt BytesIO zurück."""
    ...

def test_generated_xml_is_valid_xml():
    """Output ist valides XML."""
    import xml.etree.ElementTree as ET
    generator = GAEBGenerator()
    lv = _make_test_lv()
    output = generator.generate_xml(lv)
    root = ET.fromstring(output.read())   # Darf nicht werfen
    assert root is not None

def test_generated_xml_contains_project_name():
    """Projektname ist im XML enthalten."""
    ...

def test_generated_xml_contains_positions():
    """Positionen sind im XML enthalten."""
    ...

def test_generate_excel_returns_readable_workbook():
    """generate_excel gibt lesbares Excel zurück."""
    from openpyxl import load_workbook
    generator = GAEBGenerator()
    output = generator.generate_excel(_make_test_lv())
    wb = load_workbook(output)   # Darf nicht werfen
    assert "Leistungsverzeichnis" in wb.sheetnames

def test_generate_excel_contains_positions():
    """Positionen sind in Excel enthalten."""
    ...

# Hilfsfunktion:
def _make_test_lv() -> Leistungsverzeichnis:
    return Leistungsverzeichnis(
        projekt_name="Testprojekt",
        lose=[LosGruppe(
            oz="01", bezeichnung="Bodenbeläge",
            positionen=[Position(
                oz="01.001", kurztext="Parkett",
                menge=Decimal("50.0"), einheit="m²",
                einheitspreis=Decimal("60.00"),
            )]
        )]
    )
```

## Schritt 4 — IFCX83Converter Tests

**Zieldatei:** `packages/nl2cad-gaeb/tests/test_ifc_x83_converter.py`

```python
# IFC-Daten-Fixture (dict — kein echtes IFC nötig):
IFC_DATA = {
    "project_name": "Neubau EFH",
    "rooms": [
        {"name": "Wohnzimmer", "area_m2": 30.0, "perimeter_m": 22.0, "height_m": 2.6},
        {"name": "Schlafzimmer", "area_m2": 16.0, "perimeter_m": 16.0, "height_m": 2.6},
    ],
    "walls": [{"name": "Außenwand", "area_m2": 45.0}],
    "doors": [{"name": "Haustür", "width_m": 1.0, "height_m": 2.1}],
    "windows": [],
    "slabs": [],
}

def test_convert_to_x83_returns_xml():
    ...

def test_convert_to_x83_has_positions_for_rooms():
    """Für jeden Raum gibt es eine GAEB-Position."""
    ...

def test_convert_to_excel_readable():
    ...

def test_empty_ifc_data():
    """Keine Räume → LV mit 0 Positionen (kein Crash)."""
    converter = IFCX83Converter()
    result = converter.convert_to_x83({}, projekt_name="Leer")
    assert result is not None
```

## Schritt 5 — conftest.py für gemeinsame Fixtures

**Zieldatei:** `packages/nl2cad-gaeb/tests/conftest.py`

```python
import pytest
from decimal import Decimal
from nl2cad.gaeb.models import GAEBPhase, Leistungsverzeichnis, LosGruppe, Position

@pytest.fixture
def simple_lv():
    return Leistungsverzeichnis(
        projekt_name="Test-LV",
        projekt_nummer="2026-001",
        lose=[LosGruppe(
            oz="01",
            bezeichnung="Bodenbeläge",
            positionen=[
                Position(oz="01.001", kurztext="Parkett Wohnzimmer",
                         menge=Decimal("30.0"), einheit="m²",
                         einheitspreis=Decimal("65.00")),
                Position(oz="01.002", kurztext="Fliesen Bad",
                         menge=Decimal("8.0"), einheit="m²",
                         einheitspreis=Decimal("45.00")),
            ]
        )]
    )

@pytest.fixture
def sample_ifc_data():
    return {
        "project_name": "Test Neubau",
        "rooms": [
            {"name": "Büro 1", "area_m2": 25.0, "perimeter_m": 20.0, "height_m": 2.8},
            {"name": "Büro 2", "area_m2": 18.0, "perimeter_m": 17.0, "height_m": 2.8},
        ],
        "walls": [], "doors": [], "windows": [], "slabs": [],
    }
```

## Schritt 6 — Abschluss-Check

```bash
uv run pytest packages/nl2cad-gaeb/ -v     # mind. 15 Tests erwartet
uv run pytest -v                            # alle Tests, keine Regression
uv run ruff check packages/nl2cad-gaeb/
```

## Definition of Done

- [ ] ≥ 15 Tests in nl2cad-gaeb grün
- [ ] XML-Output validiert (ET.fromstring ohne Exception)
- [ ] Excel-Output validiert (openpyxl load_workbook ohne Exception)
- [ ] `uv run pytest -v` → alle Tests grün
- [ ] `CHANGELOG.md` aktualisiert
