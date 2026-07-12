import sys
from pathlib import Path

# Allow running as `python src/main.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import utils
from languages.languages import LanguageManager


def main():
    LanguageManager.refresh()
    if not LanguageManager.data:
        print(
            "No Vosk speech models found in models/vosk_models/.\n"
            "Download one from https://alphacephei.com/vosk/models and unzip it there,\n"
            "or run the GUI (python src/gui.py) and use the Model Manager tab."
        )
        return
    device_ID = utils.get_device_id()
    sample_rate = utils.get_sample_rate(device_ID)
    instruction = utils.get_instruction()
    from_language = utils.get_languages()
    # instruction 1 = transcription only, 2 = transcription + translation
    if instruction == 1:
        utils.run_transcription(from_language, sample_rate, device_ID, "transcription")
    elif instruction == 2:
        utils.run_translation(from_language, sample_rate, device_ID)
    else:
        print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
