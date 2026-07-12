"""Tests for TextTranslator (no model required, tests interface/validation only)."""

import pytest
from unittest.mock import patch, MagicMock
from translation.text_translate import TextTranslator
from languages.languages import LanguageManager


class TestTextTranslatorInit:
    def test_raises_on_unknown_source(self):
        with pytest.raises(ValueError):
            TextTranslator("hello", "klingon", "english")

    def test_raises_on_unknown_target(self):
        # Only fails if at least one language IS valid
        if "english" in LanguageManager.data:
            with pytest.raises(ValueError):
                TextTranslator("hello", "english", "klingon")


class TestModelExists:
    @patch("translation.text_translate.translate")
    def test_returns_false_when_no_installed_packages(self, mock_translate):
        mock_translate.get_installed_languages.return_value = []
        assert TextTranslator.model_exists("english", "spanish") is False

    def test_returns_false_for_unknown_language(self):
        assert TextTranslator.model_exists("klingon", "elvish") is False
