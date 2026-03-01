"""
Integration Test: Vollständige nl2cad Pipeline ohne Django.
Zeigt wie cad-hub die Library nutzt.
"""
import pytest
from nl2cad.areas.din277 import DIN277Calculator
from nl2cad.areas.woflv import WoFlVCalculator
from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer
from nl2cad.brandschutz.models import BrandschutzAnalyse, Fluchtweg
from nl2cad.core.handlers.base import BaseCADHandler, CADHandlerPipeline, HandlerResult, HandlerStatus
from nl2cad.gaeb.converter import IFCX83Converter
from nl2cad.gaeb.models import Leistungsverzeichnis
from nl2cad.nlp.intent import IntentClassifier, NLIntent


# ---------------------------------------------------------------------------
# Beispiel-Handler für Integration-Test
# ---------------------------------------------------------------------------

class MockRoomAnalysisHandler(BaseCADHandler):
    """Simuliert RoomAnalysisHandler mit fixen Testdaten."""
    name = "MockRoomAnalysis"

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name, status=HandlerStatus.SUCCESS)
        result.data["rooms"] = [
            {"name": "Büro 1", "area_m2": 25.0, "height_m": 2.8},
            {"name": "Büro 2", "area_m2": 18.0, "height_m": 2.8},
            {"name": "Flur",   "area_m2": 12.0, "height_m": 2.5},
            {"name": "WC",     "area_m2":  4.0, "height_m": 2.5},
        ]
        return result


class MockDIN277Handler(BaseCADHandler):
    """Berechnet DIN 277 aus Pipeline-Context."""
    name = "DIN277Analysis"
    required_inputs = ["rooms"]

    def execute(self, input_data: dict) -> HandlerResult:
        calc = DIN277Calculator()
        din277_result = calc.calculate(input_data["rooms"])
        result = HandlerResult(success=True, handler_name=self.name, status=HandlerStatus.SUCCESS)
        result.data["din277"] = din277_result.to_dict()
        return result


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_pipeline_room_to_din277(self):
        """Pipeline: Raumerkennung → DIN 277."""
        pipeline = CADHandlerPipeline()
        pipeline.add(MockRoomAnalysisHandler())
        pipeline.add(MockDIN277Handler())

        pipeline.run({})

        assert pipeline.success
        ctx = pipeline.get_context()
        assert "rooms" in ctx
        assert "din277" in ctx
        # Büro1(25) + Büro2(18) + WC(4→NUF_8) = 47 NUF; Flur(12) = VF
        assert ctx["din277"]["nutzungsflaeche_m2"] == pytest.approx(47.0)
        assert ctx["din277"]["verkehrsflaeche_m2"] == pytest.approx(12.0)

    def test_pipeline_missing_input_fails(self):
        """Pipeline stoppt bei fehlendem required_input."""
        pipeline = CADHandlerPipeline()
        pipeline.add(MockDIN277Handler())  # rooms fehlt im initial context

        pipeline.run({})

        assert not pipeline.success
        assert len(pipeline.errors) > 0

    def test_pipeline_continue_on_error(self):
        """Pipeline mit continue_on_error läuft durch."""
        pipeline = CADHandlerPipeline(continue_on_error=True)
        pipeline.add(MockDIN277Handler())   # rooms fehlt → Error
        pipeline.add(MockRoomAnalysisHandler())  # läuft trotzdem

        pipeline.run({})

        assert len(pipeline._results) == 2

    def test_ifc_data_to_gaeb(self):
        """IFC-Daten → GAEB X83 XML."""
        ifc_data = {
            "project_name": "Testprojekt",
            "rooms": [
                {"name": "Büro 1", "area_m2": 25.0, "perimeter_m": 20.0},
                {"name": "Büro 2", "area_m2": 18.0, "perimeter_m": 17.0},
            ]
        }
        converter = IFCX83Converter()
        xml_bytes = converter.convert_to_x83(ifc_data, projekt_name="Testprojekt")

        content = xml_bytes.read()
        assert len(content) > 0
        assert b"GAEB" in content
        assert b"Testprojekt" in content

    def test_brandschutz_pipeline_integration(self):
        """BrandschutzAnalyze → Mängel-Report."""
        analyse = BrandschutzAnalyse()
        analyse.fluchtwege = [
            Fluchtweg(name="Fluchtweg EG", laenge_m=70.0, breite_m=0.6, hat_notausgang=False),
        ]

        from nl2cad.brandschutz.rules.asr_a23 import ASRA23Validator
        validator = ASRA23Validator()
        result = validator.validate(analyse)

        # 70m > 60m → kritisch
        # 0.6m < 0.875m → kritisch
        # kein Notausgang → kritisch
        assert result.hat_kritische_maengel
        assert len(result.kritische_maengel) >= 2

    def test_intent_to_handler_routing(self):
        """NL-Query → Intent → Handler-Auswahl (konzeptionell)."""
        classifier = IntentClassifier()

        cases = [
            ("Zeige alle Räume und ihre Flächen", NLIntent.RAUMANALYSE),
            ("Berechne DIN 277 Nutzungsarten", NLIntent.DIN277),
            ("Fluchtweglängen prüfen ASR", NLIntent.FLUCHTWEG),
            ("GAEB Leistungsverzeichnis exportieren", NLIntent.GAEB_EXPORT),
        ]

        for query, expected_intent in cases:
            result = classifier.classify(query)
            assert result.intent == expected_intent, f"Query '{query}' → {result.intent} statt {expected_intent}"
            assert result.confidence > 0
