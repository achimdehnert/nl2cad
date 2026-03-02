"""
Tests für nl2cad-core: DIN277Calculator, WoFlVCalculator.
Keine Mocks — echte Logik-Tests.
"""

import pytest

from nl2cad.areas.din277 import DIN277Calculator
from nl2cad.areas.woflv import WoFlVCalculator


class TestDIN277Calculator:
    def test_classify_buero(self):
        calc = DIN277Calculator()
        assert calc.classify_room("Büro 1.01") == "NUF_2"

    def test_classify_flur(self):
        calc = DIN277Calculator()
        assert calc.classify_room("Flur EG") == "VF_1"

    def test_classify_wohnzimmer(self):
        calc = DIN277Calculator()
        assert calc.classify_room("Wohnzimmer") == "NUF_1"

    def test_calculate_rooms(self):
        calc = DIN277Calculator()
        rooms = [
            {"name": "Büro 1", "area_m2": 20.0},
            {"name": "Büro 2", "area_m2": 15.0},
            {"name": "Flur", "area_m2": 8.0},
        ]
        result = calc.calculate(rooms)
        assert result.nutzungsflaeche_m2 == pytest.approx(35.0)
        assert result.verkehrsflaeche_m2 == pytest.approx(8.0)
        assert result.netto_grundflaeche_m2 == pytest.approx(43.0)

    def test_unclassified_room_defaults_to_nuf8(self):
        calc = DIN277Calculator()
        rooms = [{"name": "Sonstige Nutzung XYZ", "area_m2": 10.0}]
        result = calc.calculate(rooms)
        assert "NUF_8" in result.categories
        assert len(result.warnings) > 0

    def test_empty_rooms(self):
        calc = DIN277Calculator()
        result = calc.calculate([])
        assert result.netto_grundflaeche_m2 == 0.0
        assert result.total_rooms == 0

    def test_to_dict(self):
        calc = DIN277Calculator()
        result = calc.calculate([{"name": "Büro", "area_m2": 25.0}])
        d = result.to_dict()
        assert "nutzungsflaeche_m2" in d
        assert "categories" in d
        assert d["nutzungsflaeche_m2"] == pytest.approx(25.0)


class TestWoFlVCalculator:
    def test_full_height_room(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [{"name": "Wohnzimmer", "area_m2": 30.0, "height_m": 2.5}]
        )
        assert result.total_woflv_m2 == pytest.approx(30.0)  # Faktor 1.0

    def test_low_ceiling_half_factor(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [{"name": "Dachschräge", "area_m2": 10.0, "height_m": 1.5}]
        )
        assert result.total_woflv_m2 == pytest.approx(5.0)  # Faktor 0.5

    def test_very_low_ceiling_excluded(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [{"name": "Kriechkeller", "area_m2": 10.0, "height_m": 0.5}]
        )
        assert result.total_woflv_m2 == pytest.approx(0.0)  # Faktor 0.0

    def test_balcony_25_percent(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [{"name": "Balkon", "area_m2": 8.0, "is_balcony": True}]
        )
        assert result.total_woflv_m2 == pytest.approx(2.0)  # 25%

    def test_mixed_rooms(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [
                {"name": "Wohnzimmer", "area_m2": 30.0, "height_m": 2.5},
                {"name": "Balkon", "area_m2": 8.0, "is_balcony": True},
                {"name": "Schräge", "area_m2": 6.0, "height_m": 1.5},
            ]
        )
        # 30*1.0 + 8*0.25 + 6*0.5 = 30 + 2 + 3 = 35
        assert result.total_woflv_m2 == pytest.approx(35.0)

    def test_zero_area_skipped_with_warning(self):
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms(
            [{"name": "Kein Raum", "area_m2": 0.0}]
        )
        assert result.total_woflv_m2 == pytest.approx(0.0)
        assert len(result.warnings) > 0
