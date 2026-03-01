"""
nl2cad.brandschutz.rules.din4102
==================================
Regelwerk-Checks nach DIN 4102 / EN 13501 Feuerwiderstand.
"""
from __future__ import annotations

from nl2cad.brandschutz.models import BrandschutzAnalyse


class DIN4102Validator:
    """Prüft Brandabschnitte auf korrekte Feuerwiderstandsklassen."""

    VALID_KLASSEN = frozenset([
        "F30", "F60", "F90", "F120", "F180",
        "REI30", "REI60", "REI90", "REI120",
        "EI30", "EI60", "EI90", "EI120",
    ])

    def validate(self, analyse: BrandschutzAnalyse) -> BrandschutzAnalyse:
        """Prüft Feuerwiderstandsklassen der erkannten Brandabschnitte."""
        for abschnitt in analyse.brandabschnitte:
            if abschnitt.feuerwiderstand:
                abschnitt.klasse_ausreichend = (
                    abschnitt.feuerwiderstand.upper() in self.VALID_KLASSEN
                )
                if not abschnitt.klasse_ausreichend:
                    analyse.warnungen.append(
                        f"Unbekannte Feuerwiderstandsklasse: "
                        f"'{abschnitt.feuerwiderstand}' bei '{abschnitt.name}'"
                    )
        return analyse
