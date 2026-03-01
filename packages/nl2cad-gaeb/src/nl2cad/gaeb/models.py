"""nl2cad.gaeb.models — GAEB Domäne-Dataclasses."""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from enum import Enum


class GAEBPhase(str, Enum):
    X81 = "81"   # Ausschreibung
    X82 = "82"   # Vergabe
    X83 = "83"   # Angebot mit Mengen+Preisen
    X84 = "84"   # Auftragserteilung
    X85 = "85"   # Abrechnung


@dataclass
class Position:
    oz: str                        # Ordnungszahl "01.001"
    kurztext: str
    langtext: str = ""
    menge: Decimal = Decimal("0")
    einheit: str = "m²"
    einheitspreis: Decimal = Decimal("0")
    stlb_code: str = ""

    @property
    def gesamtpreis(self) -> Decimal:
        return self.menge * self.einheitspreis


@dataclass
class LosGruppe:
    oz: str
    bezeichnung: str
    positionen: list[Position] = field(default_factory=list)
    untergruppen: list["LosGruppe"] = field(default_factory=list)

    @property
    def summe(self) -> Decimal:
        pos_sum = sum((p.gesamtpreis for p in self.positionen), Decimal("0"))
        ug_sum = sum((ug.summe for ug in self.untergruppen), Decimal("0"))
        return pos_sum + ug_sum


@dataclass
class Leistungsverzeichnis:
    projekt_name: str
    projekt_nummer: str = ""
    auftraggeber: str = ""
    auftragnehmer: str = ""
    lose: list[LosGruppe] = field(default_factory=list)
    waehrung: str = "EUR"
    datum: date = field(default_factory=date.today)
    phase: GAEBPhase = GAEBPhase.X83

    @property
    def netto_summe(self) -> Decimal:
        return sum((los.summe for los in self.lose), Decimal("0"))

    @property
    def mwst(self) -> Decimal:
        return self.netto_summe * Decimal("0.19")

    @property
    def brutto_summe(self) -> Decimal:
        return self.netto_summe + self.mwst
