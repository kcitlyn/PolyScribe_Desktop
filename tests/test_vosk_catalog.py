"""Tests for the Vosk model catalog and download URLs."""

import pytest
from vosk_catalog import VOSK_MODELS, models_by_language, find_model, BASE_URL


class TestCatalogStructure:
    def test_all_entries_have_required_keys(self):
        required = {"name", "lang", "quality", "size", "accuracy", "license", "url"}
        for model in VOSK_MODELS:
            missing = required - model.keys()
            assert not missing, f"{model['name']} missing keys: {missing}"

    def test_urls_match_base_pattern(self):
        for model in VOSK_MODELS:
            expected = f"{BASE_URL}/{model['name']}.zip"
            assert model["url"] == expected, f"URL mismatch for {model['name']}"

    def test_quality_is_valid(self):
        valid = {"small", "medium", "large"}
        for model in VOSK_MODELS:
            assert model["quality"] in valid, f"Bad quality '{model['quality']}' for {model['name']}"

    def test_no_duplicate_names(self):
        names = [m["name"] for m in VOSK_MODELS]
        assert len(names) == len(set(names)), "Duplicate model names found"

    def test_catalog_is_comprehensive(self):
        assert len(VOSK_MODELS) >= 70, f"Expected 70+ models, got {len(VOSK_MODELS)}"

    def test_models_by_language_covers_all(self):
        grouped = models_by_language()
        total = sum(len(v) for v in grouped.values())
        assert total == len(VOSK_MODELS)

    def test_find_model(self):
        m = find_model("vosk-model-small-en-us-0.15")
        assert m is not None
        assert m["lang"] == "English (US)"
        assert m["quality"] == "small"

    def test_find_model_returns_none_for_unknown(self):
        assert find_model("nonexistent-model-xyz") is None


class TestLanguageCoverage:
    """Verify we have the expected breadth of languages."""

    def test_at_least_25_languages(self):
        langs = set(m["lang"] for m in VOSK_MODELS)
        assert len(langs) >= 25, f"Only {len(langs)} languages: {langs}"

    @pytest.mark.parametrize("lang", [
        "English (US)", "Chinese (Mandarin)", "Russian", "French", "German",
        "Spanish", "Portuguese", "Italian", "Japanese", "Korean", "Hindi",
        "Arabic", "Turkish", "Polish", "Dutch", "Ukrainian", "Farsi (Persian)",
        "Vietnamese", "Kazakh", "Swedish", "Gujarati", "Georgian", "Kyrgyz",
    ])
    def test_language_present(self, lang):
        matching = [m for m in VOSK_MODELS if m["lang"] == lang]
        assert matching, f"No models found for language: {lang}"
