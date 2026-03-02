"""nl2cad.nlp.nl2dxf — NL2DXF Generator (framework-agnostisch)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from nl2cad.core.models.dxf import CADCommand, CADCommandType

logger = logging.getLogger(__name__)

_PATTERNS: list[tuple[re.Pattern[str], object]] = [
    (
        re.compile(
            r"(?:rechteck|raum|room|zimmer)?\s*"
            r"(\d+\.?\d*)\s*m?\s*[x×]\s*(\d+\.?\d*)",
            re.IGNORECASE,
        ),
        lambda m: CADCommand(
            CADCommandType.RECT,
            {"x": 0.0, "y": 0.0, "width": float(m.group(1)), "height": float(m.group(2))},
            "Rooms",
        ),
    ),
    (
        re.compile(
            r"(?:kreis|circle)\s*(?:radius\s*|r\s*=?\s*)?(\d+\.?\d*)",
            re.IGNORECASE,
        ),
        lambda m: CADCommand(
            CADCommandType.CIRCLE,
            {"cx": 0.0, "cy": 0.0, "radius": float(m.group(1))},
            "Objects",
        ),
    ),
    (
        re.compile(
            r"linie\s+(?:von\s+)?\(?(\d+\.?\d*)[,\s]+(\d+\.?\d*)\)?"
            r"\s+(?:nach\s+)?\(?(\d+\.?\d*)[,\s]+(\d+\.?\d*)\)?",
            re.IGNORECASE,
        ),
        lambda m: CADCommand(
            CADCommandType.LINE,
            {
                "x1": float(m.group(1)),
                "y1": float(m.group(2)),
                "x2": float(m.group(3)),
                "y2": float(m.group(4)),
            },
            "Lines",
        ),
    ),
]


@dataclass
class NL2DXFResult:
    success: bool
    commands: list[CADCommand] = field(default_factory=list)
    raw_llm_response: str = ""
    error: str = ""
    used_fallback: bool = False


class NL2DXFGenerator:
    """
    Konvertiert natuerlichsprachliche Beschreibungen in CAD-Befehle.

    Zwei Modi:
    1. Mit LLM-Client: Vollstaendige NL-Interpretation via LLM
    2. Ohne LLM-Client (llm_client=None): Regex-Fallback-Parsing
    """

    SYSTEM_PROMPT = (
        "Du bist ein CAD-Assistent. Konvertiere die Beschreibung in JSON.\n"
        "Antworte NUR mit einem JSON-Array aus Objekten mit den Feldern:\n"
        '  "command": string (LINE|RECT|CIRCLE|ARC|TEXT|DOOR|WINDOW|WALL|ROOM)\n'
        '  "params": object (Schluessel/Werte je nach Befehl)\n'
        '  "layer": string\n'
        "Beispiel: "
        '[{"command":"RECT","params":{"x":0,"y":0,"width":5,"height":4},"layer":"Rooms"}]'
    )

    def __init__(self, llm_client: object = None) -> None:
        self.llm_client = llm_client

    def generate(self, description: str, use_llm: bool = True) -> NL2DXFResult:
        """Hauptmethode: NL-Beschreibung → CAD-Befehle."""
        if self.llm_client and use_llm:
            return self._generate_with_llm(description)
        return self._generate_fallback(description)

    def _generate_with_llm(self, description: str) -> NL2DXFResult:
        """LLM-basierte Generierung."""
        try:
            response = self.llm_client.chat(  # type: ignore[union-attr]
                system=self.SYSTEM_PROMPT,
                user=description,
            )
            raw = response if isinstance(response, str) else str(response)
            commands = self.parse_llm_response(raw)
            return NL2DXFResult(
                success=True,
                commands=commands,
                raw_llm_response=raw,
                used_fallback=False,
            )
        except Exception as exc:
            logger.warning("[NL2DXFGenerator] LLM-Fehler: %s — Fallback", exc)
            result = self._generate_fallback(description)
            result.error = str(exc)
            return result

    def _generate_fallback(self, description: str) -> NL2DXFResult:
        """Regex-basiertes Fallback ohne LLM."""
        commands: list[CADCommand] = []
        for pattern, builder in _PATTERNS:
            match = pattern.search(description)
            if match:
                cmd = builder(match)  # type: ignore[operator]
                commands.append(cmd)
        logger.info(
            "[NL2DXFGenerator] fallback: %d Befehle aus '%s'",
            len(commands),
            description[:50],
        )
        return NL2DXFResult(
            success=True,
            commands=commands,
            used_fallback=True,
        )

    def parse_llm_response(self, json_str: str) -> list[CADCommand]:
        """Parsed LLM-JSON-Response in CADCommand-Liste."""
        try:
            json_str = json_str.strip()
            start = json_str.find("[")
            end = json_str.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("Kein JSON-Array gefunden")
            data = json.loads(json_str[start:end])
            commands: list[CADCommand] = []
            for item in data:
                cmd = CADCommand(
                    command=item.get("command", ""),
                    params=item.get("params", {}),
                    layer=item.get("layer", "0"),
                )
                commands.append(cmd)
            return commands
        except Exception as exc:
            logger.warning("[NL2DXFGenerator] JSON-Parse-Fehler: %s", exc)
            return []
