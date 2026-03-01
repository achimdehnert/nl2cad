"""
nl2cad.areas.woflv
===================
WoFlV Wohnflächenberechnung (Wohnflächenverordnung 2004).

Berechnungsregeln:
- Vollwertige Grundfläche: Raumhöhe >= 2m → 100%
- Halbwertige Grundfläche: Raumhöhe 1-2m → 50%
- Nicht anrechenbar: Raumhöhe < 1m → 0%
- Terrassen, Balkone, Loggien → 25-50% je nach Art
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WoFlVRoom:
    """Raum für WoFlV-Berechnung."""
    name: str
    raw_area_m2: float
    height_m: float = 2.5
    is_balcony: bool = False
    is_terrace: bool = False
    is_loggia: bool = False

    @property
    def factor(self) -> float:
        """Anrechnungsfaktor nach WoFlV."""
        if self.is_balcony or self.is_terrace:
            return 0.25  # Standard: 25% (kann 50% sein bei Bebauungsplan)
        if self.is_loggia:
            return 0.50
        # Nach Raumhöhe
        if self.height_m >= 2.0:
            return 1.0
        if self.height_m >= 1.0:
            return 0.5
        return 0.0

    @property
    def woflv_area_m2(self) -> float:
        return self.raw_area_m2 * self.factor


@dataclass
class WoFlVResult:
    """Ergebnis der WoFlV-Berechnung."""
    rooms: list[WoFlVRoom] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_woflv_m2(self) -> float:
        return sum(r.woflv_area_m2 for r in self.rooms)

    @property
    def total_raw_m2(self) -> float:
        return sum(r.raw_area_m2 for r in self.rooms)

    def to_dict(self) -> dict:
        return {
            "total_woflv_m2": round(self.total_woflv_m2, 2),
            "total_raw_m2": round(self.total_raw_m2, 2),
            "rooms": [
                {
                    "name": r.name,
                    "raw_area_m2": round(r.raw_area_m2, 2),
                    "height_m": r.height_m,
                    "factor": r.factor,
                    "woflv_area_m2": round(r.woflv_area_m2, 2),
                }
                for r in self.rooms
            ],
            "warnings": self.warnings,
        }


class WoFlVCalculator:
    """
    Berechnet Wohnfläche nach WoFlV 2004.

    Usage:
        calc = WoFlVCalculator()
        result = calc.calculate_from_rooms([
            {"name": "Wohnzimmer", "area_m2": 30.0, "height_m": 2.5},
            {"name": "Balkon",     "area_m2":  8.0, "is_balcony": True},
        ])
        print(f"Wohnfläche: {result.total_woflv_m2:.2f} m²")
    """

    def calculate_from_rooms(self, rooms: list[dict]) -> WoFlVResult:
        """
        Berechnet WoFlV aus Raumliste.

        Args:
            rooms: Liste von Dicts mit:
                   "name", "area_m2", optional: "height_m",
                   "is_balcony", "is_terrace", "is_loggia"
        """
        result = WoFlVResult()

        for r in rooms:
            room = WoFlVRoom(
                name=r.get("name", ""),
                raw_area_m2=float(r.get("area_m2", 0.0)),
                height_m=float(r.get("height_m", 2.5)),
                is_balcony=bool(r.get("is_balcony", False)),
                is_terrace=bool(r.get("is_terrace", False)),
                is_loggia=bool(r.get("is_loggia", False)),
            )

            if room.raw_area_m2 <= 0:
                result.warnings.append(f"Raum '{room.name}': Fläche = 0, wird ignoriert")
                continue

            result.rooms.append(room)

        logger.info(
            "[WoFlV] %d Räume, %.2f m² Wohnfläche (von %.2f m² Grundfläche)",
            len(result.rooms),
            result.total_woflv_m2,
            result.total_raw_m2,
        )
        return result
