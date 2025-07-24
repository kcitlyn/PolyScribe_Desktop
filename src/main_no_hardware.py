from languages.languages import LanguageManager
import utils
import languages.speak as speak
import sounddevice as sd

def main():
    device_ID = utils.get_device_id()
    sample_rate = utils.get_sample_rate(device_ID)
    instruction = utils.get_instruction()
    from_language = utils.get_languages()

    #instructions ask if they just want transcription (1) or both transcribed and translation version (2)
    if instruction == 1:
        utils.run_transcription(from_language, sample_rate, device_ID, "transcription")
        
    elif instruction == 2:
        utils.run_translation(from_language, sample_rate, device_ID)
    else:
        print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()