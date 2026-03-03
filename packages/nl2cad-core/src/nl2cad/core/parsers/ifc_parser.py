"""
nl2cad.core.parsers.ifc_parser
===============================
ifcopenshell-Wrapper. Konvertiert IFC-Dateien → IFCModel Dataclasses.
"""

from __future__ import annotations

import logging
from pathlib import Path

from nl2cad.core.constants import ROOM_KEYWORD_TO_DIN277
from nl2cad.core.exceptions import IFCParseError, UnsupportedFormatError
from nl2cad.core.models.ifc import (
    IFCDoor,
    IFCFloor,
    IFCModel,
    IFCRoom,
    IFCSlab,
    IFCWall,
    IFCWindow,
)

logger = logging.getLogger(__name__)


class IFCParser:
    """
    Parst IFC-Dateien mit ifcopenshell und gibt IFCModel zurück.

    Usage:
        parser = IFCParser()
        model = parser.parse("gebaeude.ifc")
        print(f"{len(model.rooms)} Räume, {model.total_area_m2:.1f} m²")

    Parser unterstützt: IFC2X3, IFC4, IFC4X3
    """

    def parse(self, path: str | Path) -> IFCModel:
        """
        Parst IFC-Datei und gibt IFCModel zurück.

        Args:
            path: Pfad zur .ifc Datei

        Returns:
            IFCModel mit allen extrahierten Elementen

        Raises:
            UnsupportedFormatError: Dateiendung ist nicht .ifc
            IFCParseError: Datei konnte nicht gelesen werden
        """
        path = Path(path)
        if path.suffix.lower() != ".ifc":
            raise UnsupportedFormatError(path.suffix, [".ifc"])

        try:
            import ifcopenshell
        except ImportError as e:
            raise IFCParseError("ifcopenshell nicht installiert") from e

        logger.info("[IFCParser] Parsing %s", path.name)

        try:
            ifc_file = ifcopenshell.open(str(path))
        except Exception as e:
            raise IFCParseError(
                f"Konnte IFC-Datei nicht öffnen: {path.name}"
            ) from e

        model = IFCModel(source_file=str(path))

        try:
            model = self._extract_project_info(ifc_file, model)
            model.floors = self._extract_floors(ifc_file)
        except Exception as e:
            raise IFCParseError(f"Fehler beim Parsen: {e}") from e

        logger.info(
            "[IFCParser] %s: %d Räume, %.1f m²",
            path.name,
            len(model.rooms),
            model.total_area_m2,
        )
        return model

    def parse_bytes(
        self, content: bytes, filename: str = "upload.ifc"
    ) -> IFCModel:
        """Parst IFC aus Bytes (z.B. Django File Upload)."""
        import os
        import tempfile

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".ifc", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            return self.parse(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Private Methoden
    # ------------------------------------------------------------------

    def _extract_project_info(self, ifc_file, model: IFCModel) -> IFCModel:
        """Extrahiert Projekt-, Site- und Building-Informationen."""
        projects = ifc_file.by_type("IfcProject")
        if projects:
            p = projects[0]
            model.project_name = getattr(p, "Name", "") or ""
            model.project_description = getattr(p, "Description", "") or ""
            model.schema = ifc_file.schema

        sites = ifc_file.by_type("IfcSite")
        if sites:
            model.site_name = getattr(sites[0], "Name", "") or ""

        buildings = ifc_file.by_type("IfcBuilding")
        if buildings:
            model.building_name = getattr(buildings[0], "Name", "") or ""

        return model

    def _extract_floors(self, ifc_file) -> list[IFCFloor]:
        """Extrahiert alle Geschosse mit ihren Elementen."""
        floors: list[IFCFloor] = []

        storeys = ifc_file.by_type("IfcBuildingStorey")
        for i, storey in enumerate(storeys):
            floor = IFCFloor(
                ifc_id=str(storey.GlobalId),
                name=getattr(storey, "Name", f"EG+{i}") or f"Geschoss {i}",
                elevation_m=self._get_elevation(storey),
                number=i,
            )

            floor.rooms = self._extract_rooms(ifc_file, storey, floor.name)
            floor.walls = self._extract_walls(ifc_file, storey)
            floor.doors = self._extract_doors(ifc_file, storey)
            floor.windows = self._extract_windows(ifc_file, storey)
            floor.slabs = self._extract_slabs(ifc_file, storey)

            floors.append(floor)

        if not floors:
            floors = self._extract_without_storeys(ifc_file)

        return floors

    def _extract_rooms(
        self, ifc_file, storey, floor_name: str
    ) -> list[IFCRoom]:
        """Extrahiert IfcSpace-Elemente."""
        rooms: list[IFCRoom] = []

        try:
            import ifcopenshell.util.element as ifc_util

            spaces = [
                el
                for el in ifc_util.get_decomposition(storey)
                if el.is_a("IfcSpace")
            ]
        except Exception as e:
            logger.debug(
                "[IFCParser] get_decomposition fehlgeschlagen, Fallback: %s", e
            )
            spaces = ifc_file.by_type("IfcSpace")

        floor_guid = str(storey.GlobalId)
        for space in spaces:
            room = IFCRoom(
                ifc_id=str(space.GlobalId),
                name=getattr(space, "Name", "") or "",
                long_name=getattr(space, "LongName", "") or "",
                number=str(getattr(space, "Number", "") or ""),
                floor_name=floor_name,
                floor_guid=floor_guid,
            )
            room.area_m2, room.perimeter_m, room.height_m, room.volume_m3 = (
                self._get_space_quantities(space)
            )
            room.usage_category = self._classify_room_usage(room.name)
            room.properties = self._get_properties(space)
            rooms.append(room)

        return rooms

    def _extract_walls(self, ifc_file, storey) -> list[IFCWall]:
        """Extrahiert IfcWall-Elemente."""
        walls: list[IFCWall] = []
        try:
            import ifcopenshell.util.element as ifc_util

            wall_elements = [
                el
                for el in ifc_util.get_decomposition(storey)
                if el.is_a("IfcWall") or el.is_a("IfcWallStandardCase")
            ]
        except Exception:
            wall_elements = ifc_file.by_type("IfcWall")

        floor_guid = str(storey.GlobalId)
        for w in wall_elements:
            wall = IFCWall(
                ifc_id=str(w.GlobalId),
                name=getattr(w, "Name", "") or "",
                floor_guid=floor_guid,
            )
            wall.properties = self._get_properties(w)
            wall.fire_rating = str(wall.properties.get("FireRating", "") or "")
            wall.is_external = bool(wall.properties.get("IsExternal", False))
            wall.is_load_bearing = bool(wall.properties.get("LoadBearing", False))
            wall.material = str(wall.properties.get("Material", "") or "")
            (
                wall.length_m, wall.height_m, wall.thickness_m,
                wall.gross_area_m2, wall.net_area_m2, wall.volume_m3,
            ) = self._get_wall_quantities(w)
            walls.append(wall)

        return walls

    def _extract_doors(self, ifc_file, storey) -> list[IFCDoor]:
        """Extrahiert IfcDoor-Elemente inkl. Brandschutztüren."""
        doors: list[IFCDoor] = []
        try:
            import ifcopenshell.util.element as ifc_util

            door_elements = [
                el
                for el in ifc_util.get_decomposition(storey)
                if el.is_a("IfcDoor")
            ]
        except Exception:
            door_elements = ifc_file.by_type("IfcDoor")

        floor_guid = str(storey.GlobalId)
        for d in door_elements:
            door = IFCDoor(
                ifc_id=str(d.GlobalId),
                name=getattr(d, "Name", "") or "",
                number=self._get_element_number(d),
                width_m=getattr(d, "OverallWidth", 0.0) or 0.0,
                height_m=getattr(d, "OverallHeight", 0.0) or 0.0,
                floor_guid=floor_guid,
            )
            door.properties = self._get_properties(d)
            fire_rating = door.properties.get("FireRating", "")
            door.fire_rating = str(fire_rating) if fire_rating else ""
            door.is_fire_door = bool(door.fire_rating)
            door.door_type = "Brandschutz" if door.is_fire_door else "Standard"
            door.material = str(door.properties.get("Material", "") or "")
            doors.append(door)

        return doors

    def _extract_windows(self, ifc_file, storey) -> list[IFCWindow]:
        """Extrahiert IfcWindow-Elemente."""
        windows: list[IFCWindow] = []
        try:
            import ifcopenshell.util.element as ifc_util

            win_elements = [
                el
                for el in ifc_util.get_decomposition(storey)
                if el.is_a("IfcWindow")
            ]
        except Exception:
            win_elements = ifc_file.by_type("IfcWindow")

        floor_guid = str(storey.GlobalId)
        for w in win_elements:
            win = IFCWindow(
                ifc_id=str(w.GlobalId),
                name=getattr(w, "Name", "") or "",
                number=self._get_element_number(w),
                width_m=getattr(w, "OverallWidth", 0.0) or 0.0,
                height_m=getattr(w, "OverallHeight", 0.0) or 0.0,
                floor_guid=floor_guid,
            )
            win.area_m2 = win.width_m * win.height_m
            win.properties = self._get_properties(w)
            win.material = str(win.properties.get("Material", "") or "")
            u_raw = win.properties.get("ThermalTransmittance")
            if u_raw is not None:
                try:
                    win.u_value_wm2k = float(u_raw)
                except (TypeError, ValueError):
                    pass
            windows.append(win)

        return windows

    def _extract_slabs(self, ifc_file, storey) -> list[IFCSlab]:
        """Extrahiert IfcSlab-Elemente."""
        slabs: list[IFCSlab] = []
        try:
            import ifcopenshell.util.element as ifc_util

            slab_elements = [
                el
                for el in ifc_util.get_decomposition(storey)
                if el.is_a("IfcSlab")
            ]
        except Exception:
            slab_elements = ifc_file.by_type("IfcSlab")

        floor_guid = str(storey.GlobalId)
        for s in slab_elements:
            slab = IFCSlab(
                ifc_id=str(s.GlobalId),
                name=getattr(s, "Name", "") or "",
                floor_guid=floor_guid,
            )
            slab.properties = self._get_properties(s)
            slab.material = str(slab.properties.get("Material", "") or "")
            (
                slab.area_m2, slab.thickness_m,
                slab.volume_m3, slab.perimeter_m,
            ) = self._get_slab_quantities(s)
            slabs.append(slab)

        return slabs

    def _extract_without_storeys(self, ifc_file) -> list[IFCFloor]:
        """Fallback: Alle Räume in ein EG-Geschoss."""
        floor = IFCFloor(name="EG", number=0)
        for space in ifc_file.by_type("IfcSpace"):
            room = IFCRoom(
                ifc_id=str(space.GlobalId),
                name=getattr(space, "Name", "") or "",
                floor_name="EG",
            )
            room.area_m2, room.perimeter_m, room.height_m, room.volume_m3 = (
                self._get_space_quantities(space)
            )
            room.usage_category = self._classify_room_usage(room.name)
            floor.rooms.append(room)
        return [floor]

    def _get_space_quantities(self, space) -> tuple[float, float, float, float]:
        """Extrahiert Fläche, Umfang, Höhe und Volumen aus IfcSpace Quantities."""
        area_m2 = perimeter_m = height_m = volume_m3 = 0.0
        try:
            for rel in space.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcElementQuantity"):
                        for q in prop_set.Quantities:
                            name = q.Name.lower() if q.Name else ""
                            if "area" in name or "fläche" in name:
                                area_m2 = float(q.AreaValue or 0)
                            elif "perimeter" in name or "umfang" in name:
                                perimeter_m = float(q.LengthValue or 0)
                            elif "height" in name or "höhe" in name:
                                height_m = float(q.LengthValue or 0)
                            elif "volume" in name or "volumen" in name:
                                volume_m3 = float(q.VolumeValue or 0)
        except Exception:
            pass
        return area_m2, perimeter_m, height_m, volume_m3

    def _get_wall_quantities(
        self, wall
    ) -> tuple[float, float, float, float, float, float]:
        """Extrahiert Länge, Höhe, Dicke, Bruttofläche, Nettofläche, Volumen."""
        length_m = height_m = thickness_m = 0.0
        gross_area_m2 = net_area_m2 = volume_m3 = 0.0
        try:
            for rel in wall.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcElementQuantity"):
                        for q in prop_set.Quantities:
                            name = q.Name.lower() if q.Name else ""
                            if "length" in name or "länge" in name:
                                length_m = float(q.LengthValue or 0)
                            elif "height" in name or "höhe" in name:
                                height_m = float(q.LengthValue or 0)
                            elif "width" in name or "breite" in name or "thickness" in name:
                                thickness_m = float(q.LengthValue or 0)
                            elif "grossarea" in name.replace("_", "") or "grossfl" in name:
                                gross_area_m2 = float(q.AreaValue or 0)
                            elif "netarea" in name.replace("_", "") or "nettofl" in name:
                                net_area_m2 = float(q.AreaValue or 0)
                            elif "volume" in name:
                                volume_m3 = float(q.VolumeValue or 0)
        except Exception:
            pass
        return length_m, height_m, thickness_m, gross_area_m2, net_area_m2, volume_m3

    def _get_slab_quantities(self, slab) -> tuple[float, float, float, float]:
        """Extrahiert Fläche, Dicke, Volumen, Umfang aus IfcSlab."""
        area_m2 = thickness_m = volume_m3 = perimeter_m = 0.0
        try:
            for rel in slab.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcElementQuantity"):
                        for q in prop_set.Quantities:
                            name = q.Name.lower() if q.Name else ""
                            if "area" in name:
                                area_m2 = float(q.AreaValue or 0)
                            elif "thickness" in name or "dicke" in name:
                                thickness_m = float(q.LengthValue or 0)
                            elif "volume" in name:
                                volume_m3 = float(q.VolumeValue or 0)
                            elif "perimeter" in name:
                                perimeter_m = float(q.LengthValue or 0)
        except Exception:
            pass
        return area_m2, thickness_m, volume_m3, perimeter_m

    def _get_element_number(self, element) -> str:
        """Extrahiert Element-Nummer aus Tag/Name."""
        tag = getattr(element, "Tag", None)
        if tag:
            return str(tag)
        name = getattr(element, "Name", "") or ""
        parts = name.split()
        return parts[0] if parts else ""

    def _classify_room_usage(self, room_name: str) -> str:
        """Klassifiziert Raum nach DIN 277 usage_category aus Raumname."""
        name_lower = room_name.lower()
        for keyword, code in ROOM_KEYWORD_TO_DIN277.items():
            if keyword in name_lower:
                return code
        return ""

    def _get_properties(self, element) -> dict:
        """Extrahiert alle Properties eines IFC-Elements."""
        props: dict[str, str | float | bool] = {}
        try:
            for rel in element.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    prop_set = rel.RelatingPropertyDefinition
                    if prop_set.is_a("IfcPropertySet"):
                        for p in prop_set.HasProperties:
                            if hasattr(p, "NominalValue") and p.NominalValue:
                                props[p.Name] = p.NominalValue.wrappedValue
        except Exception:
            pass
        return props

    def _get_elevation(self, storey) -> float:
        """Extrahiert Geschoss-Höhe aus Placement."""
        try:
            placement = storey.ObjectPlacement
            if placement and placement.RelativePlacement:
                loc = placement.RelativePlacement.Location
                if loc and loc.Coordinates:
                    return float(loc.Coordinates[2])
        except Exception:
            pass
        return 0.0
