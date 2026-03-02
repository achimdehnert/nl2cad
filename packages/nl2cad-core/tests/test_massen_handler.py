"""
Tests fuer nl2cad.core.handlers.massen.MassenHandler.
"""

from __future__ import annotations

import pytest

from nl2cad.core.handlers.massen import MassenHandler
from nl2cad.core.models.dxf import DXFModel, DXFRoom
from nl2cad.core.models.ifc import (
    IFCFloor,
    IFCModel,
    IFCRoom,
    IFCSlab,
    IFCWall,
)


@pytest.fixture
def handler() -> MassenHandler:
    return MassenHandler()


def _make_ifc_model(
    rooms: list[IFCRoom],
    walls: list[IFCWall] | None = None,
    slabs: list[IFCSlab] | None = None,
) -> IFCModel:
    floor = IFCFloor(
        ifc_id="F1",
        name="EG",
        number=0,
        elevation_m=0.0,
        rooms=rooms,
        walls=walls or [],
        slabs=slabs or [],
    )
    model = IFCModel(source_file="test.ifc")
    model.floors = [floor]
    return model


class TestMassenHandlerIFC:
    def test_should_calculate_raumflaeche(self, handler):
        rooms = [
            IFCRoom(
                ifc_id="R1", name="Wohnzimmer", area_m2=30.0, height_m=2.5
            ),
            IFCRoom(
                ifc_id="R2", name="Schlafzimmer", area_m2=15.0, height_m=2.5
            ),
        ]
        model = _make_ifc_model(rooms)
        result = handler.run({"ifc_model": model})
        assert result.success
        assert result.data["massen"]["raumflaeche_gesamt_m2"] == pytest.approx(
            45.0
        )

    def test_should_calculate_volumen(self, handler):
        rooms = [
            IFCRoom(ifc_id="R1", name="Raum", area_m2=20.0, height_m=3.0),
        ]
        model = _make_ifc_model(rooms)
        result = handler.run({"ifc_model": model})
        assert result.data["massen"]["volumen_gesamt_m3"] == pytest.approx(
            60.0
        )

    def test_should_count_raeume(self, handler):
        rooms = [
            IFCRoom(ifc_id="R1", name="R1", area_m2=10.0),
            IFCRoom(ifc_id="R2", name="R2", area_m2=10.0),
            IFCRoom(ifc_id="R3", name="R3", area_m2=10.0),
        ]
        model = _make_ifc_model(rooms)
        result = handler.run({"ifc_model": model})
        assert result.data["massen"]["raum_count"] == 3

    def test_should_calculate_wandflaeche(self, handler):
        rooms = [IFCRoom(ifc_id="R1", name="Raum", area_m2=20.0)]
        walls = [
            IFCWall(ifc_id="W1", name="Wand1", area_m2=12.0),
            IFCWall(ifc_id="W2", name="Wand2", area_m2=8.0),
        ]
        model = _make_ifc_model(rooms, walls=walls)
        result = handler.run({"ifc_model": model})
        assert result.data["massen"]["wandflaeche_gesamt_m2"] == pytest.approx(
            20.0
        )

    def test_should_handle_empty_model(self, handler):
        model = _make_ifc_model([])
        result = handler.run({"ifc_model": model})
        assert result.success
        assert result.data["massen"]["raumflaeche_gesamt_m2"] == 0.0
        assert result.data["massen"]["volumen_gesamt_m3"] == 0.0
        assert result.data["massen"]["raum_count"] == 0

    def test_should_ignore_rooms_with_zero_height_for_volumen(self, handler):
        rooms = [
            IFCRoom(ifc_id="R1", name="R1", area_m2=20.0, height_m=0.0),
        ]
        model = _make_ifc_model(rooms)
        result = handler.run({"ifc_model": model})
        assert result.data["massen"]["volumen_gesamt_m3"] == 0.0


class TestMassenHandlerDXF:
    def test_should_calculate_raumflaeche_from_dxf(self, handler):
        room1 = DXFRoom(name="Raum1", area_m2=25.0)
        room2 = DXFRoom(name="Raum2", area_m2=15.0)
        model = DXFModel(source_file="test.dxf")
        model.rooms = [room1, room2]
        result = handler.run({"dxf_model": model})
        assert result.success
        assert result.data["massen"]["raumflaeche_gesamt_m2"] == pytest.approx(
            40.0
        )

    def test_should_warn_about_missing_volumen_in_dxf(self, handler):
        model = DXFModel(source_file="test.dxf")
        result = handler.run({"dxf_model": model})
        assert result.data["massen"]["volumen_gesamt_m3"] == 0.0
        assert len(result.warnings) > 0
        assert any("Volumen" in w for w in result.warnings)

    def test_should_have_zero_wandflaeche_for_dxf(self, handler):
        model = DXFModel(source_file="test.dxf")
        result = handler.run({"dxf_model": model})
        assert result.data["massen"]["wandflaeche_gesamt_m2"] == 0.0


class TestMassenHandlerErrors:
    def test_should_fail_when_no_model(self, handler):
        result = handler.run({})
        assert not result.success
        assert len(result.errors) > 0

    def test_should_fail_with_empty_input(self, handler):
        result = handler.run({"unrelated_key": "value"})
        assert not result.success


class TestMassenHandlerPipeline:
    def test_should_work_after_file_input_in_pipeline(self):
        from unittest.mock import patch

        from nl2cad.core.handlers.base import CADHandlerPipeline
        from nl2cad.core.handlers.file_input import FileInputHandler

        rooms = [
            IFCRoom(ifc_id="R1", name="Wohnzimmer", area_m2=30.0, height_m=2.5)
        ]
        floor = IFCFloor(
            ifc_id="F1", name="EG", number=0, elevation_m=0.0, rooms=rooms
        )
        mock_model = IFCModel(source_file="test.ifc")
        mock_model.floors = [floor]

        with patch("nl2cad.core.handlers.file_input.IFCParser") as MockParser:
            MockParser.return_value.parse_bytes.return_value = mock_model
            pipeline = CADHandlerPipeline()
            pipeline.add(FileInputHandler())
            pipeline.add(MassenHandler())
            pipeline.run(
                {
                    "file_content": b"fake ifc",
                    "filename": "test.ifc",
                }
            )

        ctx = pipeline.get_context()
        assert "massen" in ctx
        assert ctx["massen"]["raumflaeche_gesamt_m2"] == pytest.approx(30.0)
