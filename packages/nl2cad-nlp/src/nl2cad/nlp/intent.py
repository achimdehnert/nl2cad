"""nl2cad.nlp.intent — Intent-Klassifikation aus NL-Queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class NLIntent(StrEnum):
    RAUMANALYSE = "raumanalyse"
    DIN277 = "din277"
    WOFLV = "woflv"
    MASSENERMITTLUNG = "massenermittlung"
    GAEB_EXPORT = "gaeb_export"
    BRANDSCHUTZ = "brandschutz"
    FLUCHTWEG = "fluchtweg"
    NL2DXF = "nl2dxf"
    UNBEKANNT = "unbekannt"


@dataclass
class IntentResult:
    intent: NLIntent
    confidence: float = 0.0
    entities: dict[str, str] = field(default_factory=dict)
    next_handler: str = ""


_INTENT_PATTERNS: list[tuple[NLIntent, list[str]]] = [
    (
        NLIntent.RAUMANALYSE,
        ["raum", "räume", "fläche", "grundriss", "raumliste"],
    ),
    (NLIntent.DIN277, ["din 277", "din277", "nutzungsart", "nuf", "ngf"]),
    (NLIntent.WOFLV, ["woflv", "wohnfläche", "wohnflächenverordnung"]),
    (
        NLIntent.MASSENERMITTLUNG,
        ["massen", "volumen", "massenermittlung", "mengen"],
    ),
    (
        NLIntent.GAEB_EXPORT,
        ["gaeb", "leistungsverzeichnis", "lv", "ausschreibung"],
    ),
    (
        NLIntent.BRANDSCHUTZ,
        ["brandschutz", "brandabschnitt", "f30", "f60", "f90"],
    ),
    (NLIntent.FLUCHTWEG, ["fluchtweg", "rettungsweg", "notausgang", "asr"]),
    (
        NLIntent.NL2DXF,
        ["zeichne", "erstelle", "generiere", "dxf", "cad-befehl"],
    ),
]


class IntentClassifier:
    """Keyword-basierter Intent-Klassifikator."""

    def classify(self, query: str) -> IntentResult:
        query_lower = query.lower()
        scores: dict[NLIntent, float] = {}
        for intent, keywords in _INTENT_PATTERNS:
            hits = sum(1 for kw in keywords if kw in query_lower)
            if hits:
                scores[intent] = hits / len(keywords)
        if not scores:
            return IntentResult(intent=NLIntent.UNBEKANNT, confidence=0.0)
        best = max(scores, key=lambda k: scores[k])
        return IntentResult(intent=best, confidence=scores[best])
