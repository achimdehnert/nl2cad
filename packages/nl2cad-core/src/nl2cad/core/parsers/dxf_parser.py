"""
nl2cad.core.parsers.dxf_parser
================================
ezdxf-Wrapper. Konvertiert DXF-Dateien → DXFModel Dataclasses.
Unterstützt: DXF R12 bis R2018, DWG via Konvertierung.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from nl2cad.core.constants import EXCLUDED_LAYER_KEYWORDS
from nl2cad.core.exceptions import DXFParseError, UnsupportedFormatError
from nl2cad.core.models.dxf import (
    BoundingBox,
    DXFLayer,
    DXFModel,
    DXFRoom,
    Point2D,
)

logger = logging.getLogger(__name__)


class DXFParser:
    """
    Parst DXF-Dateien mit ezdxf und gibt DXFModel zurück.

    Usage:
        parser = DXFParser()
        model = parser.parse("grundriss.dxf")
        for room in model.rooms:
            print(f"{room.name}: {room.area_m2:.1f} m²")
    """

    def parse(self, path: str | Path) -> DXFModel:
        """
        Parst DXF-Datei und gibt DXFModel zurück.

        Args:
            path: Pfad zur .dxf Datei

        Returns:
            DXFModel mit allen extrahierten Elementen

        Raises:
            UnsupportedFormatError: Nicht .dxf
            DXFParseError: Datei konnte nicht gelesen werden
        """
        path = Path(path)
        if path.suffix.lower() not in (".dxf",):
            raise UnsupportedFormatError(path.suffix, [".dxf"])

        try:
            import ezdxf
        except ImportError as e:
            raise DXFParseError("ezdxf nicht installiert") from e

        logger.info("[DXFParser] Parsing %s", path.name)

        try:
            doc = ezdxf.readfile(str(path))
        except Exception as e:
            raise DXFParseError(f"Konnte DXF nicht lesen: {path.name}") from e

        model = DXFModel(
            source_file=str(path),
            dxf_version=doc.dxfversion,
        )

        model.layers = self._extract_layers(doc)
        model.rooms = self._extract_rooms(doc)

        logger.info(
            "[DXFParser] %s: %d Layer, %d Räume, %.1f m²",
            path.name,
            len(model.layers),
            len(model.rooms),
            model.total_area_m2,
        )
        return model

    def parse_bytes(
        self, content: bytes, filename: str = "upload.dxf"
    ) -> DXFModel:
        """Parst DXF aus Bytes (z.B. Django File Upload)."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            tmp.write(content)
            return self.parse(tmp.name)

    # ------------------------------------------------------------------
    # Private Methoden
    # ------------------------------------------------------------------

    def _extract_layers(self, doc) -> list[DXFLayer]:
        """Extrahiert alle Layer."""
        layers = []
        for layer in doc.layers:
            name = layer.dxf.name
            if name.startswith("*") or name == "0":
                continue
            layers.append(
                DXFLayer(
                    name=name,
                    color=getattr(layer.dxf, "color", 7),
                    linetype=getattr(layer.dxf, "linetype", "CONTINUOUS"),
                    is_frozen=bool(getattr(layer.dxf, "flags", 0) & 1),
                )
            )
        return layers

    def _extract_rooms(self, doc) -> list[DXFRoom]:
        """Extrahiert Räume aus Polygonen und Text-Labels."""
        msp = doc.modelspace()
        rooms: list[DXFRoom] = []

        # 1. Polygone (LWPOLYLINE) als Raumflächen
        polygon_rooms = self._extract_polyline_rooms(msp)

        # 2. Texte als Raum-Labels
        text_labels = self._extract_text_labels(msp)

        # 3. Text ↔ Polygon verknüpfen
        rooms = self._match_texts_to_polygons(polygon_rooms, text_labels)

        # 4. Deduplizierung
        rooms = self._deduplicate(rooms)

        return rooms

    def _extract_polyline_rooms(self, msp) -> list[DXFRoom]:
        """Extrahiert geschlossene Polylinien als Räume."""
        rooms = []

        for entity in msp.query("LWPOLYLINE"):
            layer = entity.dxf.layer

            # Ausgeschlossene Layer überspringen
            if any(kw in layer.lower() for kw in EXCLUDED_LAYER_KEYWORDS):
                continue

            if not entity.is_closed:
                continue

            try:
                vertices = [
                    Point2D(x, y) for x, y in entity.get_points(format="xy")
                ]
                if len(vertices) < 3:
                    continue

                area = self._calculate_polygon_area(vertices)
                perimeter = self._calculate_perimeter(vertices)

                if area < 0.5:  # Kleiner als 0.5 m² → kein Raum
                    continue

                centroid = self._calculate_centroid(vertices)
                room = DXFRoom(
                    layer=layer,
                    area_m2=area,
                    perimeter_m=perimeter,
                    vertices=vertices,
                    position=centroid,
                )
                rooms.append(room)
            except Exception as e:
                logger.debug("[DXFParser] Polyline skip: %s", e)

        return rooms

    def _extract_text_labels(self, msp) -> list[dict]:
        """Extrahiert Text-Labels (TEXT + MTEXT)."""
        labels = []

        for entity in msp.query("TEXT MTEXT"):
            try:
                if entity.dxftype() == "TEXT":
                    text = entity.dxf.text
                    pos = Point2D(entity.dxf.insert.x, entity.dxf.insert.y)
                else:  # MTEXT
                    text = entity.plain_mtext()
                    pos = Point2D(entity.dxf.insert.x, entity.dxf.insert.y)

                text = text.strip()
                if text and len(text) > 1:
                    labels.append({"text": text, "position": pos})
            except Exception:
                pass

        return labels

    def _match_texts_to_polygons(
        self, rooms: list[DXFRoom], labels: list[dict]
    ) -> list[DXFRoom]:
        """Verknüpft Text-Labels mit Polygon-Räumen."""
        for room in rooms:
            for label in labels:
                if self._point_in_polygon(label["position"], room.vertices):
                    room.name = room.name or label["text"]
                    break

            if not room.name:
                room.name = f"Raum ({room.layer})"

        return rooms

    def _deduplicate(self, rooms: list[DXFRoom]) -> list[DXFRoom]:
        """Entfernt Duplikate (gleiche Fläche + gleicher Layer)."""
        seen: set[tuple[str, float]] = set()
        unique = []
        for room in rooms:
            key = (room.layer, round(room.area_m2, 1))
            if key not in seen:
                seen.add(key)
                unique.append(room)
        return unique

    # ------------------------------------------------------------------
    # Geometrie-Hilfsmethoden
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_polygon_area(vertices: list[Point2D]) -> float:
        """Shoelace-Formel für Polygon-Fläche."""
        n = len(vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i].x * vertices[j].y
            area -= vertices[j].x * vertices[i].y
        return abs(area) / 2.0

    @staticmethod
    def _calculate_perimeter(vertices: list[Point2D]) -> float:
        """Berechnet Umfang eines Polygons."""
        n = len(vertices)
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = vertices[j].x - vertices[i].x
            dy = vertices[j].y - vertices[i].y
            perimeter += math.sqrt(dx * dx + dy * dy)
        return perimeter

    @staticmethod
    def _calculate_centroid(vertices: list[Point2D]) -> Point2D:
        """Berechnet Schwerpunkt eines Polygons."""
        n = len(vertices)
        cx = sum(v.x for v in vertices) / n
        cy = sum(v.y for v in vertices) / n
        return Point2D(cx, cy)

    @staticmethod
    def _point_in_polygon(point: Point2D, polygon: list[Point2D]) -> bool:
        """Ray-Casting Algorithmus."""
        x, y = point.x, point.y
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i].x, polygon[i].y
            xj, yj = polygon[j].x, polygon[j].y
            if ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi) + xi
            ):
                inside = not inside
            j = i
        return inside

    @staticmethod
    def _get_bounding_box(vertices: list[Point2D]) -> BoundingBox:
        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        return BoundingBox(min(xs), min(ys), max(xs), max(ys))
