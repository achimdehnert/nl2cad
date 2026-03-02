"""
nl2cad.brandschutz.gebaeudeklasse
===================================
Gebaeudeklassen-Ermittlung nach MBO § 2 Abs. 3 (Fassung 2016).

Implementierungsreihenfolge: Schritt 2.

Eingabe: IFCModel (OKFF-Werte aus elevation_m der Geschosse)
Ausgabe: GebaeudeklasseResult (GK 1-5, Hochhaus-Flag, Norm-Version)

Keine stillen Fallbacks: fehlende OKFF-Werte erzeugen GK_UNBEKANNT.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum

from nl2cad.brandschutz.constants import (
    MBO_GK4_MAX_OKFF_M,
    MBO_GK12_MAX_NE_ANZAHL,
    MBO_GK12_MAX_NE_FLAECHE_M2,
    MBO_GK123_MAX_OKFF_M,
    MBO_HOCHHAUS_MIN_OKFF_M,
    MBO_VERSION,
)

logger = logging.getLogger(__name__)


class Gebaeudeklasse(StrEnum):
    """MBO § 2 Abs. 3 Gebaeudeklassen."""

    GK_1 = "GK1"
    GK_2 = "GK2"
    GK_3 = "GK3"
    GK_4 = "GK4"
    GK_5 = "GK5"
    HOCHHAUS = "Hochhaus"
    UNBEKANNT = "Unbekannt"


@dataclass
class GebaeudeklasseResult:
    """
    Ergebnis der MBO-Gebaeudeklassen-Ermittlung.

    Felder:
        gebaeudeklasse:  Ermittelte GK (GK1..GK5, Hochhaus, Unbekannt)
        okff_max_m:      Hoechste OKFF (Oberkante Fertigfussboden) in m
        geschoss_anzahl: Anzahl Geschosse laut IFC
        norm_version:    Verwendete Norm-Version (immer gesetzt)
        meldungen:       Hinweise und Warnungen zur Ermittlung
        ist_hochhaus:    True ab OKFF > 22m (Sonderbau)
    """

    gebaeudeklasse: Gebaeudeklasse = Gebaeudeklasse.UNBEKANNT
    okff_max_m: float = 0.0
    geschoss_anzahl: int = 0
    norm_version: str = MBO_VERSION
    meldungen: list[str] = field(default_factory=list)

    @property
    def ist_hochhaus(self) -> bool:
        return self.okff_max_m > MBO_HOCHHAUS_MIN_OKFF_M

    def to_dict(self) -> dict:
        return {
            "gebaeudeklasse": self.gebaeudeklasse.value,
            "okff_max_m": self.okff_max_m,
            "geschoss_anzahl": self.geschoss_anzahl,
            "norm_version": self.norm_version,
            "ist_hochhaus": self.ist_hochhaus,
            "meldungen": self.meldungen,
        }


class GebaeudeklasseHandler:
    """
    Ermittelt Gebaeudeklasse nach MBO § 2 Abs. 3.

    Prueffolge (konservativ, hoechste anwendbare GK):
    1. Hochhaus: OKFF > 22m  → Sonderbau
    2. GK 5:     OKFF > 13m  → GK5
    3. GK 4:     OKFF > 7m   → GK4
    4. GK 3:     OKFF <= 7m, mehr als 2 NE oder NE > 400m² → GK3
    5. GK 2:     OKFF <= 7m, max. 2 NE, NE <= 400m² → GK2
    6. GK 1:     Wie GK2, aber nur 1 NE (freistehend)

    Hinweis: NE-Flaeche und NE-Anzahl koennen aus IFC nicht zuverlaessig
    ermittelt werden. Wenn keine Raum-Daten vorhanden → GK_UNBEKANNT
    mit Hinweismeldung. Kein stiller Fallback auf GK3.

    Usage:
        handler = GebaeudeklasseHandler()
        result = handler.ermittle(ifc_model)
        print(result.gebaeudeklasse.value)  # "GK3"
    """

    def ermittle(self, model) -> GebaeudeklasseResult:
        """
        Ermittelt Gebaeudeklasse aus IFCModel.

        Args:
            model: IFCModel (nl2cad.core.models.IFCModel)

        Returns:
            GebaeudeklasseResult mit Gebaeudeklasse und Begruendung
        """
        result = GebaeudeklasseResult()
        result.geschoss_anzahl = len(model.floors)

        if not model.floors:
            result.meldungen.append(
                "Keine Geschosse im Modell — Gebaeudeklasse nicht ermittelbar"
            )
            logger.warning("[GebaeudeklasseHandler] Kein Geschoss vorhanden")
            return result

        # OKFF = elevation_m des hoechsten Nutzgeschosses
        elevations = [f.elevation_m for f in model.floors]
        okff_max = max(elevations)
        result.okff_max_m = okff_max

        # Alle elevations 0.0: OKFF nicht auswertbar
        if all(e == 0.0 for e in elevations) and len(model.floors) > 1:
            result.meldungen.append(
                "Alle Geschoss-Hoehen sind 0.0 m — OKFF nicht auswertbar. "
                "Gebaeudeklasse kann nicht zuverlaessig ermittelt werden."
            )
            logger.warning("[GebaeudeklasseHandler] Alle elevation_m == 0.0")
            return result

        # Hochhaus-Pruefung zuerst (Sonderbau)
        if okff_max > MBO_HOCHHAUS_MIN_OKFF_M:
            result.gebaeudeklasse = Gebaeudeklasse.HOCHHAUS
            result.meldungen.append(
                f"OKFF {okff_max:.1f}m > {MBO_HOCHHAUS_MIN_OKFF_M}m "
                f"— Hochhaus (Sonderbau MBO § 2 Abs. 8 Nr. 1, {MBO_VERSION})"
            )
            logger.info(
                "[GebaeudeklasseHandler] Hochhaus: OKFF=%.1fm", okff_max
            )
            return result

        # GK 5: OKFF > 13m
        if okff_max > MBO_GK4_MAX_OKFF_M:
            result.gebaeudeklasse = Gebaeudeklasse.GK_5
            result.meldungen.append(
                f"OKFF {okff_max:.1f}m > {MBO_GK4_MAX_OKFF_M}m "
                f"→ GK 5 (MBO § 2 Abs. 3 Nr. 5, {MBO_VERSION})"
            )
            logger.info("[GebaeudeklasseHandler] GK5: OKFF=%.1fm", okff_max)
            return result

        # GK 4: OKFF > 7m
        if okff_max > MBO_GK123_MAX_OKFF_M:
            result.gebaeudeklasse = Gebaeudeklasse.GK_4
            result.meldungen.append(
                f"OKFF {okff_max:.1f}m > {MBO_GK123_MAX_OKFF_M}m "
                f"→ GK 4 (MBO § 2 Abs. 3 Nr. 4, {MBO_VERSION})"
            )
            logger.info("[GebaeudeklasseHandler] GK4: OKFF=%.1fm", okff_max)
            return result

        # GK 1/2/3: OKFF <= 7m — NE-Kriterium
        # NE-Flaeche und -Anzahl aus IFC naeherungsweise:
        # Anzahl Nutzungseinheiten = Anzahl Geschosse (grobe Naeherung)
        # Flaeche = groesste Einzelgeschoss-Gesamtflaeche
        total_areas = [sum(r.area_m2 for r in f.rooms) for f in model.floors]
        max_ne_flaeche = max(total_areas) if total_areas else 0.0
        ne_anzahl = len(model.floors)  # Konservative Naeherung

        if max_ne_flaeche == 0.0:
            result.meldungen.append(
                "Keine Raumflaechen aus IFC — NE-Flaeche fuer GK1/2/3 "
                "nicht ermittelbar. Konservativ GK 3 angenommen."
            )
            result.gebaeudeklasse = Gebaeudeklasse.GK_3
            logger.warning(
                "[GebaeudeklasseHandler] Keine Raumflaechen — konservativ GK3"
            )
            return result

        # GK 3: mehr als 2 NE oder NE-Flaeche > 400m²
        if (
            ne_anzahl > MBO_GK12_MAX_NE_ANZAHL
            or max_ne_flaeche > MBO_GK12_MAX_NE_FLAECHE_M2
        ):
            result.gebaeudeklasse = Gebaeudeklasse.GK_3
            result.meldungen.append(
                f"NE-Anzahl={ne_anzahl}, NE-Flaeche={max_ne_flaeche:.0f}m² "
                f"→ GK 3 (MBO § 2 Abs. 3 Nr. 3, {MBO_VERSION})"
            )
            logger.info(
                "[GebaeudeklasseHandler] GK3: NE=%d, Fl=%.0f",
                ne_anzahl,
                max_ne_flaeche,
            )
            return result

        # GK 2: max. 2 NE <= 400m²
        if ne_anzahl == MBO_GK12_MAX_NE_ANZAHL:
            result.gebaeudeklasse = Gebaeudeklasse.GK_2
            result.meldungen.append(
                f"NE-Anzahl={ne_anzahl}, NE-Flaeche={max_ne_flaeche:.0f}m² "
                f"→ GK 2 (MBO § 2 Abs. 3 Nr. 2, {MBO_VERSION})"
            )
            logger.info("[GebaeudeklasseHandler] GK2: NE=%d", ne_anzahl)
            return result

        # GK 1: 1 NE, freistehend — nicht aus IFC pruefbar
        result.gebaeudeklasse = Gebaeudeklasse.GK_1
        result.meldungen.append(
            f"NE-Anzahl={ne_anzahl}, NE-Flaeche={max_ne_flaeche:.0f}m² "
            f"→ GK 1 (MBO § 2 Abs. 3 Nr. 1, {MBO_VERSION}). "
            "Freistand aus IFC nicht pruefbar — manuell bestaetigen."
        )
        logger.info("[GebaeudeklasseHandler] GK1: NE=%d", ne_anzahl)
        return result
