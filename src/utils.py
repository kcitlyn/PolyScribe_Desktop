import sounddevice as sd

from languages.languages import LanguageManager
from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor

def prompt_choice(prompt, valid_options):
    while True:
        user_input = input(prompt).strip()
        if user_input in valid_options:
            return user_input
        print(f"Invalid input. Choose from: {', '.join(valid_options)}")
        
def get_device_id():
    print(sd.query_devices())
    return int(prompt_choice("Which number microphone do you want to use?", [str(i) for i in range(len(sd.query_devices()))]))

def get_sample_rate(device_ID):
    return sd.query_devices(device_ID)['default_samplerate']

def get_instruction():
    return int(prompt_choice(
        "Do you want me to transcribe what you say only (1) or translate as well (2)?", ["1", "2"]
    ))

def get_languages():
    from_lang = prompt_choice("What language will you speak in?", list(LanguageManager.data.keys())).lower()
    return from_lang

def run_transcription(from_language, sample_rate, device_ID):
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    last_partial = ""
    for chunk, is_final in transcriber.processing_audio():  # assuming your generator yields (text, is_final)
        if is_final:
            print('\r' + chunk + ' ' * max(0, len(last_partial) - len(chunk)), end='', flush=True)
            last_partial = ""
            print(' ' * max(0, len(last_partial)), end='', flush=True)
        else:
            print('\r' + chunk + ' ' * (len(last_partial) - len(chunk)), end='', flush=True)
            last_partial = chunk

def run_translation(from_language, sample_rate, device_ID):
    to_language = prompt_choice("What language do you want to translate into?", list(LanguageManager.data.keys())).lower()
    mode = int(prompt_choice("Show both transcription and translation (1), or only translation (2)?", ["1", "2"]))
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    last_partial = ""
    for chunk, is_final in transcriber.processing_audio():
        if mode == 1:
            if is_final:
                print()  # newline after partials
                print("Recognized:", chunk)
            else:
                print('\r' + chunk + ' ' * (len(last_partial) - len(chunk)), end='', flush=True)
                last_partial = chunk
        translator = TextTranslator(chunk, from_language, to_language)
        translator.translate_text()
