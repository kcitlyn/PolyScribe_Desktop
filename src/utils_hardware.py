import sounddevice as sd

from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor

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

def run_translation(from_language, to_language, sample_rate, device_ID, translation_mode):
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    last_partial = ""
    translation_mode= translation_mode

    for chunk, is_final in transcriber.processing_audio():
        if translation_mode == 1:
            if is_final:
                print()  # newline after partials
                print("Recognized:", chunk)
            else:
                print('\r' + chunk + ' ' * (len(last_partial) - len(chunk)), end='', flush=True)
                last_partial = chunk
        translator = TextTranslator(chunk, from_language, to_language)
    
