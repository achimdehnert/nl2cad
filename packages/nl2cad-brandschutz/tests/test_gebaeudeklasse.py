"""
Tests fuer nl2cad.brandschutz.gebaeudeklasse.GebaeudeklasseHandler.

Testet:
- GK1..GK5 und Hochhaus anhand OKFF-Werte
- Fehlende Geschosse -> UNBEKANNT
- Alle elevation_m==0 -> UNBEKANNT mit Meldung
- Keine Raumflaechen -> konservativ GK3
"""

from __future__ import annotations

from nl2cad.core.models.ifc import IFCFloor, IFCModel, IFCRoom


def _make_floor(name: str, elevation: float, area: float = 200.0) -> IFCFloor:
    f = IFCFloor()
    f.name = name
    f.elevation_m = elevation
    room = IFCRoom()
    room.name = "Buero"
    room.area_m2 = area
    f.rooms = [room]
    return f


def _make_model(floors: list) -> IFCModel:
    model = IFCModel()
    model.floors = floors
    return model


class TestGebaeudeklasseHandler:
    def test_should_return_unbekannt_for_empty_model(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        model = _make_model([])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.UNBEKANNT
        assert len(result.meldungen) > 0

    def test_should_return_hochhaus_above_22m(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("OG7", 23.5)])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.HOCHHAUS
        assert result.ist_hochhaus is True

    def test_should_return_gk5_between_13_and_22m(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("OG4", 15.0)])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.GK_5

    def test_should_return_gk4_between_7_and_13m(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("OG2", 9.0)])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.GK_4

    def test_should_return_gk3_for_many_floors_below_7m(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        floors = [
            _make_floor("EG", 0.0),
            _make_floor("OG1", 3.0),
            _make_floor("OG2", 6.0),
        ]
        model = _make_model(floors)
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.GK_3

    def test_should_return_gk1_for_single_small_floor(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("EG", 0.0, area=80.0)])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.GK_1

    def test_should_include_norm_version(self):
        from nl2cad.brandschutz.constants import MBO_VERSION
        from nl2cad.brandschutz.gebaeudeklasse import GebaeudeklasseHandler

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("EG", 3.0)])
        result = handler.ermittle(model)
        assert result.norm_version == MBO_VERSION
        assert MBO_VERSION in result.meldungen[0]

    def test_should_return_gk3_conservative_when_no_room_areas(self):
        from nl2cad.brandschutz.gebaeudeklasse import (
            Gebaeudeklasse,
            GebaeudeklasseHandler,
        )

        handler = GebaeudeklasseHandler()
        floor = IFCFloor()
        floor.name = "EG"
        floor.elevation_m = 3.0
        floor.rooms = []
        model = _make_model([floor])
        result = handler.ermittle(model)
        assert result.gebaeudeklasse == Gebaeudeklasse.GK_3
        assert any("Konservativ" in m for m in result.meldungen)

    def test_should_flag_hochhaus_property(self):
        from nl2cad.brandschutz.gebaeudeklasse import GebaeudeklasseHandler

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("EG", 25.0)])
        result = handler.ermittle(model)
        assert result.ist_hochhaus is True

    def test_to_dict_contains_required_keys(self):
        from nl2cad.brandschutz.gebaeudeklasse import GebaeudeklasseHandler

        handler = GebaeudeklasseHandler()
        model = _make_model([_make_floor("EG", 3.0)])
        result = handler.ermittle(model)
        d = result.to_dict()
        assert "gebaeudeklasse" in d
        assert "okff_max_m" in d
        assert "ist_hochhaus" in d
        assert "norm_version" in d
