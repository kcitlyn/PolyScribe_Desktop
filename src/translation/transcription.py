import sys
import json
import queue
import sounddevice as sd
from vosk import KaldiRecognizer

# vosk library requires microphone inputs to only come in at a sample rate of 16kHz, this library will help later in readjusting audio to fit standards
import numpy as np
from scipy.signal import resample_poly

from languages.languages import LanguageManager

class VoiceProcessor():
    def __init__(self, language, input_sample_rate, device_ID):
        self.language= language
        self.model = LanguageManager.get_model(language)
        self.ideal_sample_rate = 16000        # 16000 Hz for Vosk
        self.device_ID = device_ID
        self.input_sample_rate = input_sample_rate  # depending on microphone Hz
        self.rec = KaldiRecognizer(self.model, self.ideal_sample_rate)
        self.queue = queue.Queue() # create a queue to hold audio data

    def resample_audio(self, indata_bytes):
        # Convert bytes to numpy int16 array
        audio_np = np.frombuffer(indata_bytes, dtype=np.int16)
        # Resample from input_samplerate to self.sample_rate (e.g. x Hz to 16000)
        resampled = resample_poly(audio_np, self.ideal_sample_rate, self.input_sample_rate)
        # Convert back to bytes
        return resampled.astype(np.int16).tobytes()

    def callback(self, indata, status):
        if status:
            print(status, file=sys.stderr) #prints a status error if problems detected with audio file
        resampled_data = self.resample_audio(bytes(indata))
        self.queue.put(resampled_data)

    def processing_audio(self):
        # Start recording from mic
        with sd.RawInputStream(samplerate=self.input_sample_rate, blocksize=None, dtype='int16', device= self.device_ID, channels=1
                             ,callback=self.callback): #never_drop_input may buffer audio translation but makes sure no audio gets deleted; disable if u prefer speedy trasnlation over inaccraute fix later
            print("Listening... (Ctrl+C to stop)")
            last_partial = ""
            while True:
                data = self.queue.get() # grabs data from queue and also deletes as it processesq
                if self.rec.AcceptWaveform(data):
                    result = self.rec.Result()
                    text = json.loads(result).get('text', '')
                    if text:
                        with self.queue.mutex:
                            self.queue.queue.clear()
                        yield (text, True)  # True = final
                else:
                    partial = self.rec.PartialResult()
                    partial_dict = json.loads(partial)
                    partial_text = partial_dict.get('partial', '')
                    if partial_text != "" and partial_text != last_partial:
                        last_partial = partial_text
                        yield (partial_text, False)  # False = partial
                