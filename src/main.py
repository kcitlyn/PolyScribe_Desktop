from hardware.gpio import Button, Keypad
from translation.text_translate import TextTranslator
from utils import prompt_choice

def main():
    #make this part correspond with button push later
    minimum_time_needed_speaking= 5
    speaking_button= Button(model_used)
    keypad= Keypad()
    model_used=keypad.input_model_type(1,1) #change values later/ add something corresponding to matrix stuff
    keypad.key_scanning_setup()

    if speaking_button.time_held_for() >= minimum_time_needed_speaking:
        Button.voice_processor_setup()
    
if __name__ == "__main__":
    main()