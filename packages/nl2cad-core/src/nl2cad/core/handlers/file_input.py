"""
nl2cad.core.handlers.file_input
================================
FileInputHandler — Format-Erkennung, delegiert an IFCParser/DXFParser.

Eingabe:  file_path (str|Path) ODER (file_content: bytes + filename: str)
Ausgabe:  context["format"] = "ifc"|"dxf"
          context["source_file"] = str
          context["ifc_model"] = IFCModel  (nur bei IFC)
          context["dxf_model"] = DXFModel  (nur bei DXF)
"""

from __future__ import annotations

import logging
from pathlib import Path

from nl2cad.core.exceptions import UnsupportedFormatError
from nl2cad.core.handlers.base import (
    BaseCADHandler,
    HandlerResult,
    HandlerStatus,
)
from nl2cad.core.parsers.dxf_parser import DXFParser
from nl2cad.core.parsers.ifc_parser import IFCParser

logger = logging.getLogger(__name__)

_SUPPORTED = {".ifc": "ifc", ".dxf": "dxf"}


class FileInputHandler(BaseCADHandler):
    """
    Erkennt IFC oder DXF, parst die Datei und legt das Model in den Context.

    Eingabe (eine der beiden Varianten):
        input_data["file_path"]   — Pfad zur Datei auf dem Filesystem
        input_data["file_content"] + input_data["filename"]  — Bytes

    Ausgabe im HandlerResult.data:
        "format"      — "ifc" oder "dxf"
        "source_file" — Dateiname/-pfad als str
        "ifc_model"   — IFCModel (nur bei IFC)
        "dxf_model"   — DXFModel (nur bei DXF)
    """

    name = "FileInputHandler"
    description = "Dateiformat-Erkennung und Parsing (IFC/DXF)"
    required_inputs: list[str] = []
    optional_inputs: list[str] = ["file_path", "file_content", "filename"]

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name)

        file_path = input_data.get("file_path")
        file_content = input_data.get("file_content")
        filename = input_data.get("filename", "")

        if file_path is None and file_content is None:
            result.add_error("Weder file_path noch file_content angegeben")
            return result

        suffix = Path(str(file_path or filename)).suffix.lower()
        fmt = _SUPPORTED.get(suffix)

        if fmt is None:
            result.add_error(
                f"Nicht unterstuetztes Format: '{suffix}' — "
                f"erwartet: {list(_SUPPORTED)}"
            )
            result.status = HandlerStatus.ERROR
            return result

        source = str(file_path or filename)
        result.data["format"] = fmt
        result.data["source_file"] = source

        if fmt == "ifc":
            self._parse_ifc(result, file_path, file_content, source)
        else:
            self._parse_dxf(result, file_path, file_content, source)

        if result.success:
            result.status = HandlerStatus.SUCCESS
            logger.info(
                "[FileInputHandler] %s geparst — format=%s", source, fmt
            )

        return result

    def _parse_ifc(
        self,
        result: HandlerResult,
        file_path: object,
        file_content: bytes | None,
        source: str,
    ) -> None:
        try:
            parser = IFCParser()
            if file_content is not None:
                model = parser.parse_bytes(file_content, filename=source)
            else:
                model = parser.parse(file_path)  # type: ignore[arg-type]
            result.data["ifc_model"] = model
        except UnsupportedFormatError:
            raise
        except Exception as exc:
            result.add_error(f"IFC-Parsing fehlgeschlagen: {exc}")

    def _parse_dxf(
        self,
        result: HandlerResult,
        file_path: object,
        file_content: bytes | None,
        source: str,
    ) -> None:
        try:
            parser = DXFParser()
            if file_content is not None:
                model = parser.parse_bytes(file_content)
            else:
                model = parser.parse(file_path)  # type: ignore[arg-type]
            result.data["dxf_model"] = model
        except UnsupportedFormatError:
            raise
        except Exception as exc:
            result.add_error(f"DXF-Parsing fehlgeschlagen: {exc}")
