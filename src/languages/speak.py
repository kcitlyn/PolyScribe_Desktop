import pyttsx3
import json
from languages import LanguageManager

with open("voice_config.json", "r") as f:
    voice_config=json.load(f)
    
class Speak:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices') 

    def voice_setup(self):
        self.engine.setProperty('rate', voice_config["speed_of_voice"]) 
        self.engine.setProperty('volume',voice_config["volume"]) 
        self.engine.setProperty('voice', self.voices[voice_config["voice_type"]].id) 

    def get_voice_matches(self, from_language, to_language):
        voice_matches=[]
        if to_language== None:
            voice_language= from_language
        else:
            voice_language= to_language
        for voice in self.voices:
            if voice.languages[0][:2] == LanguageManager.data.get(voice_language, [None, None])[0]:
                voice_matches.append(voice.name)

        if voice_matches:
            return voice_matches
        else:
            print("no voice model matches were found for desired language")
            return None

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
