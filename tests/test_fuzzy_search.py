"""Tests for typo-tolerant fuzzy model search."""

from fuzzy_search import search_models, search_argos_packages
from vosk_catalog import VOSK_MODELS


class TestSearchModels:
    def test_empty_query_returns_everything(self):
        assert len(search_models("", VOSK_MODELS)) == len(VOSK_MODELS)
        assert len(search_models("   ", VOSK_MODELS)) == len(VOSK_MODELS)

    def test_exact_language(self):
        results = search_models("japanese", VOSK_MODELS)
        assert results
        assert all(m["lang"] == "Japanese" for m in results[:2])

    def test_typo_tolerant(self):
        results = search_models("japanse", VOSK_MODELS)  # missing 'e'
        assert any(m["lang"] == "Japanese" for m in results)

    def test_typo_english(self):
        results = search_models("englsh", VOSK_MODELS)
        assert any("English" in m["lang"] for m in results)

    def test_partial_word(self):
        results = search_models("port", VOSK_MODELS)
        assert any(m["lang"] == "Portuguese" for m in results)

    def test_multi_token_narrows(self):
        results = search_models("german large", VOSK_MODELS)
        assert results
        assert all(m["lang"] == "German" for m in results[:2])
        assert any(m["quality"] == "large" for m in results)

    def test_gibberish_returns_nothing(self):
        assert search_models("zzqqxxyy", VOSK_MODELS) == []

    def test_best_match_ranked_first(self):
        results = search_models("korean", VOSK_MODELS)
        assert results[0]["lang"] == "Korean"

    def test_search_by_model_name(self):
        results = search_models("lgraph", VOSK_MODELS)
        assert any("lgraph" in m["name"] for m in results)


class TestSearchArgosPackages:
    PACKAGES = [
        {"from_name": "English", "to_name": "Spanish", "from_code": "en", "to_code": "es"},
        {"from_name": "English", "to_name": "Japanese", "from_code": "en", "to_code": "ja"},
        {"from_name": "French", "to_name": "English", "from_code": "fr", "to_code": "en"},
    ]

    def test_empty_returns_all(self):
        assert len(search_argos_packages("", self.PACKAGES)) == 3

    def test_by_language(self):
        results = search_argos_packages("spanish", self.PACKAGES)
        assert len(results) == 1
        assert results[0]["to_name"] == "Spanish"

    def test_typo(self):
        results = search_argos_packages("japanse", self.PACKAGES)
        assert any(p["to_name"] == "Japanese" for p in results)

    def test_pair_query(self):
        results = search_argos_packages("french english", self.PACKAGES)
        assert results
        assert results[0]["from_name"] == "French"
