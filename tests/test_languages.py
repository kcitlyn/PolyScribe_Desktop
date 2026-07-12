"""Tests for language detection and management."""

import pytest
from languages.languages import language_from_model_name, LanguageManager, VOSK_NAME_TO_LANGUAGE


class TestLanguageFromModelName:
    def test_english_small(self):
        assert language_from_model_name("vosk-model-small-en-us-0.15") == ("english", "en")

    def test_mandarin(self):
        assert language_from_model_name("vosk-model-cn-0.22") == ("mandarin", "zh")

    def test_french(self):
        assert language_from_model_name("vosk-model-small-fr-0.22") == ("french", "fr")

    def test_japanese(self):
        assert language_from_model_name("vosk-model-small-ja-0.22") == ("japanese", "ja")

    def test_unknown_returns_none(self):
        assert language_from_model_name("vosk-model-small-xx-0.1") is None

    def test_case_insensitive(self):
        assert language_from_model_name("Vosk-Model-Small-EN-US-0.15") == ("english", "en")


class TestLanguageManager:
    def test_get_code_raises_for_unknown(self):
        with pytest.raises(ValueError, match="No code was found"):
            LanguageManager.get_code("klingon")

    def test_get_model_path_raises_for_unknown(self):
        with pytest.raises(ValueError, match="No Vosk model was found"):
            LanguageManager.get_model_path("klingon")

    def test_refresh_returns_dict(self):
        result = LanguageManager.refresh()
        assert isinstance(result, dict)

    def test_data_structure(self):
        for lang_name, entry in LanguageManager.data.items():
            assert isinstance(lang_name, str)
            assert len(entry) == 2
            code, path = entry
            assert isinstance(code, str)
            assert len(code) >= 2


class TestVoskNameMapping:
    def test_all_values_have_two_parts(self):
        for fragment, (name, code) in VOSK_NAME_TO_LANGUAGE.items():
            assert len(code) >= 2
            assert len(name) >= 2
