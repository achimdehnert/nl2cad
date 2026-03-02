"""Tests fuer nl2cad.nlp.nl2dxf.NL2DXFGenerator."""

from __future__ import annotations

import pytest

from nl2cad.nlp.nl2dxf import NL2DXFGenerator, NL2DXFResult


class TestNL2DXFFallback:

    def test_rechteck_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Rechteck 5m x 4m")
        assert result.success
        assert result.used_fallback
        assert len(result.commands) >= 1
        rect = result.commands[0]
        assert rect.command == "RECT"
        assert rect.params["width"] == pytest.approx(5.0)
        assert rect.params["height"] == pytest.approx(4.0)

    def test_raum_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Raum 6x5")
        assert result.success
        assert result.used_fallback
        assert len(result.commands) >= 1
        assert result.commands[0].command == "RECT"
        assert result.commands[0].params["width"] == pytest.approx(6.0)

    def test_kreis_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Kreis Radius 3m")
        assert result.success
        assert result.commands[0].command == "CIRCLE"
        assert result.commands[0].params["radius"] == pytest.approx(3.0)

    def test_kreis_ohne_einheit(self):
        gen = NL2DXFGenerator()
        result = gen.generate("circle radius 2.5")
        assert result.success
        assert result.commands[0].params["radius"] == pytest.approx(2.5)

    def test_linie_erkannt(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Linie von 0 0 nach 10 5")
        assert result.success
        cmd = result.commands[0]
        assert cmd.command == "LINE"
        assert cmd.params["x2"] == pytest.approx(10.0)
        assert cmd.params["y2"] == pytest.approx(5.0)

    def test_unbekannte_beschreibung(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Irgendwas ohne Masse")
        assert result.used_fallback
        assert isinstance(result.commands, list)
        assert result.success

    def test_used_fallback_flag(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Raum 3x3")
        assert result.used_fallback is True

    def test_layer_rooms(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Raum 4x4")
        assert result.commands[0].layer == "Rooms"

    def test_layer_objects_kreis(self):
        gen = NL2DXFGenerator()
        result = gen.generate("Kreis 5")
        assert result.commands[0].layer == "Objects"


class TestParseLLMResponse:

    def test_valid_json(self):
        gen = NL2DXFGenerator()
        json_str = (
            '[{"command": "RECT", "params": {"x":0,"y":0,"width":5,"height":4},'
            ' "layer": "Rooms"}]'
        )
        commands = gen.parse_llm_response(json_str)
        assert len(commands) == 1
        assert commands[0].command == "RECT"
        assert commands[0].params["width"] == 5

    def test_valid_json_multiple(self):
        gen = NL2DXFGenerator()
        json_str = (
            '[{"command":"LINE","params":{"x1":0,"y1":0,"x2":5,"y2":0},"layer":"Lines"},'
            '{"command":"CIRCLE","params":{"cx":0,"cy":0,"radius":3},"layer":"Objects"}]'
        )
        commands = gen.parse_llm_response(json_str)
        assert len(commands) == 2
        assert commands[1].command == "CIRCLE"

    def test_invalid_json_returns_empty(self):
        gen = NL2DXFGenerator()
        commands = gen.parse_llm_response("kein json {{{")
        assert commands == []

    def test_empty_string_returns_empty(self):
        gen = NL2DXFGenerator()
        commands = gen.parse_llm_response("")
        assert commands == []

    def test_json_with_preamble(self):
        gen = NL2DXFGenerator()
        json_str = (
            'Hier ist das Ergebnis:\n'
            '[{"command":"RECT","params":{"x":0,"y":0,"width":3,"height":2},'
            '"layer":"Rooms"}]'
        )
        commands = gen.parse_llm_response(json_str)
        assert len(commands) == 1
        assert commands[0].params["width"] == 3


class TestNL2DXFWithLLM:

    def test_llm_client_used_when_provided(self):
        class FakeLLM:
            def chat(self, system: str, user: str) -> str:
                return (
                    '[{"command":"RECT",'
                    '"params":{"x":0,"y":0,"width":10,"height":8},'
                    '"layer":"Rooms"}]'
                )

        gen = NL2DXFGenerator(llm_client=FakeLLM())
        result = gen.generate("Ein grosses Buero")
        assert result.success
        assert result.used_fallback is False
        assert result.commands[0].params["width"] == 10

    def test_llm_error_falls_back(self):
        class BrokenLLM:
            def chat(self, system: str, user: str) -> str:
                raise ConnectionError("LLM nicht erreichbar")

        gen = NL2DXFGenerator(llm_client=BrokenLLM())
        result = gen.generate("Raum 5x4")
        assert result.success
        assert result.used_fallback is True
        assert "LLM nicht erreichbar" in result.error

    def test_no_llm_uses_fallback(self):
        gen = NL2DXFGenerator(llm_client=None)
        result = gen.generate("Raum 3x3")
        assert result.used_fallback is True


class TestNL2DXFResult:

    def test_default_values(self):
        result = NL2DXFResult(success=True)
        assert result.commands == []
        assert result.raw_llm_response == ""
        assert result.error == ""
        assert result.used_fallback is False
