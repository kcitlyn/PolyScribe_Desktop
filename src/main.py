from translator.src.hardware.input_handler import Button, Keypad
from translation.text_translate import TextTranslator
import utils 
import json
from hardware.display_logic import Stats

voice_button= Button()
VOICE_MODE_CHANGE_TIME=0

with open("config.json", "r") as f:
    config = json.load(f)
    
def main():
    #default values: to edit values, change config.json file

    button= Button()

    while True:
        try:
            instructions_collected=Stats()
            if instructions_collected.instruction_collection:
                instructions_collected.process_instructions()

            if voice_button.is_held_for(VOICE_MODE_CHANGE_TIME):  # if start button held for reboot time, restart
                if config["microphone_mode"]== "push-to-talk":
                    config["microphone_mode"]== "open-talk"
                else:
                    config["push-to-talk"] == "open-talk"
        except KeyboardInterrupt:
            pass
        finally:
            Stats.save_config()

if __name__ == "__main__":
    main()