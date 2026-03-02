"""
Tests fuer nl2cad.core.parsers.dxf_parser.DXFParser
mit echter .dxf-Fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DXF = Path(__file__).parent / "fixtures" / "minimal.dxf"


@pytest.fixture
def parser():
    from nl2cad.core.parsers.dxf_parser import DXFParser

    return DXFParser()


@pytest.fixture
def model(parser):
    return parser.parse(FIXTURE_DXF)


class TestDXFParserBasic:
    def test_should_parse_without_error(self, model):
        assert model is not None

    def test_should_return_dxf_model(self, model):
        from nl2cad.core.models.dxf import DXFModel

        assert isinstance(model, DXFModel)

    def test_should_set_source_file(self, model):
        assert "minimal.dxf" in model.source_file

    def test_should_have_dxf_version(self, model):
        assert model.dxf_version != ""

    def test_should_have_layers(self, model):
        assert len(model.layers) > 0

    def test_total_area_is_non_negative(self, model):
        assert model.total_area_m2 >= 0.0


class TestDXFParserLayers:
    def test_layers_have_names(self, model):
        for layer in model.layers:
            assert isinstance(layer.name, str)
            assert layer.name != ""

    def test_layer_0_excluded(self, model):
        names = [layer.name for layer in model.layers]
        assert "0" not in names

    def test_layers_have_color(self, model):
        for layer in model.layers:
            assert isinstance(layer.color, int)


class TestDXFParserGeometry:
    def test_polygon_area_shoelace(self, parser):
        from nl2cad.core.models.dxf import Point2D

        square = [
            Point2D(0.0, 0.0),
            Point2D(4.0, 0.0),
            Point2D(4.0, 4.0),
            Point2D(0.0, 4.0),
        ]
        area = parser._calculate_polygon_area(square)
        assert abs(area - 16.0) < 0.001

    def test_polygon_perimeter(self, parser):
        from nl2cad.core.models.dxf import Point2D

        square = [
            Point2D(0.0, 0.0),
            Point2D(3.0, 0.0),
            Point2D(3.0, 3.0),
            Point2D(0.0, 3.0),
        ]
        perimeter = parser._calculate_perimeter(square)
        assert abs(perimeter - 12.0) < 0.001

    def test_centroid_of_square(self, parser):
        from nl2cad.core.models.dxf import Point2D

        square = [
            Point2D(0.0, 0.0),
            Point2D(2.0, 0.0),
            Point2D(2.0, 2.0),
            Point2D(0.0, 2.0),
        ]
        centroid = parser._calculate_centroid(square)
        assert abs(centroid.x - 1.0) < 0.001
        assert abs(centroid.y - 1.0) < 0.001

    def test_point_in_polygon(self, parser):
        from nl2cad.core.models.dxf import Point2D

        square = [
            Point2D(0.0, 0.0),
            Point2D(4.0, 0.0),
            Point2D(4.0, 4.0),
            Point2D(0.0, 4.0),
        ]
        assert parser._point_in_polygon(Point2D(2.0, 2.0), square) is True
        assert parser._point_in_polygon(Point2D(5.0, 5.0), square) is False

    def test_bounding_box(self, parser):
        from nl2cad.core.models.dxf import Point2D

        pts = [Point2D(1.0, 2.0), Point2D(3.0, 4.0), Point2D(0.0, 5.0)]
        bb = parser._get_bounding_box(pts)
        assert bb.min_x == 0.0
        assert bb.max_y == 5.0


class TestDXFParserErrors:
    def test_should_raise_on_wrong_extension(self, parser):
        from nl2cad.core.exceptions import UnsupportedFormatError

        with pytest.raises(UnsupportedFormatError):
            parser.parse("plan.ifc")

    def test_should_raise_on_nonexistent_file(self, parser):
        from nl2cad.core.exceptions import DXFParseError

        with pytest.raises(DXFParseError):
            parser.parse("/tmp/does_not_exist.dxf")

    def test_should_raise_on_dwg_extension(self, parser):
        from nl2cad.core.exceptions import UnsupportedFormatError

        with pytest.raises(UnsupportedFormatError):
            parser.parse("plan.dwg")
