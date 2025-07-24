import pyttsx3
import json

from languages.languages import LanguageManager

with open("languages/voice_config.json", "r") as f:
    voice_config = json.load(f)

class Speak:
    def __init__(self, speed_of_voice, volume):
        self.engine = pyttsx3.init()

        voice_config["speed_of_voice"] = speed_of_voice
        voice_config["volume"] = volume
        self.voices = self.engine.getProperty('voices')

        self.voice_setup()  # Setup voice properties right after init

    def voice_setup(self):
        self.engine.setProperty('rate', voice_config["speed_of_voice"])
        self.engine.setProperty('volume', voice_config["volume"])
        
        # Use voice_ID if set, otherwise fallback to voice_type index
        if "voice_ID" in voice_config and voice_config["voice_ID"]:
            self.engine.setProperty('voice', voice_config["voice_ID"])
        else:
            # voice_type is expected to be an int index
            self.engine.setProperty('voice', self.voices[voice_config["voice_type"]].id)

    def get_voice_matches(self, from_language, to_language):
        voice_matches = []
        voice_language = to_language if to_language else from_language
        for voice in self.voices:
            if voice.languages and voice.languages[0][:2] == LanguageManager.data.get(voice_language, [None, None])[0]:
                voice_matches.append(voice.name)

        if voice_matches:
            return voice_matches
        else:
            print("No voice model matches were found for desired language")
            return None

    def set_voice_ID(self, voice_name):
        for voice in self.voices:
            if voice_name == voice.name:
                voice_config["voice_ID"] = voice.id
                self.engine.setProperty('voice', voice.id)  # Update immediately
                return
        print("Voice name not found.")
        
    def speak(self, text):
        self.engine.say(text)      # Queue the text
        self.engine.runAndWait()