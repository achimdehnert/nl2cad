"""
nl2cad.core.models.ifc
======================
Dataclasses für IFC-Domänenobjekte.
Kein Django, kein Pydantic — reine stdlib dataclasses.
Alle Maß-Felder tragen Einheits-Suffix (_m2, _m, _m3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class IFCElementType(StrEnum):
    ROOM = "IfcSpace"
    WALL = "IfcWall"
    DOOR = "IfcDoor"
    WINDOW = "IfcWindow"
    SLAB = "IfcSlab"
    STAIR = "IfcStair"
    ROOF = "IfcRoof"
    COLUMN = "IfcColumn"
    BEAM = "IfcBeam"


@dataclass
class IFCRoom:
    """Raum/Space aus IFC (IfcSpace)."""

    ifc_id: str = ""
    name: str = ""
    long_name: str = ""
    number: str = ""
    area_m2: float = 0.0
    perimeter_m: float = 0.0
    height_m: float = 0.0
    volume_m3: float = 0.0
    floor_name: str = ""
    floor_number: int = 0
    floor_guid: str = ""  # GlobalId des IfcBuildingStorey
    din277_code: str = ""
    din277_category: str = ""
    usage_category: str = ""  # DIN 277 usage code (NF1.1, NF2, VF8, ...)
    properties: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class IFCWall:
    """Wand aus IFC (IfcWall / IfcWallStandardCase)."""

    ifc_id: str = ""
    name: str = ""
    area_m2: float = 0.0
    gross_area_m2: float = 0.0
    net_area_m2: float = 0.0
    length_m: float = 0.0
    height_m: float = 0.0
    thickness_m: float = 0.0
    volume_m3: float = 0.0
    is_external: bool = False
    is_load_bearing: bool = False
    fire_rating: str = ""
    material: str = ""
    floor_guid: str = ""
    properties: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class IFCDoor:
    """Tür aus IFC (IfcDoor)."""

    ifc_id: str = ""
    name: str = ""
    number: str = ""
    width_m: float = 0.0
    height_m: float = 0.0
    fire_rating: str = ""  # T30, T60, T90
    is_fire_door: bool = False
    opening_direction: str = ""
    door_type: str = ""  # Standard, Brandschutz, ...
    material: str = ""
    floor_guid: str = ""
    properties: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class IFCWindow:
    """Fenster aus IFC (IfcWindow)."""

    ifc_id: str = ""
    name: str = ""
    number: str = ""
    width_m: float = 0.0
    height_m: float = 0.0
    area_m2: float = 0.0
    material: str = ""
    u_value_wm2k: float | None = None  # Wärmedurchgangskoeffizient W/(m²K)
    floor_guid: str = ""
    properties: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class IFCSlab:
    """Decke/Boden aus IFC (IfcSlab)."""

    ifc_id: str = ""
    name: str = ""
    area_m2: float = 0.0
    thickness_m: float = 0.0
    volume_m3: float = 0.0
    perimeter_m: float = 0.0
    fire_rating: str = ""
    slab_type: str = "FLOOR"  # FLOOR, ROOF, BASESLAB
    material: str = ""
    floor_guid: str = ""
    properties: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class IFCFloor:
    """Geschoss (IfcBuildingStorey)."""

    ifc_id: str = ""
    name: str = ""
    elevation_m: float = 0.0
    number: int = 0
    rooms: list[IFCRoom] = field(default_factory=list)
    walls: list[IFCWall] = field(default_factory=list)
    doors: list[IFCDoor] = field(default_factory=list)
    windows: list[IFCWindow] = field(default_factory=list)
    slabs: list[IFCSlab] = field(default_factory=list)


@dataclass
class IFCModel:
    """
    Vollständiges geparses IFC-Modell.
    Einstiegspunkt für alle weiteren Analysen.
    """

    project_name: str = ""
    project_description: str = ""
    site_name: str = ""
    building_name: str = ""
    source_file: str = ""
    schema: str = ""  # IFC2X3, IFC4, IFC4X3

    floors: list[IFCFloor] = field(default_factory=list)

    # Flat lists für einfachen Zugriff
    @property
    def rooms(self) -> list[IFCRoom]:
        return [r for f in self.floors for r in f.rooms]

    @property
    def walls(self) -> list[IFCWall]:
        return [w for f in self.floors for w in f.walls]

    @property
    def doors(self) -> list[IFCDoor]:
        return [d for f in self.floors for d in f.doors]

    @property
    def windows(self) -> list[IFCWindow]:
        return [w for f in self.floors for w in f.windows]

    @property
    def slabs(self) -> list[IFCSlab]:
        return [s for f in self.floors for s in f.slabs]

    @property
    def total_area_m2(self) -> float:
        return sum(r.area_m2 for r in self.rooms)

    @property
    def floor_count(self) -> int:
        return len(self.floors)

    def to_dict(self) -> dict:
        """Serialisierung für Downstream-Verarbeitung (z.B. GAEB-Converter)."""
        return {
            "project_name": self.project_name,
            "total_area_m2": self.total_area_m2,
            "floor_count": self.floor_count,
            "rooms": [
                {
                    "name": r.name,
                    "number": r.number,
                    "area_m2": r.area_m2,
                    "perimeter_m": r.perimeter_m,
                    "height_m": r.height_m,
                    "din277_code": r.din277_code,
                    "usage_category": r.usage_category,
                    "floor_name": r.floor_name,
                    "floor_guid": r.floor_guid,
                }
                for r in self.rooms
            ],
            "walls": [
                {
                    "name": w.name,
                    "area_m2": w.area_m2,
                    "length_m": w.length_m,
                    "height_m": w.height_m,
                    "thickness_m": w.thickness_m,
                    "is_external": w.is_external,
                    "is_load_bearing": w.is_load_bearing,
                    "fire_rating": w.fire_rating,
                    "material": w.material,
                    "floor_guid": w.floor_guid,
                }
                for w in self.walls
            ],
            "doors": [
                {
                    "name": d.name,
                    "width_m": d.width_m,
                    "height_m": d.height_m,
                    "fire_rating": d.fire_rating,
                    "is_fire_door": d.is_fire_door,
                    "door_type": d.door_type,
                    "material": d.material,
                    "floor_guid": d.floor_guid,
                }
                for d in self.doors
            ],
            "windows": [
                {
                    "name": w.name,
                    "width_m": w.width_m,
                    "height_m": w.height_m,
                    "area_m2": w.area_m2,
                    "material": w.material,
                    "u_value_wm2k": w.u_value_wm2k,
                    "floor_guid": w.floor_guid,
                }
                for w in self.windows
            ],
            "slabs": [
                {
                    "name": s.name,
                    "area_m2": s.area_m2,
                    "thickness_m": s.thickness_m,
                    "fire_rating": s.fire_rating,
                    "slab_type": s.slab_type,
                    "material": s.material,
                    "floor_guid": s.floor_guid,
                }
                for s in self.slabs
            ],
        }
