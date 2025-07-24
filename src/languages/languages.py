from vosk import Model

class LanguageManager:
    data = {
    #"language": ["language code from argos translate", Model("path to language in files"), model url for installation (this is for vosk transcription)]
    #in order to find pathway to file, locate file and open in terminal; then type pwd and copy paste into below section
    "english": ["en", "/Users/kaitlynchen/rsp5/translator/src/vosk_models/vosk-model-en-us-0.22-lgraph"],
    "mandarin": ["zh", "/Users/kaitlynchen/rsp5/translator/src/vosk_models/vosk-model-small-cn-0.22"],
    "chinese": ["zh", "/Users/kaitlynchen/rsp5/translator/src/vosk_models/vosk-model-small-cn-0.22"],
    "spanish": ["es", "/Users/kaitlynchen/rsp5/translator/src/vosk_models/vosk-model-small-es-0.42"]
    #add specific languages to ur preferances
    }

    @staticmethod
    def get_code(lang):
        code = LanguageManager.data.get(lang, [None, None])[0]
        if code is None:
             raise ValueError(f"No code was found for language '{lang}'. Look at LibreTranslate codes for more information.")
        return code
    
    @staticmethod
    def get_model(lang):
        model = LanguageManager.data.get(lang, [None, None])[1]
        if model is None:
            raise ValueError(f"No model was found for language '{lang}'. Look at LibreTranslate models for more information.")
        return Model(model)
    