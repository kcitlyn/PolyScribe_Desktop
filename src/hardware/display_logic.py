import json
from hardware.input_handler import Keypad, Button
import utils_hardware

with open("config.json", "r") as f:
    config = json.load(f)

voice_button= Button()
VOICE_MODE_CHANGE_TIME=0

class Stats:
    def __init__(self):
        self.keypad= Keypad()

    def mode_handler(self):
        if self.key_pressed== "A":
            config["display_mode"]= "setting"
            Display.setting_screen()
        if self.key_pressed == "B":
            config["display_mode"]= "voice settings"
            Display.voice_setting_screen()
        if self.key_pressed=="C":
            config["display_mode"]= "info"
            Display.info_screen()
        if config["display_mode"] == "language display":
            Display.language_display(config["from_language"], config["to_language"], utils_hardware.get_sample_rate(config["device_ID"]), config["device_ID"])
    def instruction_collection(self):
        key_pressed = self.scan_keypad()

        if key_pressed is None:
            pass

        if config["display_mode"] == "setting":
            if len(self.instruction_input) < 2:
                if key_pressed != "*" and len(self.instruction_input)>0:
                    self.instruction_input += key_pressed
                else:
                    self.instruction_input[:-1]
                print("Current instruction:", self.instruction_input)
            if len(self.instruction_input) == 2:
                return self.instruction_input
            else:
                self.instruction_input = ""
        elif config["display_mode"] == "info":
            #display instructions on screen
            pass
        elif config["display_mode"] == "utils":
            pass

        if voice_button.is_held_for(VOICE_MODE_CHANGE_TIME):  # if start button held for reboot time, restart
                if config["microphone_mode"]== "push-to-talk":
                    config["microphone_mode"]== "open-talk"
                else:
                    config["push-to-talk"] == "open-talk"

        return self.instruction_input

    def process_instructions(self):
        instructions= self.instruction_input
        if instructions[0] in config["language_mapping"]:
            config["from_language"] = config["language_mapping"][instructions[0]]
        else:
            print(f"Invalid from-language key: {instructions[0]}")
        
        if instructions[1] in config["language_mapping"]:
            config["to_language"] = config["language_mapping"][instructions[1]]
        else:
            print(f"Invalid to-language key: {instructions[1]}")
        
        if instructions[0]==instructions[1]:
            config["method_mode"]= "transcribe"
        else:
            config["method_mode"]= "translate"
        config["display_mode"] = "language display"

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
    
class Display:
    def __init__(self):
        pass
    #different modes of screen
    def language_display(self, from_language, to_language, sample_rate, device_ID):
        if config["method_mode"]== "translation":
            if config["voice_mode"]=="open" or (config["voice_mode"]=="push-to-talk" and voice_button._is_pressed()):
                utils_hardware.run_translation(from_language, to_language, sample_rate, device_ID)
        elif config["method_mode"]== "transcription":
            if config["voice_mode"]=="open" or (config["voice_mode"]=="push-to-talk" and voice_button._is_pressed()):
                utils_hardware.run_transcription(from_language, sample_rate, device_ID)
    def setting_screen(self):
        print("setting screen display")
    def info_screen(self):
        print("info screen")
    def log_screen(self):
        print("log screen")
    def voice_setting_screen(self):
        print("voice setting screen")

    