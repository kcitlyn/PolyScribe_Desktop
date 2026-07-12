import json
from pathlib import Path

import pyttsx3

from languages.languages import LanguageManager

VOICE_CONFIG_PATH = Path(__file__).resolve().parent / "voice_config.json"

with open(VOICE_CONFIG_PATH, "r") as f:
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
        if voice_config.get("voice_ID"):
            self.engine.setProperty('voice', voice_config["voice_ID"])
        elif "voice_type" in voice_config and self.voices:
            index = min(voice_config["voice_type"], len(self.voices) - 1)
            self.engine.setProperty('voice', self.voices[index].id)

    def get_voice_matches(self, from_language, to_language):
        voice_matches = []
        voice_language = to_language if to_language else from_language
        target_code = LanguageManager.data.get(voice_language, [None, None])[0]
        if target_code is None:
            return None
        for voice in self.voices:
            langs = voice.languages or []
            codes = [l.decode() if isinstance(l, bytes) else str(l) for l in langs]
            if any(code[:2].lower() == target_code for code in codes):
                voice_matches.append(voice.name)

        if voice_matches:
            return voice_matches
        print("No voice model matches were found for desired language")
        return None

    def set_voice_ID(self, voice_name):
        for voice in self.voices:
            if voice_name == voice.name:
                voice_config["voice_ID"] = voice.id
                self.engine.setProperty('voice', voice.id)  # Update immediately
                return
        print("Voice not found.")

    def speak(self, text):
        if isinstance(text, (list, tuple)):
            text = " ".join(text)
        self.engine.say(text)      # Queue the text
        self.engine.runAndWait()

    @staticmethod
    def print_all_voices_available():
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for voice in voices:
            print(voice.name)
