import re
from pathlib import Path

from vosk import Model

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VOSK_MODELS_DIR = BASE_DIR / "models" / "vosk_models"
TRANSLATION_MODELS_DIR = BASE_DIR / "models" / "translation_models"

# Maps the language fragment used in Vosk model folder names
# (e.g. "vosk-model-small-en-us-0.15" -> "en-us") to a
# (language name, ISO/Argos language code) pair.
VOSK_NAME_TO_LANGUAGE = {
    "en-us": ("english", "en"),
    "en-in": ("english (indian)", "en"),
    "en-gb": ("english (british)", "en"),
    "cn": ("mandarin", "zh"),
    "ru": ("russian", "ru"),
    "fr": ("french", "fr"),
    "de": ("german", "de"),
    "es": ("spanish", "es"),
    "pt": ("portuguese", "pt"),
    "el-gr": ("greek", "el"),
    "tr": ("turkish", "tr"),
    "vn": ("vietnamese", "vi"),
    "it": ("italian", "it"),
    "nl": ("dutch", "nl"),
    "ca": ("catalan", "ca"),
    "ar": ("arabic", "ar"),
    "fa": ("persian", "fa"),
    "tl-ph": ("filipino", "tl"),
    "uk": ("ukrainian", "uk"),
    "kz": ("kazakh", "kk"),
    "sv": ("swedish", "sv"),
    "ja": ("japanese", "ja"),
    "eo": ("esperanto", "eo"),
    "hi": ("hindi", "hi"),
    "cs": ("czech", "cs"),
    "pl": ("polish", "pl"),
    "ko": ("korean", "ko"),
    "uz": ("uzbek", "uz"),
    "ky": ("kyrgyz", "ky"),
    "ka": ("georgian", "ka"),
    "ar-tn": ("arabic (tunisian)", "ar"),
    "br": ("breton", "br"),
    "gu": ("gujarati", "gu"),
    "tg": ("tajik", "tg"),
    "te": ("telugu", "te"),
}

# Longest fragments first so "en-us" wins over a hypothetical "en".
_FRAGMENTS = sorted(VOSK_NAME_TO_LANGUAGE, key=len, reverse=True)


def language_from_model_name(folder_name):
    """Return (language name, code) parsed from a Vosk model folder name, or None."""
    name = folder_name.lower()
    for fragment in _FRAGMENTS:
        if re.search(rf"(?:^|-){re.escape(fragment)}(?:-|$)", name):
            return VOSK_NAME_TO_LANGUAGE[fragment]
    return None


class LanguageManager:
    BASE_DIR = BASE_DIR
    # "language name": [argos language code, path to vosk model folder]
    data = {}
    _model_cache = {}

    @classmethod
    def refresh(cls):
        """Scan models/vosk_models and rebuild the available-language table."""
        cls.data = {}
        if VOSK_MODELS_DIR.is_dir():
            for folder in sorted(VOSK_MODELS_DIR.iterdir()):
                if not folder.is_dir():
                    continue
                parsed = language_from_model_name(folder.name)
                if parsed:
                    name, code = parsed
                    cls.data[name] = [code, folder]
        return cls.data

    @staticmethod
    def get_code(lang):
        code = LanguageManager.data.get(lang, [None, None])[0]
        if code is None:
            raise ValueError(
                f"No code was found for language '{lang}'. "
                f"Available languages: {', '.join(LanguageManager.data) or 'none'}"
            )
        return code

    @staticmethod
    def get_model_path(lang):
        path = LanguageManager.data.get(lang, [None, None])[1]
        if path is None:
            raise ValueError(
                f"No Vosk model was found for language '{lang}'. "
                f"Download one into {VOSK_MODELS_DIR} (see https://alphacephei.com/vosk/models)."
            )
        return path

    @staticmethod
    def get_model(lang):
        path = LanguageManager.get_model_path(lang)
        if lang not in LanguageManager._model_cache:
            LanguageManager._model_cache[lang] = Model(str(path))
        return LanguageManager._model_cache[lang]


LanguageManager.refresh()
