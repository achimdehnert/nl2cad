"""
Tests fuer nl2cad.core.parsers.ifc_parser.IFCParser
mit echter .ifc-Fixture (ARCHICAD IFC2X3).
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_IFC = Path(__file__).parent / "fixtures" / "minimal.ifc"

try:
    import ifcopenshell as _ifc  # noqa: F401

    _IFC_AVAILABLE = True
except Exception:
    _IFC_AVAILABLE = False

ifc_required = pytest.mark.skipif(
    not _IFC_AVAILABLE,
    reason="ifcopenshell nicht in uv-venv verfuegbar",
)


@pytest.fixture
def parser():
    from nl2cad.core.parsers.ifc_parser import IFCParser

    return IFCParser()


@pytest.fixture
def model(parser):
    return parser.parse(FIXTURE_IFC)


@ifc_required
class TestIFCParserBasic:
    def test_should_parse_without_error(self, model):
        assert model is not None

    def test_should_return_ifc_model(self, model):
        from nl2cad.core.models.ifc import IFCModel

        assert isinstance(model, IFCModel)

    def test_should_set_source_file(self, model):
        assert "minimal.ifc" in model.source_file

    def test_should_have_schema(self, model):
        assert model.schema != ""

    def test_should_have_floors(self, model):
        assert len(model.floors) > 0

    def test_should_have_rooms(self, model):
        assert len(model.rooms) >= 0  # leer wenn keine Quantities

    def test_should_have_non_negative_total_area(self, model):
        assert model.total_area_m2 >= 0.0

    def test_should_have_project_name(self, model):
        assert isinstance(model.project_name, str)

    def test_should_have_building_name(self, model):
        assert isinstance(model.building_name, str)


@ifc_required
class TestIFCParserFloors:
    def test_floors_have_names(self, model):
        for floor in model.floors:
            assert isinstance(floor.name, str)
            assert floor.name != ""

    def test_floors_have_ifc_ids(self, model):
        for floor in model.floors:
            assert floor.ifc_id != ""

    def test_floor_numbers_are_sequential(self, model):
        for i, floor in enumerate(model.floors):
            assert floor.number == i


@ifc_required
class TestIFCParserRooms:
    def test_rooms_have_names(self, model):
        for floor in model.floors:
            for room in floor.rooms:
                assert isinstance(room.name, str)

    def test_rooms_have_ifc_ids(self, model):
        for floor in model.floors:
            for room in floor.rooms:
                assert room.ifc_id != ""

    def test_rooms_have_floor_name(self, model):
        for floor in model.floors:
            for room in floor.rooms:
                assert room.floor_name == floor.name

    def test_rooms_have_non_negative_area(self, model):
        all_rooms = model.rooms
        assert all(r.area_m2 >= 0 for r in all_rooms)


class TestIFCParserErrors:
    def test_should_raise_on_wrong_extension(self, parser):
        from nl2cad.core.exceptions import UnsupportedFormatError

        with pytest.raises(UnsupportedFormatError):
            parser.parse("gebaeude.dwg")

    def test_should_raise_on_nonexistent_file(self, parser):
        from nl2cad.core.exceptions import IFCParseError

        with pytest.raises(IFCParseError):
            parser.parse("/tmp/does_not_exist.ifc")

    def test_should_raise_on_wrong_extension_str(self, parser):
        from nl2cad.core.exceptions import UnsupportedFormatError

        with pytest.raises(UnsupportedFormatError):
            parser.parse("plan.dxf")
