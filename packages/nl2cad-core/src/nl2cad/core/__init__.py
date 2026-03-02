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

from nl2cad.core.exceptions import (
    DXFParseError,
    HandlerError,
    IFCParseError,
    NL2CADError,
    PipelineError,
    UnsupportedFormatError,
)
from nl2cad.core.handlers.base import (
    BaseCADHandler,
    CADHandlerPipeline,
    HandlerResult,
    HandlerStatus,
)
from nl2cad.core.handlers.file_input import FileInputHandler
from nl2cad.core.handlers.ifc_quality import IFCQualityHandler
from nl2cad.core.handlers.massen import MassenHandler
from nl2cad.core.models import (
    BoundingBox,
    CADCommand,
    CADCommandType,
    DXFLayer,
    DXFModel,
    DXFRoom,
    IFCDoor,
    IFCFloor,
    IFCModel,
    IFCRoom,
    IFCSlab,
    IFCWall,
    IFCWindow,
    Point2D,
)
from nl2cad.core.parsers import DXFParser, IFCParser
from nl2cad.core.quality import (
    IFCQualityChecker,
    IFCQualityIssue,
    IFCQualityReport,
)

__all__ = [
    "__version__",
    # Models - IFC
    "IFCModel",
    "IFCFloor",
    "IFCRoom",
    "IFCWall",
    "IFCDoor",
    "IFCWindow",
    "IFCSlab",
    # Models - DXF
    "DXFModel",
    "DXFLayer",
    "DXFRoom",
    "CADCommand",
    "CADCommandType",
    "Point2D",
    "BoundingBox",
    # Parsers
    "IFCParser",
    "DXFParser",
    # Handlers
    "BaseCADHandler",
    "CADHandlerPipeline",
    "HandlerResult",
    "HandlerStatus",
    "FileInputHandler",
    "MassenHandler",
    # Exceptions
    "NL2CADError",
    "IFCParseError",
    "DXFParseError",
    "UnsupportedFormatError",
    "HandlerError",
    "PipelineError",
    # Quality + Handler (FIX B-03: gehoert in core, nicht brandschutz)
    "IFCQualityChecker",
    "IFCQualityReport",
    "IFCQualityIssue",
    "IFCQualityHandler",
]
