"""
nl2cad.core.models.dxf
======================
Dataclasses für DXF-Domänenobjekte.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DXFEntityType(str, Enum):
    LINE = "LINE"
    LWPOLYLINE = "LWPOLYLINE"
    POLYLINE = "POLYLINE"
    CIRCLE = "CIRCLE"
    ARC = "ARC"
    TEXT = "TEXT"
    MTEXT = "MTEXT"
    INSERT = "INSERT"  # Block-Referenz
    HATCH = "HATCH"
    DIMENSION = "DIMENSION"


class CADCommandType(str, Enum):
    """Bekannte CAD-Befehle für NL2DXF-Generator."""
    LINE = "LINE"
    RECT = "RECT"
    CIRCLE = "CIRCLE"
    ARC = "ARC"
    TEXT = "TEXT"
    DOOR = "DOOR"
    WINDOW = "WINDOW"
    WALL = "WALL"
    ROOM = "ROOM"


@dataclass
class Point2D:
    x: float = 0.0
    y: float = 0.0

    def __iter__(self):
        yield self.x
        yield self.y


@dataclass
class BoundingBox:
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def width_m(self) -> float:
        return abs(self.max_x - self.min_x)

    @property
    def height_m(self) -> float:
        return abs(self.max_y - self.min_y)

    @property
    def area_m2(self) -> float:
        return self.width_m * self.height_m


@dataclass
class DXFLayer:
    """DXF-Layer mit Metadaten."""
    name: str = ""
    color: int = 7
    linetype: str = "CONTINUOUS"
    is_frozen: bool = False
    entity_count: int = 0
    classified_as: str = ""  # room, wall, door, window, etc.


@dataclass
class DXFRoom:
    """Erkannter Raum aus DXF."""
    name: str = ""
    layer: str = ""
    area_m2: float = 0.0
    perimeter_m: float = 0.0
    vertices: list[Point2D] = field(default_factory=list)
    position: Point2D = field(default_factory=Point2D)
    din277_code: str = ""
    din277_category: str = ""
    has_door: bool = False
    has_window: bool = False
    floor: int = 0


@dataclass
class CADCommand:
    """Parsed CAD command (für NL2DXF)."""
    command: CADCommandType | str
    params: dict[str, float | str] = field(default_factory=dict)
    layer: str = "0"


@dataclass
class DXFModel:
    """
    Vollständiges geparses DXF-Modell.
    """
    source_file: str = ""
    dxf_version: str = ""
    units: str = "m"

    layers: list[DXFLayer] = field(default_factory=list)
    rooms: list[DXFRoom] = field(default_factory=list)

    @property
    def total_area_m2(self) -> float:
        return sum(r.area_m2 for r in self.rooms)

    @property
    def layer_names(self) -> list[str]:
        return [layer.name for layer in self.layers]

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "dxf_version": self.dxf_version,
            "room_count": len(self.rooms),
            "total_area_m2": self.total_area_m2,
            "rooms": [
                {
                    "name": r.name,
                    "layer": r.layer,
                    "area_m2": r.area_m2,
                    "perimeter_m": r.perimeter_m,
                    "din277_code": r.din277_code,
                }
                for r in self.rooms
            ],
        }
