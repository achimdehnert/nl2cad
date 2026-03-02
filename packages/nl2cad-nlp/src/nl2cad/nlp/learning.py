"""nl2cad.nlp.learning — NL Learning Store für Query-Intent-Paare."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LearnedPattern:
    query: str
    intent: str
    confidence: float = 1.0
    source: str = "user_feedback"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    use_count: int = 0


class NLLearningStore:
    """Persistenter JSON-Store für gelernte NL-Patterns."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = (
            data_path or Path.home() / ".nl2cad" / "nl_learning.json"
        )
        self.patterns: list[LearnedPattern] = []
        self._load()

    def add(
        self,
        query: str,
        intent: str,
        confidence: float = 1.0,
        source: str = "user",
    ) -> None:
        self.patterns.append(
            LearnedPattern(
                query=query,
                intent=intent,
                confidence=confidence,
                source=source,
            )
        )
        self._save()

    def find(
        self, query: str, threshold: float = 0.8
    ) -> LearnedPattern | None:
        q = query.lower().strip()
        for p in self.patterns:
            if p.query.lower().strip() == q and p.confidence >= threshold:
                p.use_count += 1
                return p
        return None

    def _load(self) -> None:
        try:
            if self.data_path.exists():
                with open(self.data_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.patterns = [
                        LearnedPattern(**p) for p in data.get("patterns", [])
                    ]
        except Exception as e:
            logger.warning("[NLLearning] Load failed: %s", e)

    def _save(self) -> None:
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"patterns": [asdict(p) for p in self.patterns]},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error("[NLLearning] Save failed: %s", e)
