"""
Tests fuer nl2cad.core.handlers.file_input.FileInputHandler.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from nl2cad.core.handlers.file_input import FileInputHandler
from nl2cad.core.models.dxf import DXFModel
from nl2cad.core.models.ifc import IFCModel


@pytest.fixture
def handler() -> FileInputHandler:
    return FileInputHandler()


class TestFileInputHandlerFormat:
    def test_should_detect_ifc_format(self, handler):
        mock_model = IFCModel(source_file="test.ifc")
        with patch("nl2cad.core.handlers.file_input.IFCParser") as MockParser:
            MockParser.return_value.parse_bytes.return_value = mock_model
            result = handler.run(
                {
                    "file_content": b"fake ifc",
                    "filename": "gebaeude.ifc",
                }
            )
        assert result.success
        assert result.data["format"] == "ifc"
        assert "ifc_model" in result.data

    def test_should_detect_dxf_format(self, handler):
        mock_model = DXFModel(source_file="test.dxf")
        with patch("nl2cad.core.handlers.file_input.DXFParser") as MockParser:
            MockParser.return_value.parse_bytes.return_value = mock_model
            result = handler.run(
                {
                    "file_content": b"fake dxf",
                    "filename": "grundriss.dxf",
                }
            )
        assert result.success
        assert result.data["format"] == "dxf"
        assert "dxf_model" in result.data

    def test_should_fail_on_unsupported_format(self, handler):
        result = handler.run(
            {
                "file_content": b"data",
                "filename": "dokument.pdf",
            }
        )
        assert not result.success
        assert any("pdf" in e.lower() for e in result.errors)

    def test_should_fail_when_no_input(self, handler):
        result = handler.run({})
        assert not result.success
        assert len(result.errors) > 0

    def test_should_set_source_file_from_filename(self, handler):
        mock_model = IFCModel(source_file="test.ifc")
        with patch("nl2cad.core.handlers.file_input.IFCParser") as MockParser:
            MockParser.return_value.parse_bytes.return_value = mock_model
            result = handler.run(
                {
                    "file_content": b"fake ifc",
                    "filename": "projekt.ifc",
                }
            )
        assert result.data["source_file"] == "projekt.ifc"

    def test_should_use_file_path_when_provided(self, handler):
        mock_model = DXFModel(source_file="plan.dxf")
        with patch("nl2cad.core.handlers.file_input.DXFParser") as MockParser:
            MockParser.return_value.parse.return_value = mock_model
            result = handler.run({"file_path": "plan.dxf"})
        assert result.data["format"] == "dxf"

    def test_should_fail_on_dwg_extension(self, handler):
        result = handler.run(
            {
                "file_content": b"dwg data",
                "filename": "plan.dwg",
            }
        )
        assert not result.success

    def test_should_fail_when_parser_raises(self, handler):
        with patch("nl2cad.core.handlers.file_input.DXFParser") as MockParser:
            MockParser.return_value.parse_bytes.side_effect = Exception(
                "parse error"
            )
            result = handler.run(
                {
                    "file_content": b"broken dxf",
                    "filename": "broken.dxf",
                }
            )
        assert not result.success
        assert any("parse error" in e for e in result.errors)


class TestFileInputHandlerPipeline:
    def test_should_integrate_in_pipeline(self, handler):
        from nl2cad.core.handlers.base import CADHandlerPipeline

        mock_model = IFCModel(source_file="test.ifc")
        with patch("nl2cad.core.handlers.file_input.IFCParser") as MockParser:
            MockParser.return_value.parse_bytes.return_value = mock_model
            pipeline = CADHandlerPipeline()
            pipeline.add(handler)
            pipeline.run(
                {
                    "file_content": b"fake ifc",
                    "filename": "test.ifc",
                }
            )
        ctx = pipeline.get_context()
        assert ctx.get("format") == "ifc"
        assert "ifc_model" in ctx
