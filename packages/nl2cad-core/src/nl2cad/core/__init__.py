"""
nl2cad-core — IFC/DXF Domain Models, Parsers, Handler Pipeline.

Public API:
    from nl2cad.core.models import IFCModel, IFCRoom, DXFModel, DXFRoom
    from nl2cad.core.parsers import IFCParser, DXFParser
    from nl2cad.core.handlers.base import BaseCADHandler, CADHandlerPipeline, HandlerResult
    from nl2cad.core.exceptions import IFCParseError, DXFParseError
    from nl2cad.core.constants import DIN277_CODES
"""

__version__ = "0.1.0"

from nl2cad.core.models import (
    IFCModel,
    IFCFloor,
    IFCRoom,
    IFCWall,
    IFCDoor,
    IFCWindow,
    IFCSlab,
    DXFModel,
    DXFLayer,
    DXFRoom,
    CADCommand,
    CADCommandType,
    Point2D,
    BoundingBox,
)
from nl2cad.core.parsers import IFCParser, DXFParser
from nl2cad.core.handlers.base import (
    BaseCADHandler,
    CADHandlerPipeline,
    HandlerResult,
    HandlerStatus,
)
from nl2cad.core.exceptions import (
    NL2CADError,
    IFCParseError,
    DXFParseError,
    UnsupportedFormatError,
    HandlerError,
    PipelineError,
)

__all__ = [
    "__version__",
    # Models - IFC
    "IFCModel", "IFCFloor", "IFCRoom", "IFCWall",
    "IFCDoor", "IFCWindow", "IFCSlab",
    # Models - DXF
    "DXFModel", "DXFLayer", "DXFRoom",
    "CADCommand", "CADCommandType", "Point2D", "BoundingBox",
    # Parsers
    "IFCParser", "DXFParser",
    # Handlers
    "BaseCADHandler", "CADHandlerPipeline", "HandlerResult", "HandlerStatus",
    # Exceptions
    "NL2CADError", "IFCParseError", "DXFParseError",
    "UnsupportedFormatError", "HandlerError", "PipelineError",
]
