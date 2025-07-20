from argostranslate import translate
from languages.languages import LanguageManager

class TextTranslator:
    def __init__(self, text, from_language, to_language):
            self.text= text
            self.from_language= from_language
            self.to_language= to_language
            self.from_language_code= LanguageManager.get_code(from_language)
            self.to_language_code= LanguageManager.get_code(to_language)

    def translate_text(self):
        print(translate.translate(self.text, self.from_language_code, self.to_language_code)) 