"""
nl2cad.areas.din277
====================
DIN 277 Flächenberechnung (Ausgabe 2016).
Klassifiziert Räume und berechnet Nutzungsflächenanteile.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from nl2cad.core.constants import DIN277_CODES, ROOM_KEYWORD_TO_DIN277
from nl2cad.core.models.dxf import DXFModel
from nl2cad.core.models.ifc import IFCModel

logger = logging.getLogger(__name__)


@dataclass
class DIN277Category:
    """Eine DIN 277 Nutzungsart mit aggregierten Flächen."""

    code: str
    name: str
    room_count: int = 0
    area_m2: float = 0.0

    @property
    def area_formatted(self) -> str:
        return f"{self.area_m2:.2f} m²"


@dataclass
class DIN277Result:
    """
    Ergebnis einer DIN 277 Flächenberechnung.

    Enthält alle Kategorien (NUF, TF, VF, FF, KGF)
    sowie Gesamtflächen.
    """

    categories: dict[str, DIN277Category] = field(default_factory=dict)
    unclassified_rooms: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def nutzungsflaeche_m2(self) -> float:
        """Hauptnutzfläche NUF (alle NUF_x)."""
        return sum(
            c.area_m2
            for code, c in self.categories.items()
            if code.startswith("NUF")
        )

    @property
    def verkehrsflaeche_m2(self) -> float:
        """Verkehrsfläche VF."""
        return sum(
            c.area_m2
            for code, c in self.categories.items()
            if code.startswith("VF")
        )

    @property
    def technische_flaeche_m2(self) -> float:
        """Technische Anlagenfläche TF."""
        return self.categories.get("TF", DIN277Category("TF", "")).area_m2

    @property
    def netto_grundflaeche_m2(self) -> float:
        """NGF = NUF + TF + VF."""
        return (
            self.nutzungsflaeche_m2
            + self.technische_flaeche_m2
            + self.verkehrsflaeche_m2
        )

    @property
    def total_rooms(self) -> int:
        return sum(c.room_count for c in self.categories.values())

    def to_dict(self) -> dict:
        return {
            "nutzungsflaeche_m2": round(self.nutzungsflaeche_m2, 2),
            "verkehrsflaeche_m2": round(self.verkehrsflaeche_m2, 2),
            "technische_flaeche_m2": round(self.technische_flaeche_m2, 2),
            "netto_grundflaeche_m2": round(self.netto_grundflaeche_m2, 2),
            "total_rooms": self.total_rooms,
            "categories": {
                code: {
                    "name": c.name,
                    "room_count": c.room_count,
                    "area_m2": round(c.area_m2, 2),
                }
                for code, c in self.categories.items()
            },
            "warnings": self.warnings,
        }


class DIN277Calculator:
    """
    Berechnet DIN 277 Flächenkenngrößen aus IFC- oder DXF-Modell.

    Usage:
        calc = DIN277Calculator()

        # Aus IFC
        result = calc.calculate_from_ifc(ifc_model)

        # Aus DXF
        result = calc.calculate_from_dxf(dxf_model)

        # Aus Raumliste (dict)
        result = calc.calculate(rooms=[{"name": "Büro", "area_m2": 25.0}])

        print(f"NUF: {result.nutzungsflaeche_m2:.1f} m²")
        print(f"NGF: {result.netto_grundflaeche_m2:.1f} m²")
    """

    def calculate_from_ifc(self, model: IFCModel) -> DIN277Result:
        """Berechnet DIN 277 aus IFCModel."""
        rooms_data = [
            {
                "name": r.name,
                "area_m2": r.area_m2,
                "din277_code": r.din277_code,
            }
            for r in model.rooms
        ]
        return self.calculate(rooms_data)

    def calculate_from_dxf(self, model: DXFModel) -> DIN277Result:
        """Berechnet DIN 277 aus DXFModel."""
        rooms_data = [
            {
                "name": r.name,
                "area_m2": r.area_m2,
                "din277_code": r.din277_code,
            }
            for r in model.rooms
        ]
        return self.calculate(rooms_data)

    def calculate(self, rooms: list[dict]) -> DIN277Result:
        """
        Berechnet DIN 277 aus Raumliste.

        Args:
            rooms: Liste von Dicts mit "name", "area_m2", optional "din277_code"

        Returns:
            DIN277Result mit allen Kategorien
        """
        result = DIN277Result()

        for room in rooms:
            name = room.get("name", "")
            area = float(room.get("area_m2", 0.0))
            code = room.get("din277_code", "") or self._classify(name)

            if not code:
                code = "NUF_8"  # Default: Sonstige Nutzung
                result.warnings.append(
                    f"Raum '{name}' nicht klassifiziert → NUF_8"
                )

            if code not in result.categories:
                category_name = DIN277_CODES.get(code, "Unbekannt")
                result.categories[code] = DIN277Category(
                    code=code,
                    name=category_name,
                )

            result.categories[code].room_count += 1
            result.categories[code].area_m2 += area

        logger.info(
            "[DIN277] %d Räume, %.1f m² NGF",
            len(rooms),
            result.netto_grundflaeche_m2,
        )
        return result

    def classify_room(self, room_name: str) -> str:
        """Klassifiziert einen Raum nach DIN 277. Gibt DIN277-Code zurück."""
        return self._classify(room_name)

    def _classify(self, name: str) -> str:
        """Keyword-basierte Klassifikation."""
        name_lower = name.lower()
        for keyword, code in ROOM_KEYWORD_TO_DIN277.items():
            if keyword in name_lower:
                return code
        return ""
