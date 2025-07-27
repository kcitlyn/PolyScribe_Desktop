from vosk import Model

class LanguageManager:
    data = {
    #"language": ["language code from argos translate", Model("path to language in files"), model url for installation (this is for vosk transcription)]
    #in order to find pathway to file, locate file and open in terminal; then type pwd and copy paste into below section
    "english": ["en", r"C:\Users\kcitl\projects\personal\PolyScribe_Desktop\models\vosk_models\vosk-model-en-us-0.22-lgraph"],
    "mandarin": ["zh", r"C:\Users\kcitl\projects\personal\PolyScribe_Desktop\models\vosk_models\vosk-model-cn-0.22"],
    #add specific languages to ur preferances (visit https://alphacephei.com/vosk/models))
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
    