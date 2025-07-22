from translator.src.hardware.input_handler import Button, Keypad
from translation.text_translate import TextTranslator
import json
from hardware.display_logic import Stats
import RPi.GPIO as GPIO

with open("config.json", "r") as f:
    config = json.load(f)
    
def main():
    while True:
        try:
            instructions_collected=Stats()
            if instructions_collected.instruction_collection:
                instructions_collected.process_instructions()
        except KeyboardInterrupt:
            pass
        finally:
            Stats.save_config()
            GPIO.cleanup()

if __name__ == "__main__":
    main()