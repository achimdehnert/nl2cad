"""
Tests für nl2cad-brandschutz — ASR A2.3 Regelwerk-Checks.
"""

from nl2cad.brandschutz.models import (
    BrandschutzAnalyse,
    Fluchtweg,
    MaengelSchwere,
)
from nl2cad.brandschutz.rules.asr_a23 import (
    ASRA23Validator,
)


class TestASRA23Validator:
    def setup_method(self):
        self.validator = ASRA23Validator()

    def test_ok_fluchtweg(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW EG", laenge_m=20.0, breite_m=1.2, hat_notausgang=True
            )
        )
        result = self.validator.validate(analyse)
        assert len(result.kritische_maengel) == 0
        assert analyse.fluchtwege[0].laenge_ok is True
        assert analyse.fluchtwege[0].breite_ok is True

    def test_zu_langer_fluchtweg(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW EG", laenge_m=65.0, breite_m=1.0, hat_notausgang=True
            )
        )
        result = self.validator.validate(analyse)
        kritisch = [
            m for m in result.maengel if m.schwere == MaengelSchwere.KRITISCH
        ]
        assert len(kritisch) >= 1
        assert "65.0m" in kritisch[0].beschreibung
        assert "ASR A2.3" in kritisch[0].regelwerk

    def test_grenzwert_fluchtweg_35m_warnung(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW EG", laenge_m=45.0, breite_m=1.0, hat_notausgang=True
            )
        )
        result = self.validator.validate(analyse)
        warnungen = [
            m for m in result.maengel if m.schwere == MaengelSchwere.WARNUNG
        ]
        assert any("Richtungsänderung" in w.beschreibung for w in warnungen)

    def test_zu_schmaler_fluchtweg(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW OG", laenge_m=15.0, breite_m=0.5, hat_notausgang=True
            )
        )
        result = self.validator.validate(analyse)
        kritisch = result.kritische_maengel
        assert len(kritisch) >= 1
        assert analyse.fluchtwege[0].breite_ok is False

    def test_kein_notausgang_kritisch(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW EG", laenge_m=20.0, breite_m=1.0, hat_notausgang=False
            )
        )
        result = self.validator.validate(analyse)
        assert result.hat_kritische_maengel

    def test_keine_fluchtwege_warnung(self):
        analyse = BrandschutzAnalyse()
        result = self.validator.validate(analyse)
        assert len(result.maengel) >= 1
        assert any(
            "Keine Fluchtwege" in m.beschreibung for m in result.maengel
        )

    def test_laenge_nicht_pruefbar(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(name="FW", laenge_m=0.0, hat_notausgang=True)
        )
        self.validator.validate(analyse)
        assert analyse.fluchtwege[0].laenge_ok is None

    def test_to_dict(self):
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege.append(
            Fluchtweg(
                name="FW", laenge_m=25.0, breite_m=1.2, hat_notausgang=True
            )
        )
        self.validator.validate(analyse)
        d = analyse.to_dict()
        assert "fluchtwege_count" in d
        assert "maengel" in d
        assert d["fluchtwege_count"] == 1
