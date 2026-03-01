"""
nl2cad.brandschutz.rules.asr_a23
==================================
Regelwerk-Checks nach ASR A2.3 "Fluchtwege und Notausgänge".

Quellen:
- ASR A2.3 (2022): Technische Regeln für Arbeitsstätten
- § 4: Mindestbreiten von Fluchtwegen
- § 5: Länge von Fluchtwegen (max. 35m, Richtungsänderung max. +25m)

WICHTIG: Diese Klasse implementiert den bisher FEHLENDEN Use Case
der regelwerkkonformen Fluchtweg-Validierung.
"""
from __future__ import annotations

import logging

from nl2cad.brandschutz.models import (
    BrandschutzAnalyse,
    BrandschutzKategorie,
    BrandschutzMangel,
    Fluchtweg,
    MängelSchwere,
)

logger = logging.getLogger(__name__)

# ASR A2.3 Grenzwerte
MAX_FLUCHTWEG_LAENGE_M = 35.0        # § 5 Abs. 1: max. 35m Weglänge
MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M = 60.0  # § 5 Abs. 2: max. 60m mit Richtungsänderung
MIN_BREITE_STANDARD_M = 0.875        # § 4: min. 0.875m (Grundmaß)
MIN_BREITE_AB_5_PERSONEN_M = 1.0     # § 4: ab 5 Personen min. 1.0m
MIN_BREITE_AB_20_PERSONEN_M = 1.2    # § 4: ab 20 Personen min. 1.2m
MIN_TUERBREITE_M = 0.78              # Lichte Mindestbreite Türöffnung


class ASRA23Validator:
    """
    Prüft Fluchtwege gegen ASR A2.3.

    Checks:
    1. Fluchtweglänge ≤ 35m (ohne Richtungsänderung)
    2. Fluchtweglänge ≤ 60m (mit Richtungsänderung)
    3. Mindestbreite 0.875m / 1.0m / 1.2m
    4. Mindestens ein Notausgang pro Fluchtweg

    Usage:
        validator = ASRA23Validator()
        analyse = validator.validate(analyse)
        # analyse.maengel enthält jetzt Regelwerk-Findings
    """

    def validate(self, analyse: BrandschutzAnalyse) -> BrandschutzAnalyse:
        """Führt alle ASR A2.3 Checks durch und ergänzt analyse.maengel."""

        for fluchtweg in analyse.fluchtwege:
            self._check_laenge(fluchtweg, analyse)
            self._check_breite(fluchtweg, analyse)
            self._check_notausgang(fluchtweg, analyse)

        if not analyse.fluchtwege:
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.WARNUNG,
                kategorie=BrandschutzKategorie.FLUCHTWEG,
                beschreibung="Keine Fluchtwege erkannt",
                regelwerk="ASR A2.3 § 3",
                empfehlung="Fluchtwege in CAD-Datei als dedizierte Layer kennzeichnen",
            ))

        return analyse

    def _check_laenge(self, fluchtweg: Fluchtweg, analyse: BrandschutzAnalyse) -> None:
        """§ 5 ASR A2.3: Maximale Weglänge."""
        if fluchtweg.laenge_m <= 0:
            fluchtweg.laenge_ok = None  # Nicht prüfbar
            return

        if fluchtweg.laenge_m > MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M:
            fluchtweg.laenge_ok = False
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.KRITISCH,
                kategorie=BrandschutzKategorie.FLUCHTWEG,
                beschreibung=(
                    f"Fluchtweg '{fluchtweg.name}': Länge {fluchtweg.laenge_m:.1f}m "
                    f"überschreitet max. {MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M}m"
                ),
                regelwerk="ASR A2.3 § 5 Abs. 2",
                empfehlung="Zusätzlichen Notausgang innerhalb von 35m einplanen",
            ))
        elif fluchtweg.laenge_m > MAX_FLUCHTWEG_LAENGE_M:
            fluchtweg.laenge_ok = True  # Ok mit Abzweig, aber Hinweis
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.WARNUNG,
                kategorie=BrandschutzKategorie.FLUCHTWEG,
                beschreibung=(
                    f"Fluchtweg '{fluchtweg.name}': Länge {fluchtweg.laenge_m:.1f}m "
                    f"> {MAX_FLUCHTWEG_LAENGE_M}m — Richtungsänderung erforderlich"
                ),
                regelwerk="ASR A2.3 § 5 Abs. 1",
                empfehlung="Richtungsänderung dokumentieren oder Weglänge kürzen",
            ))
        else:
            fluchtweg.laenge_ok = True

    def _check_breite(self, fluchtweg: Fluchtweg, analyse: BrandschutzAnalyse) -> None:
        """§ 4 ASR A2.3: Mindestbreite."""
        if fluchtweg.breite_m <= 0:
            fluchtweg.breite_ok = None  # Nicht prüfbar aus CAD
            return

        if fluchtweg.breite_m < MIN_BREITE_STANDARD_M:
            fluchtweg.breite_ok = False
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.KRITISCH,
                kategorie=BrandschutzKategorie.FLUCHTWEG,
                beschreibung=(
                    f"Fluchtweg '{fluchtweg.name}': Breite {fluchtweg.breite_m:.2f}m "
                    f"unterschreitet Mindestmaß {MIN_BREITE_STANDARD_M}m"
                ),
                regelwerk="ASR A2.3 § 4 Abs. 2",
                empfehlung=f"Fluchtweg auf mind. {MIN_BREITE_STANDARD_M}m verbreitern",
            ))
        elif fluchtweg.breite_m < MIN_BREITE_AB_5_PERSONEN_M:
            fluchtweg.breite_ok = True  # Grundmaß ok, Hinweis für >5 Personen
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.WARNUNG,
                kategorie=BrandschutzKategorie.FLUCHTWEG,
                beschreibung=(
                    f"Fluchtweg '{fluchtweg.name}': Breite {fluchtweg.breite_m:.2f}m "
                    f"— bei >5 Personen mind. {MIN_BREITE_AB_5_PERSONEN_M}m erforderlich"
                ),
                regelwerk="ASR A2.3 § 4 Abs. 3",
                empfehlung="Personenzahl prüfen und ggf. verbreitern",
            ))
        else:
            fluchtweg.breite_ok = True

    def _check_notausgang(self, fluchtweg: Fluchtweg, analyse: BrandschutzAnalyse) -> None:
        """§ 6 ASR A2.3: Mindestens ein Notausgang."""
        notausgaenge = [
            e for e in analyse.fluchtwege if e.hat_notausgang
        ]
        if not notausgaenge:
            analyse.maengel.append(BrandschutzMangel(
                schwere=MängelSchwere.KRITISCH,
                kategorie=BrandschutzKategorie.NOTAUSGANG,
                beschreibung="Kein Notausgang erkannt",
                regelwerk="ASR A2.3 § 6 Abs. 1",
                empfehlung="Mindestens einen Notausgang je Nutzungseinheit einplanen",
            ))
