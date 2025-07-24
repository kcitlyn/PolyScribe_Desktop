import sounddevice as sd
import time

from languages.languages import LanguageManager
from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor
from languages.speak import Speak

def prompt_choice(prompt, valid_options):
    while True:
        user_input = input(prompt).strip()
        if user_input in valid_options:
            return user_input
        print(f"Invalid input. Choose from: {', '.join(valid_options)}")
        
def get_device_id():
    print(sd.query_devices())
    return int(prompt_choice("Which number microphone do you want to use? ", [str(i) for i in range(len(sd.query_devices()))]))

def get_sample_rate(device_ID):
    return sd.query_devices(device_ID)['default_samplerate']

def get_instruction():
    return int(prompt_choice(
        "Do you want me to transcribe what you say only (1) or translate as well (2)? ", ["1", "2"]))

def get_languages():
    return prompt_choice("What language will you speak in? ", list(LanguageManager.data.keys())).lower()

def get_speaker_pref(from_language, to_language):
    answer= prompt_choice("Do you want the output speech to be read aloud? (y or n) ", ["y", "n"])
    if answer== "y":
        speed_of_voice= (int(prompt_choice("how many wpm do you want the voice to speak? (100-500 wpm) ",
                                            [str(i) for i in range(100, 501)])))
        volume=(int(prompt_choice("enter an integer between 0-100 for volume. ", [str(i) for i in range(101)])))/100 
        speaker= Speak(speed_of_voice, volume)
        voice_matches=speaker.get_voice_matches(from_language, to_language)
        print(voice_matches)
        if voice_matches:
            voice_ID=prompt_choice("here are the choice you have based on the language selected. Choose a model (type the name exactly)", voice_matches)
            speaker.set_voice_ID(voice_ID)
            return speaker
        else:
            print("unfortunately, the language you have chosen is not compatible with any voice models. translation or transcription will proceed as normal just without a voice")
            return None
    else:
        return None

def run_transcription(from_language, sample_rate, device_ID, purpose):
    speaker = get_speaker_pref(from_language, from_language)
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    speaker.voice_setup()
    last_partial = ""
    transcription_chunks=[]
    for chunk, is_final in transcriber.processing_audio():  # generator yields (text, is_final)
        try:
            if is_final:
                print('\r' + chunk + ' ' * max(0, len(last_partial) - len(chunk)), end='', flush=True)
                last_partial = ""
                print()
                if speaker and purpose == "transcription":
                    print(f"Main thread adding chunk to queue: {chunk}")
                    transcription_chunks.append(chunk)
            else:
                print('\r' + chunk + ' ' * (len(last_partial) - len(chunk)), end='', flush=True)
                last_partial = chunk
        except KeyboardInterrupt:
            print("\nEnding transcription as per user request.")
        finally: 
            if speaker and purpose == "transcription":
                run_speech(" ".join(transcription_chunks), speaker)
    if speaker:
        run_speech(" ".join(transcription_chunks), speaker)


def run_translation(from_language, sample_rate, device_ID):
    to_language = prompt_choice("What language do you want to translate into? ",
                                 list(LanguageManager.data.keys())).lower()
    speaker = get_speaker_pref(from_language, to_language)
    speaker.voice_setup()
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    translation_chunks=[]
    try:
        if TextTranslator.model_exists(): # add something later to confirm that model is installed properly
            for chunk, is_final in transcriber.processing_audio():
                if is_final:
                    translator = TextTranslator(chunk, from_language, to_language)
                    translated_chunk=translator.translate_text(speaker)
                    if speaker: 
                        translation_chunks.append(translated_chunk)
        else:
            print(
                "the translation you are trying to complete is not available or"
                "is not installed properly. Visit 'https://www.argosopentech.com/argospm/index/'"
                "download ur desired model and follow the instructions in"
                "the github folder titled 'install_translation_package.py"
                "only languages listed on website are compatible."
            )
        if speaker:
            run_speech(" ".join(translation_chunks), speaker)
    finally:
        if speaker:
            run_speech(" ".join(translation_chunks), speaker)
def run_speech(text, speaker):
    if speaker:
        speaker.speak(text)
    else:
        print("No speaker available to read the text aloud.")
