"""
nl2cad.core.quality
===================
IFC-Vollstaendigkeitspruefung fuer alle nl2cad-Packages.

FIX B-03: Gehoert in nl2cad-core, nicht nl2cad-brandschutz.
Alle Packages (areas, gaeb, brandschutz) importieren von hier.

Kein stilles 0.0-Fallback: fehlende Quantities werden als IFCQualityIssue
mit Severity KRITISCH/WARNUNG/INFO gemeldet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from nl2cad.core.models import IFCModel

logger = logging.getLogger(__name__)

# Severity-Konstanten — kein Enum damit keine Abhaengigkeit nach aussen
SEVERITY_KRITISCH = "KRITISCH"
SEVERITY_WARNUNG = "WARNUNG"
SEVERITY_INFO = "INFO"

# Grenzwerte
MIN_ROOM_AREA_M2 = 0.1
GENERIC_ROOM_NAMES = frozenset({"space", "raum", "room", "", "none"})


@dataclass
class IFCQualityIssue:
    """Ein einzelner Befund der IFC-Qualitaetspruefung."""

    severity: str  # KRITISCH | WARNUNG | INFO
    field_path: str  # z.B. "floors[0].rooms[2].area_m2"
    ifc_guid: str  # GlobalId des betroffenen Elements oder ""
    message: str


@dataclass
class IFCQualityReport:
    """
    Ergebnis der IFC-Vollstaendigkeitspruefung.

    is_valid=False bei mindestens einem KRITISCH-Issue.
    completeness_score: 0.0 (leer) bis 1.0 (vollstaendig).
    """

    is_valid: bool
    issues: list[IFCQualityIssue] = field(default_factory=list)
    completeness_score: float = 1.0

    @property
    def kritische_issues(self) -> list[IFCQualityIssue]:
        return [i for i in self.issues if i.severity == SEVERITY_KRITISCH]

    @property
    def warnungen(self) -> list[IFCQualityIssue]:
        return [i for i in self.issues if i.severity == SEVERITY_WARNUNG]

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "completeness_score": self.completeness_score,
            "issues": [
                {
                    "severity": i.severity,
                    "field_path": i.field_path,
                    "ifc_guid": i.ifc_guid,
                    "message": i.message,
                }
                for i in self.issues
            ],
        }


class IFCQualityChecker:
    """
    Prueft ein IFCModel auf Vollstaendigkeit und Mindestwerte.

    Keine Exception bei Problemen — gibt IFCQualityReport zurueck.
    IFCQualityHandler in der Pipeline prueft is_valid und setzt
    result.success=False bei KRITISCH (W-03 Fix).

    Usage:
        checker = IFCQualityChecker()
        report = checker.check(model)
        if not report.is_valid:
            raise IFCParseError(...)
    """

    def check(self, model: IFCModel) -> IFCQualityReport:
        """Fuehrt alle Pruefregeln durch und gibt einen IFCQualityReport zurueck."""
        issues: list[IFCQualityIssue] = []

        self._check_mindestanzahl_geschosse(model, issues)
        self._check_mindestanzahl_raeume(model, issues)
        self._check_geschoss_hoehen(model, issues)
        self._check_raum_flaechen(model, issues)
        self._check_raum_hoehen(model, issues)
        self._check_raum_namen(model, issues)

        # W-08: Score semantisch klar — kein irreführender Zahlenwert
        # 0.0 bei KRITISCH, 0.5 bei nur WARNUNG, 1.0 wenn alles ok
        has_kritisch = any(i.severity == SEVERITY_KRITISCH for i in issues)
        has_warnung = any(i.severity == SEVERITY_WARNUNG for i in issues)
        if has_kritisch:
            score = 0.0
        elif has_warnung:
            score = 0.5
        else:
            score = 1.0

        report = IFCQualityReport(
            is_valid=(not has_kritisch),
            issues=issues,
            completeness_score=score,
        )
        logger.info(
            "[IFCQualityChecker] score=%.2f kritisch=%d warnungen=%d",
            report.completeness_score,
            len(report.kritische_issues),
            len(report.warnungen),
        )
        return report

    def _check_mindestanzahl_geschosse(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        if not model.floors:
            issues.append(
                IFCQualityIssue(
                    severity=SEVERITY_KRITISCH,
                    field_path="floors",
                    ifc_guid="",
                    message="Kein Geschoss (IfcBuildingStorey) gefunden — Modell leer",
                )
            )

    def _check_mindestanzahl_raeume(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        all_rooms = model.rooms
        if not all_rooms:
            issues.append(
                IFCQualityIssue(
                    severity=SEVERITY_KRITISCH,
                    field_path="floors[*].rooms",
                    ifc_guid="",
                    message="Kein Raum (IfcSpace) gefunden — Flaechenberechnung nicht moeglich",
                )
            )

    def _check_geschoss_hoehen(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        if not model.floors:
            return
        all_zero = all(f.elevation_m == 0.0 for f in model.floors)
        if all_zero and len(model.floors) > 1:
            issues.append(
                IFCQualityIssue(
                    severity=SEVERITY_WARNUNG,
                    field_path="floors[*].elevation_m",
                    ifc_guid="",
                    message=(
                        "Alle Geschoss-Hoehen sind 0.0 — "
                        "Gebaeudeklassen-Ermittlung (OKFF) nicht moeglich"
                    ),
                )
            )

    def _check_raum_flaechen(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        for floor_idx, floor in enumerate(model.floors):
            for room_idx, room in enumerate(floor.rooms):
                if room.area_m2 < MIN_ROOM_AREA_M2:
                    issues.append(
                        IFCQualityIssue(
                            severity=SEVERITY_WARNUNG,
                            field_path=f"floors[{floor_idx}].rooms[{room_idx}].area_m2",
                            ifc_guid=room.ifc_id,
                            message=(
                                f"Raum '{room.name}': area_m2={room.area_m2} "
                                f"< Mindestwert {MIN_ROOM_AREA_M2} m2 "
                                f"(stilles 0.0-Fallback verhindert)"
                            ),
                        )
                    )

    def _check_raum_hoehen(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        for floor_idx, floor in enumerate(model.floors):
            for room_idx, room in enumerate(floor.rooms):
                if room.height_m == 0.0:
                    issues.append(
                        IFCQualityIssue(
                            severity=SEVERITY_WARNUNG,
                            field_path=f"floors[{floor_idx}].rooms[{room_idx}].height_m",
                            ifc_guid=room.ifc_id,
                            message=(
                                f"Raum '{room.name}': height_m=0.0 — "
                                "Raumhoehe nicht aus IFC lesbar"
                            ),
                        )
                    )

    def _check_raum_namen(
        self, model: IFCModel, issues: list[IFCQualityIssue]
    ) -> None:
        for floor_idx, floor in enumerate(model.floors):
            for room_idx, room in enumerate(floor.rooms):
                if room.name.lower().strip() in GENERIC_ROOM_NAMES:
                    issues.append(
                        IFCQualityIssue(
                            severity=SEVERITY_INFO,
                            field_path=f"floors[{floor_idx}].rooms[{room_idx}].name",
                            ifc_guid=room.ifc_id,
                            message=(
                                f"Raum hat generischen Namen '{room.name}' — "
                                "DIN277-Klassifikation per Keyword nicht moeglich"
                            ),
                        )
                    )
