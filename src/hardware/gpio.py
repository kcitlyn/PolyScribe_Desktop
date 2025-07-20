import RPi.GPIO as GPIO
import time

from translation.transcription import VoiceProcessor

BUTTON_PIN=0 #add later
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, gpio_up_down=GPIO.PUD_DOWN)

class Button:
    def __init__(self, model_used):
        self.model_used = model_used
        self._is_pressed = False
        self._pressed_and_released = False
        self._press_time = None

        #button stuff
        self._pressed = False
        self._pressed_and_released = False
        self._press_time = None
        self._hold_triggered = False

        GPIO.remove_event_detect(self.pin)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, bouncetime=75)
        GPIO.add_event_callback(self.pin, self._handle_edge)

    def voice_processor_setup(self):
        input_sample_rate = 24000 #change depending on microphone Hz, possibly add later something taht can sense this??
        device_ID = 3 #change depending on microphone ID
        # For macOS, you can find the device ID using `sd.query_devices()` add later windows version
        if self.model_used == "english_model":
            model = "/Users/kaitlynchen/rsp5/translator/vosk-model-en-us-0.22-lgraph" #ADD LATER
        #mandarin_model = " " #add later
        self.transcriber = VoiceProcessor(model, input_sample_rate, device_ID)
        #mandarin_transcribed = VoiceProcessor(mandarin_model, sample_rate)
        #return self.transcriber.processing_audio()
        print(self.transcriber.processing_audio())

    #button specifics
    def button_action(self):
        if GPIO.input(BUTTON_PIN)==GPIO.HIGH:
            self._is_pressed = True
            self._press_time = time.time()
            self.english_transcriber.processing_audio()
        else:
            print("press the button to start transcribing")
    
    def _handle_edge(self, channel):
        if GPIO.input(self.pin):  # rising edge (press)
            self._on_press(channel)
        else:  # falling edge (release)
            self._on_release(channel)

    def _on_press(self, channel):
        self._pressed = True
        self._press_time = time.time()
        self._hold_triggered = False
        global button_is_pressed
        button_is_pressed = True
        if self.press_callback:
            self.press_callback()
        
    def _on_release(self, channel):
        if self._pressed:
            self._pressed_and_released = True
            self._pressed = False
        self._press_time = None
        self._hold_triggered = False

    def is_held_for(self, seconds=5):
        if self._pressed and self._press_time is not None:
            held_time = time.time() - self._press_time
            if held_time >= seconds and not self._hold_triggered:
                self._hold_triggered = True
            return held_time

class Keypad:
    def __init__(self):
        self.COL_PINS=[]
        self.ROW_PINS=[]
        self.key_press=''
                
    def key_scanning_setup(self):
        #sets up GPIO pins for scan
        self.COL_PINS=[]
        self.ROW_PINS=[]

        self.MATRIX_KEYS= [['1', '2', '3', 'A'],
                      ['4', '5', '6', 'B'],
                      ['7', '8', '9', 'C'],
                      ['*', '0', '#', 'D']]
        
        #change pins to match your connections, below is based on my schematic
        KEYPAD_ROWS=[1,2,3,4] #add later
        KEYPAD_COLUMNS=[1,2,3,4]

        for x in range(4):
            GPIO.setup(KEYPAD_ROWS[x],GPIO.OUT)
            GPIO.setup(KEYPAD_COLUMNS[x], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.COL_PINS.append(KEYPAD_COLUMNS[x])
            self.ROW_PINS.append(KEYPAD_ROWS[x])

    def scan_keypad(self):
        for row_index, row_pin in enumerate(self.ROW_PINS):
            # drive all rows HIGH first
            for r in self.ROW_PINS:
                GPIO.output(r, GPIO.HIGH)
            # pulls current row LOW
            GPIO.output(row_pin, GPIO.LOW)

            # Check for pressed key (column goes LOW)
            for col_index, col_pin in enumerate(self.COL_PINS):
                if GPIO.input(col_pin) == GPIO.LOW:
                    time.sleep(0.2)  # Debounce
                    return self.MATRIX_KEYS[row_index][col_index]

    def input_model_type(self):
        language_mapping= { #possibly loop???
            '12': ('english', 'chinese'),
            '21': ('chinese', 'english'),
            '13': ('english', 'spanish'),
             # etc.
        }
        key=self.scan_keypad()
        if key=="1": #fix
            return "vosk-model-en-us-0.22-lgraph"
        else:
            print("Type a number 1-9defaulted model is english.")
    
