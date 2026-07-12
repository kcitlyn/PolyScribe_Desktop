from argostranslate import translate

from languages.languages import LanguageManager


class TextTranslator:
    def __init__(self, text, from_language, to_language):
        self.text = text
        self.from_language = from_language
        self.to_language = to_language
        self.from_language_code = LanguageManager.get_code(from_language)
        self.to_language_code = LanguageManager.get_code(to_language)

    def translate_text(self):
        chunk = translate.translate(self.text, self.from_language_code, self.to_language_code)
        print(chunk)
        return chunk

    @staticmethod
    def model_exists(from_language, to_language):
        """Check whether an Argos translation package for this pair is installed."""
        try:
            from_code = LanguageManager.get_code(from_language)
            to_code = LanguageManager.get_code(to_language)
        except ValueError:
            return False
        installed = translate.get_installed_languages()
        from_lang = next((l for l in installed if l.code == from_code), None)
        to_lang = next((l for l in installed if l.code == to_code), None)
        if not from_lang or not to_lang:
            return False
        return from_lang.get_translation(to_lang) is not None
