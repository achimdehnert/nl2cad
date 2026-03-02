"""
nl2cad.core.exceptions
======================
Alle Exceptions der nl2cad-Library.
"""


class NL2CADError(Exception):
    """Basis-Exception für alle nl2cad Fehler."""


class IFCParseError(NL2CADError):
    """Fehler beim Parsen einer IFC-Datei."""


class DXFParseError(NL2CADError):
    """Fehler beim Parsen einer DXF/DWG-Datei."""


class UnsupportedFormatError(NL2CADError):
    """Dateiformat wird nicht unterstützt."""

    def __init__(
        self, format_: str, supported: list[str] | None = None
    ) -> None:
        supported = supported or [".ifc", ".dxf", ".dwg"]
        super().__init__(
            f"Format '{format_}' nicht unterstützt. "
            f"Unterstützte Formate: {', '.join(supported)}"
        )
        self.format = format_
        self.supported = supported


class HandlerError(NL2CADError):
    """Fehler in einem CAD-Handler."""


class PipelineError(NL2CADError):
    """Fehler in der Handler-Pipeline."""
