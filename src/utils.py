import sounddevice as sd

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


def get_input_devices():
    """Return {device_index: device_info} for devices that can record audio."""
    devices = sd.query_devices()
    return {i: d for i, d in enumerate(devices) if d['max_input_channels'] > 0}


def get_device_id():
    input_devices = get_input_devices()
    for i, device in input_devices.items():
        print(f"({i}) {device['name']}")
    return int(prompt_choice("Which number microphone do you want to use? ",
                             [str(i) for i in input_devices]))


def get_sample_rate(device_ID):
    return sd.query_devices(device_ID)['default_samplerate']


def get_instruction():
    return int(prompt_choice(
        "Do you want me to transcribe what you say only (1) or translate as well (2)? ", ["1", "2"]))


def get_languages():
    return prompt_choice("What language will you speak in? ",
                         list(LanguageManager.data.keys())).lower()


def get_speaker_pref(from_language, to_language):
    answer = prompt_choice("Do you want the output speech to be read aloud? (y or n) ",
                           ["y", "n"]).lower()
    if answer == "y":
        speed_of_voice = int(prompt_choice(
            "How many wpm do you want the voice to speak? (50-500 wpm) ",
            [str(k) for k in range(50, 501)]))
        volume = int(prompt_choice(
            "Enter an integer between 0-100 for volume. ",
            [str(k) for k in range(101)])) / 100
        speaker = Speak(speed_of_voice, volume)
        voice_matches = speaker.get_voice_matches(from_language, to_language)
        if voice_matches:
            numbered_matches = "\n".join(f"({k}) {match}" for k, match in enumerate(voice_matches))
            print(numbered_matches)
            voice_ID_index = prompt_choice(
                "Here are the choices you have based on the language selected. Choose a voice (type a number) ",
                [str(k) for k in range(len(voice_matches))])
            voice_ID = voice_matches[int(voice_ID_index)]
            speaker.set_voice_ID(voice_ID)
            return speaker
        print("The language you have chosen has no matching voice models on this device.")
        print("Transcription/translation will proceed as normal, just without a voice.")
        print("For information on adding voice modules, see the README on GitHub.")
    else:
        print("Okay! Transcribing and/or translating now")
    return None


def run_transcription(from_language, sample_rate, device_ID, purpose):
    speaker = get_speaker_pref(from_language, from_language)
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    last_partial = ""
    transcription_chunks = []
    try:
        for chunk, is_final in transcriber.processing_audio():
            if is_final:
                print('\r' + chunk + ' ' * max(0, len(last_partial) - len(chunk)), flush=True)
                last_partial = ""
                if speaker and purpose == "transcription":
                    transcription_chunks.append(chunk)
            else:
                print('\r' + chunk + ' ' * max(0, len(last_partial) - len(chunk)), end='', flush=True)
                last_partial = chunk
    except KeyboardInterrupt:
        print("\nEnding transcription as per user request.")
    if speaker and purpose == "transcription" and transcription_chunks:
        run_speech(" ".join(transcription_chunks), speaker)


def run_translation(from_language, sample_rate, device_ID):
    to_language = prompt_choice("What language do you want to translate into? ",
                                list(LanguageManager.data.keys())).lower()
    if not TextTranslator.model_exists(from_language, to_language):
        print(
            "\nThe translation you are trying to run is not installed. Visit\n"
            "https://www.argosopentech.com/argospm/index/ to download the desired\n"
            f"{from_language} -> {to_language} .argosmodel file, place it in\n"
            "models/translation_models/, then run install_translation_package.py.\n"
            "You can also use the Model Manager tab in the GUI (python src/gui.py)."
        )
        return
    speaker = get_speaker_pref(from_language, to_language)
    transcriber = VoiceProcessor(from_language, sample_rate, device_ID)
    translation_chunks = []
    try:
        for chunk, is_final in transcriber.processing_audio():
            if is_final:
                translator = TextTranslator(chunk, from_language, to_language)
                translated_chunk = translator.translate_text()
                if speaker:
                    translation_chunks.append(translated_chunk)
    except KeyboardInterrupt:
        print("\nEnding translation as per user request.")
    finally:
        if speaker and translation_chunks:
            run_speech(" ".join(translation_chunks), speaker)


def run_speech(text, speaker):
    if speaker:
        speaker.speak(text)
    else:
        print("No speaker available to read the text aloud.")
