from vosk import Model
from pathlib import Path

class LanguageManager:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent 
    data = {
    #"language": ["language code from argos translate", relative model path to vosk language file]
    #create a folder in models folder titled "vosk_models" and put all the languages you want to use and modify code
    "english": ["en", BASE_DIR / "models" / "vosk_models" / "vosk-model-en-us-0.22-lgraph"], #example code
    "mandarin": ["zh", BASE_DIR / "models" / "vosk_models" / "vosk-model-cn-0.22"],
    #add specific languages based on your needs and preferances (visit https://alphacephei.com/vosk/models))
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
        return Model(str(model))
