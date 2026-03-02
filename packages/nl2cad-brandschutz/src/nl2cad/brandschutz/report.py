"""
nl2cad.brandschutz.report
==========================
BrandschutzkonzeptReport — Gesamtergebnis Milestone 1.

Implementierungsreihenfolge: Schritt 4.

Aggregiert:
  - IFCQualityReport (aus nl2cad-core)
  - GebaeudeklasseResult
  - BrandschutzAnalyse
  - ExplosionsschutzDokument (optional)

BeurteilungsStatus (ADR B-06): kein bool|None.
Kein stiller Fallback: fehlende Teilberichte erzeugen NICHT_BEURTEILBAR.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

from nl2cad.brandschutz.explosionsschutz import (
    BeurteilungsStatus,
    ExplosionsschutzDokument,
)
from nl2cad.brandschutz.gebaeudeklasse import GebaeudeklasseResult
from nl2cad.brandschutz.models import BrandschutzAnalyse

logger = logging.getLogger(__name__)


@dataclass
class BrandschutzkonzeptReport:
    """
    Vollstaendiger Brandschutzkonzept-Report fuer ein Gebaeude.

    Felder:
        gebaeudeklasse_result:  MBO-Gebaeudeklassen-Ermittlung (Pflicht)
        brandschutz_analyse:    Fluchtweg- und Brandabschnittsanalyse (Pflicht)
        explosionsschutz:       ESD nach BetrSichV (optional, None wenn nicht relevant)
        beurteilungs_status:    Expliziter Status — kein bool|None (ADR B-06)
        erstellt_am:            ISO-Timestamp der Report-Erstellung
        report_hash:            SHA-256 ueber to_dict() fuer Idempotenz-Pruefung

    Qualitaetspruefung (IFCQualityReport) wird als optionales Feld
    aus dem Pipeline-Context beigefuegt.
    """

    gebaeudeklasse_result: GebaeudeklasseResult
    brandschutz_analyse: BrandschutzAnalyse
    explosionsschutz: ExplosionsschutzDokument | None = None
    beurteilungs_status: BeurteilungsStatus = BeurteilungsStatus.VORPRUEFUNG
    erstellt_am: str = ""
    report_hash: str = ""
    quality_score: float = -1.0  # -1.0 = nicht geprueft
    meldungen: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.erstellt_am:
            self.erstellt_am = datetime.now().isoformat(timespec="seconds")
        self._aktualisiere_status()

    def _aktualisiere_status(self) -> None:
        """Setzt BeurteilungsStatus basierend auf vorliegenden Daten."""
        from nl2cad.brandschutz.gebaeudeklasse import Gebaeudeklasse

        # Nicht beurteilbar wenn GK unbekannt
        if (
            self.gebaeudeklasse_result.gebaeudeklasse
            == Gebaeudeklasse.UNBEKANNT
        ):
            self.beurteilungs_status = BeurteilungsStatus.NICHT_BEURTEILBAR
            self.meldungen.append(
                "Gebaeudeklasse nicht ermittelbar — Beurteilung nicht moeglich"
            )
            return

        # Nicht beurteilbar wenn IFC-Qualitaet kritisch (score == 0.0)
        if self.quality_score == 0.0:
            self.beurteilungs_status = BeurteilungsStatus.NICHT_BEURTEILBAR
            self.meldungen.append(
                "IFC-Qualitaetspruefung fehlgeschlagen (score=0.0) — "
                "Beurteilung nicht moeglich"
            )
            return

        # Abgelehnt bei kritischen Maengeln
        if self.brandschutz_analyse.hat_kritische_maengel:
            self.beurteilungs_status = BeurteilungsStatus.ABGELEHNT
            n = len(self.brandschutz_analyse.kritische_maengel)
            self.meldungen.append(
                f"{n} kritische(r) Brandschutzmangel gefunden — "
                "Beurteilung: ABGELEHNT (Vorpruefung)"
            )
            return

        # Vorpruefung: Daten vollstaendig, keine kritischen Maengel
        self.beurteilungs_status = BeurteilungsStatus.VORPRUEFUNG
        self.meldungen.append(
            "Vorpruefung abgeschlossen. Keine kritischen Maengel erkannt. "
            "Rechtsverbindliche Beurteilung durch befugten Sachverstaendigen erforderlich."
        )

    @property
    def hat_ex_bereiche(self) -> bool:
        if self.explosionsschutz is None:
            return False
        return bool(self.explosionsschutz.ex_bereiche)

    @property
    def warnungen_gesamt(self) -> list[str]:
        warnungen = list(self.meldungen)
        warnungen += self.brandschutz_analyse.warnungen
        warnungen += self.gebaeudeklasse_result.meldungen
        return warnungen

    def berechne_hash(self) -> str:
        """SHA-256 ueber den Report-Dict fuer Idempotenz bei DB-Speicherung."""
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        self.report_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.report_hash

    def to_dict(self) -> dict:
        return {
            "erstellt_am": self.erstellt_am,
            "beurteilungs_status": self.beurteilungs_status.value,
            "quality_score": self.quality_score,
            "gebaeudeklasse": self.gebaeudeklasse_result.to_dict(),
            "brandschutz": self.brandschutz_analyse.to_dict(),
            "explosionsschutz": (
                self.explosionsschutz.to_dict()
                if self.explosionsschutz
                else None
            ),
            "meldungen": self.meldungen,
        }
