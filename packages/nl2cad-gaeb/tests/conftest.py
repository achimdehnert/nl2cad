"""Gemeinsame Fixtures fuer nl2cad-gaeb Tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from nl2cad.gaeb.models import Leistungsverzeichnis, LosGruppe, Position


@pytest.fixture
def simple_position() -> Position:
    return Position(
        oz="01.001",
        kurztext="Parkett Wohnzimmer",
        menge=Decimal("30.0"),
        einheit="m²",
        einheitspreis=Decimal("65.00"),
    )


@pytest.fixture
def simple_lv() -> Leistungsverzeichnis:
    return Leistungsverzeichnis(
        projekt_name="Test-LV",
        projekt_nummer="2026-001",
        lose=[
            LosGruppe(
                oz="01",
                bezeichnung="Bodenbelaege",
                positionen=[
                    Position(
                        oz="01.001",
                        kurztext="Parkett Wohnzimmer",
                        menge=Decimal("30.0"),
                        einheit="m²",
                        einheitspreis=Decimal("65.00"),
                    ),
                    Position(
                        oz="01.002",
                        kurztext="Fliesen Bad",
                        menge=Decimal("8.0"),
                        einheit="m²",
                        einheitspreis=Decimal("45.00"),
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def sample_ifc_data() -> dict:
    return {
        "project_name": "Test Neubau",
        "rooms": [
            {
                "name": "Buero 1",
                "area_m2": 25.0,
                "perimeter_m": 20.0,
                "height_m": 2.8,
            },
            {
                "name": "Buero 2",
                "area_m2": 18.0,
                "perimeter_m": 17.0,
                "height_m": 2.8,
            },
        ],
        "walls": [],
        "doors": [],
        "windows": [],
        "slabs": [],
    }
