"""
Tests fuer nl2cad.nlp.learning.NLLearningStore.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nl2cad.nlp.learning import LearnedPattern, NLLearningStore


@pytest.fixture
def tmp_store(tmp_path: Path) -> NLLearningStore:
    store_path = tmp_path / "test_learning.json"
    return NLLearningStore(data_path=store_path)


class TestLearnedPattern:
    def test_should_create_with_defaults(self):
        p = LearnedPattern(query="Zeige Räume", intent="raumanalyse")
        assert p.query == "Zeige Räume"
        assert p.intent == "raumanalyse"
        assert p.confidence == 1.0
        assert p.source == "user_feedback"
        assert p.use_count == 0
        assert p.created_at != ""


class TestNLLearningStoreBasic:
    def test_should_create_empty_store(self, tmp_store):
        assert len(tmp_store.patterns) == 0

    def test_should_add_pattern(self, tmp_store):
        tmp_store.add("Zeige alle Räume", "raumanalyse")
        assert len(tmp_store.patterns) == 1

    def test_should_find_exact_match(self, tmp_store):
        tmp_store.add("DIN 277 berechnen", "din277")
        result = tmp_store.find("DIN 277 berechnen")
        assert result is not None
        assert result.intent == "din277"

    def test_should_return_none_for_unknown_query(self, tmp_store):
        tmp_store.add("DIN 277 berechnen", "din277")
        result = tmp_store.find("Wetter heute?")
        assert result is None

    def test_should_increment_use_count_on_find(self, tmp_store):
        tmp_store.add("GAEB Export", "gaeb_export")
        tmp_store.find("GAEB Export")
        result = tmp_store.find("GAEB Export")
        assert result is not None
        assert result.use_count >= 1

    def test_should_respect_threshold(self, tmp_store):
        tmp_store.add("Test Query", "raumanalyse", confidence=0.5)
        result = tmp_store.find("Test Query", threshold=0.8)
        assert result is None

    def test_find_case_insensitive(self, tmp_store):
        tmp_store.add("zeige räume", "raumanalyse")
        result = tmp_store.find("ZEIGE RÄUME")
        assert result is not None


class TestNLLearningStorePersistence:
    def test_should_persist_to_json(self, tmp_path):
        store_path = tmp_path / "persist.json"
        store1 = NLLearningStore(data_path=store_path)
        store1.add("Fluchtweg prüfen", "brandschutz")
        assert store_path.exists()

    def test_should_reload_from_json(self, tmp_path):
        store_path = tmp_path / "reload.json"
        store1 = NLLearningStore(data_path=store_path)
        store1.add("Fluchtweg prüfen", "brandschutz")

        store2 = NLLearningStore(data_path=store_path)
        assert len(store2.patterns) == 1
        assert store2.patterns[0].intent == "brandschutz"

    def test_should_handle_missing_file_gracefully(self, tmp_path):
        store_path = tmp_path / "nonexistent.json"
        store = NLLearningStore(data_path=store_path)
        assert len(store.patterns) == 0

    def test_should_handle_corrupt_json_gracefully(self, tmp_path):
        store_path = tmp_path / "corrupt.json"
        store_path.write_text("{ invalid json }", encoding="utf-8")
        store = NLLearningStore(data_path=store_path)
        assert len(store.patterns) == 0
