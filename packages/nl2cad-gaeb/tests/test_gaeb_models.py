"""Tests fuer nl2cad.gaeb.models."""

from __future__ import annotations

from decimal import Decimal

import pytest

from nl2cad.gaeb.models import (
    GAEBPhase,
    Leistungsverzeichnis,
    LosGruppe,
    Position,
)


class TestPosition:
    def test_gesamtpreis_ep_mal_menge(self):
        pos = Position(
            oz="01.001",
            kurztext="Bodenbelag",
            menge=Decimal("25.0"),
            einheitspreis=Decimal("45.00"),
        )
        assert pos.gesamtpreis == Decimal("1125.00")

    def test_gesamtpreis_null_wenn_kein_preis(self):
        pos = Position(oz="01.001", kurztext="Test")
        assert pos.gesamtpreis == Decimal("0")

    def test_gesamtpreis_mit_nachkommastellen(self):
        pos = Position(
            oz="01.001",
            kurztext="Test",
            menge=Decimal("3.5"),
            einheitspreis=Decimal("10.50"),
        )
        assert pos.gesamtpreis == Decimal("36.75")

    def test_default_einheit_ist_m2(self):
        pos = Position(oz="01.001", kurztext="Test")
        assert pos.einheit == "m²"


class TestLosGruppe:
    def test_summe_aller_positionen(self):
        los = LosGruppe(
            oz="01",
            bezeichnung="Bodenbelaege",
            positionen=[
                Position(
                    oz="01.001",
                    kurztext="A",
                    menge=Decimal("10"),
                    einheitspreis=Decimal("5"),
                ),
                Position(
                    oz="01.002",
                    kurztext="B",
                    menge=Decimal("20"),
                    einheitspreis=Decimal("3"),
                ),
            ],
        )
        assert los.summe == Decimal("110")

    def test_summe_mit_untergruppen(self):
        ug = LosGruppe(
            oz="01.01",
            bezeichnung="Untergruppe",
            positionen=[
                Position(
                    oz="01.01.001",
                    kurztext="C",
                    menge=Decimal("5"),
                    einheitspreis=Decimal("10"),
                ),
            ],
        )
        los = LosGruppe(
            oz="01",
            bezeichnung="Hauptgruppe",
            positionen=[
                Position(
                    oz="01.001",
                    kurztext="A",
                    menge=Decimal("10"),
                    einheitspreis=Decimal("5"),
                ),
            ],
            untergruppen=[ug],
        )
        assert los.summe == Decimal("100")

    def test_summe_leer_ist_null(self):
        los = LosGruppe(oz="01", bezeichnung="Leer")
        assert los.summe == Decimal("0")


class TestLeistungsverzeichnis:
    def test_default_phase_ist_x83(self):
        lv = Leistungsverzeichnis(projekt_name="Test")
        assert lv.phase == GAEBPhase.X83

    def test_netto_summe_leer(self):
        lv = Leistungsverzeichnis(projekt_name="Test")
        assert lv.netto_summe == Decimal("0")

    def test_brutto_summe_mit_mwst(self, simple_lv):
        netto = simple_lv.netto_summe
        expected_brutto = netto * Decimal("1.19")
        assert float(simple_lv.brutto_summe) == pytest.approx(
            float(expected_brutto), rel=1e-6
        )

    def test_mwst_19_prozent(self, simple_lv):
        expected = simple_lv.netto_summe * Decimal("0.19")
        assert simple_lv.mwst == expected

    def test_netto_summe_mehrere_lose(self):
        lv = Leistungsverzeichnis(
            projekt_name="Test",
            lose=[
                LosGruppe(
                    oz="01",
                    bezeichnung="A",
                    positionen=[
                        Position(
                            oz="01.001",
                            kurztext="X",
                            menge=Decimal("10"),
                            einheitspreis=Decimal("10"),
                        ),
                    ],
                ),
                LosGruppe(
                    oz="02",
                    bezeichnung="B",
                    positionen=[
                        Position(
                            oz="02.001",
                            kurztext="Y",
                            menge=Decimal("5"),
                            einheitspreis=Decimal("20"),
                        ),
                    ],
                ),
            ],
        )
        assert lv.netto_summe == Decimal("200")
