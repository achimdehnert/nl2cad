"""
Tests fuer nl2cad.brandschutz.report.BrandschutzkonzeptReport.
"""

from __future__ import annotations

from nl2cad.brandschutz.explosionsschutz import BeurteilungsStatus
from nl2cad.brandschutz.gebaeudeklasse import (
    Gebaeudeklasse,
    GebaeudeklasseResult,
)
from nl2cad.brandschutz.models import BrandschutzAnalyse, MaengelSchwere
from nl2cad.brandschutz.report import BrandschutzkonzeptReport


def _make_gk(gk: Gebaeudeklasse = Gebaeudeklasse.GK_3) -> GebaeudeklasseResult:
    return GebaeudeklasseResult(gebaeudeklasse=gk, norm_version="MBO 2024")


def _make_analyse(kritisch: bool = False) -> BrandschutzAnalyse:
    analyse = BrandschutzAnalyse()
    if kritisch:
        from nl2cad.brandschutz.models import BrandschutzMangel

        analyse.maengel.append(
            BrandschutzMangel(
                beschreibung="Fluchtweg zu lang",
                schwere=MaengelSchwere.KRITISCH,
                regelwerk="ASR A2.3",
            )
        )
    return analyse


class TestBrandschutzkonzeptReportErstellung:
    def test_should_create_with_required_fields(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        assert report is not None
        assert report.erstellt_am != ""

    def test_should_set_erstellt_am_automatically(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        assert len(report.erstellt_am) >= 10

    def test_should_default_to_vorpruefung(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        assert report.beurteilungs_status == BeurteilungsStatus.VORPRUEFUNG


class TestBrandschutzkonzeptReportStatus:
    def test_should_be_nicht_beurteilbar_for_unknown_gk(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(Gebaeudeklasse.UNBEKANNT),
            brandschutz_analyse=_make_analyse(),
        )
        assert (
            report.beurteilungs_status == BeurteilungsStatus.NICHT_BEURTEILBAR
        )
        assert any("Gebaeudeklasse" in m for m in report.meldungen)

    def test_should_be_nicht_beurteilbar_for_zero_quality_score(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
            quality_score=0.0,
        )
        assert (
            report.beurteilungs_status == BeurteilungsStatus.NICHT_BEURTEILBAR
        )
        assert any("score=0.0" in m for m in report.meldungen)

    def test_should_be_abgelehnt_with_kritische_maengel(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(kritisch=True),
        )
        assert report.beurteilungs_status == BeurteilungsStatus.ABGELEHNT
        assert any("ABGELEHNT" in m for m in report.meldungen)

    def test_should_be_vorpruefung_without_maengel(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(kritisch=False),
        )
        assert report.beurteilungs_status == BeurteilungsStatus.VORPRUEFUNG
        assert any("Vorpruefung" in m for m in report.meldungen)


class TestBrandschutzkonzeptReportProperties:
    def test_hat_ex_bereiche_false_without_esd(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        assert report.hat_ex_bereiche is False

    def test_warnungen_gesamt_aggregiert(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        warnungen = report.warnungen_gesamt
        assert isinstance(warnungen, list)

    def test_berechne_hash_returns_sha256(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        h = report.berechne_hash()
        assert len(h) == 64
        assert report.report_hash == h

    def test_to_dict_contains_required_keys(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        d = report.to_dict()
        assert "erstellt_am" in d
        assert "beurteilungs_status" in d
        assert "gebaeudeklasse" in d
        assert "brandschutz" in d
        assert "meldungen" in d

    def test_to_dict_explosionsschutz_none_when_absent(self):
        report = BrandschutzkonzeptReport(
            gebaeudeklasse_result=_make_gk(),
            brandschutz_analyse=_make_analyse(),
        )
        assert report.to_dict()["explosionsschutz"] is None
