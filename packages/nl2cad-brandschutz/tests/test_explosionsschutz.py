"""
Tests fuer nl2cad.brandschutz.explosionsschutz.

Testet:
- ExplosionsschutzDokument Invarianten (__post_init__)
- BeurteilungsStatus Enum-Werte
- ist_vollstaendig() mit Pflichtfeldern
- geraetekategorie_fuer_zone()
- to_dict() Struktur
"""

from __future__ import annotations

import pytest

from nl2cad.brandschutz.explosionsschutz import (
    BeurteilungsStatus,
    ExplosionsschutzDokument,
    ExplosionsschutzMassnahme,
)
from nl2cad.brandschutz.models import ExBereich, ExZone


def _make_ex_bereich() -> ExBereich:
    b = ExBereich()
    b.zone = ExZone.ZONE_1
    b.name = "Tankraum"
    b.flaeche_m2 = 25.0
    b.medium = "Gas"
    return b


def _make_vollstaendiges_esd() -> ExplosionsschutzDokument:
    return ExplosionsschutzDokument(
        betrieb_name="Testbetrieb GmbH",
        betriebsstaette="Werk Nord",
        erstellungsdatum="2024-01-15",
        erstellt_von="Max Mustermann",
        naechste_pruefung="2027-01-15",
        gefaehrdungsbeurteilung="GB-2024-001",
        explosionsfaehige_atmosphaere_moeglich=True,
        ex_bereiche=[_make_ex_bereich()],
    )


class TestBeurteilungsStatus:
    def test_should_have_four_states(self):
        states = list(BeurteilungsStatus)
        assert len(states) == 4

    def test_should_have_correct_values(self):
        assert BeurteilungsStatus.VORPRUEFUNG.value == "vorpruefung"
        assert (
            BeurteilungsStatus.NICHT_BEURTEILBAR.value == "nicht_beurteilbar"
        )
        assert BeurteilungsStatus.BESTAETIGT.value == "bestaetigt"
        assert BeurteilungsStatus.ABGELEHNT.value == "abgelehnt"


class TestExplosionsschutzDokumentInvarianten:
    def test_should_create_valid_esd(self):
        esd = _make_vollstaendiges_esd()
        assert esd.betrieb_name == "Testbetrieb GmbH"

    def test_should_raise_on_empty_betrieb_name(self):
        with pytest.raises(ValueError, match="betrieb_name"):
            ExplosionsschutzDokument(
                betrieb_name="",
                erstellungsdatum="2024-01-15",
                naechste_pruefung="2027-01-15",
            )

    def test_should_raise_on_invalid_date_format(self):
        with pytest.raises(ValueError, match="ISO-Datum"):
            ExplosionsschutzDokument(
                betrieb_name="Test GmbH",
                erstellungsdatum="15.01.2024",
                naechste_pruefung="2027-01-15",
            )

    def test_should_raise_when_pruefung_before_erstellung(self):
        with pytest.raises(ValueError, match="naechste_pruefung"):
            ExplosionsschutzDokument(
                betrieb_name="Test GmbH",
                erstellungsdatum="2024-06-01",
                naechste_pruefung="2024-01-01",
            )

    def test_should_raise_when_erstellungsdatum_in_future(self):
        with pytest.raises(ValueError, match="Zukunft"):
            ExplosionsschutzDokument(
                betrieb_name="Test GmbH",
                erstellungsdatum="2099-01-01",
                naechste_pruefung="2100-01-01",
            )


class TestExplosionsschutzDokumentVollstaendig:
    def test_should_be_vollstaendig_with_all_fields(self):
        esd = _make_vollstaendiges_esd()
        assert esd.ist_vollstaendig() is True

    def test_should_not_be_vollstaendig_without_ex_bereiche(self):
        esd = ExplosionsschutzDokument(
            betrieb_name="Test GmbH",
            betriebsstaette="Werk Sued",
            erstellungsdatum="2024-01-15",
            erstellt_von="Max Mustermann",
            naechste_pruefung="2027-01-15",
            gefaehrdungsbeurteilung="GB-001",
        )
        assert esd.ist_vollstaendig() is False

    def test_should_return_geraetekategorie_for_zone1(self):
        esd = _make_vollstaendiges_esd()
        kat = esd.geraetekategorie_fuer_zone(ExZone.ZONE_1)
        assert kat == "KAT2"

    def test_should_return_geraetekategorie_for_zone0(self):
        esd = _make_vollstaendiges_esd()
        kat = esd.geraetekategorie_fuer_zone(ExZone.ZONE_0)
        assert kat == "KAT1"

    def test_should_return_geraetekategorie_for_zone22(self):
        esd = _make_vollstaendiges_esd()
        kat = esd.geraetekategorie_fuer_zone(ExZone.ZONE_22)
        assert kat == "KAT3"

    def test_to_dict_contains_required_keys(self):
        esd = _make_vollstaendiges_esd()
        d = esd.to_dict()
        assert "betrieb_name" in d
        assert "ist_vollstaendig" in d
        assert "ex_bereiche_anzahl" in d
        assert d["ex_bereiche_anzahl"] == 1

    def test_should_contain_norm_versions_in_dict(self):
        esd = _make_vollstaendiges_esd()
        d = esd.to_dict()
        assert "norm_betrsichv" in d
        assert "BetrSichV" in d["norm_betrsichv"]


class TestExplosionsschutzMassnahme:
    def test_should_create_massnahme(self):
        m = ExplosionsschutzMassnahme(
            prioritaet=1,
            typ="Vermeidung",
            beschreibung="Lueftungsanlage erhoehen",
            umgesetzt=False,
            norm_referenz="TRBS 2152 Teil 2",
        )
        assert m.prioritaet == 1
        assert m.umgesetzt is False
