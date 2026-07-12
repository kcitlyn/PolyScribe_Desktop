import sys
import json
import queue
import sounddevice as sd
from vosk import KaldiRecognizer

# vosk requires 16kHz mono audio; we resample whatever the mic provides
import numpy as np
from scipy.signal import resample_poly

from languages.languages import LanguageManager


class VoiceProcessor():
    def __init__(self, language, input_sample_rate, device_ID):
        self.language = language
        self.model = LanguageManager.get_model(language)
        self.ideal_sample_rate = 16000        # 16000 Hz for Vosk
        self.device_ID = device_ID
        self.input_sample_rate = input_sample_rate  # depending on microphone Hz
        self.rec = KaldiRecognizer(self.model, self.ideal_sample_rate)
        self.rec.SetWords(True)  # emit per-word timestamps + confidence
        self.queue = queue.Queue()

    def resample_audio(self, indata_bytes):
        audio_np = np.frombuffer(indata_bytes, dtype=np.int16)
        resampled = resample_poly(audio_np, self.ideal_sample_rate, self.input_sample_rate)
        return resampled.astype(np.int16).tobytes()

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        resampled_data = self.resample_audio(bytes(indata))
        self.queue.put(resampled_data)

    def processing_audio(self):
        """Yield (payload, is_final) from the microphone.

        For final results payload is a dict:
            {"text": str, "words": [{"word", "start", "end", "conf"}, ...]}
        For partials payload is the partial text string.
        """
        with sd.RawInputStream(samplerate=self.input_sample_rate, blocksize=None,
                               dtype='int16', device=self.device_ID, channels=1,
                               callback=self.callback):
            print("Listening... (Ctrl+C to stop listening)")
            last_partial = ""
            while True:
                try:
                    data = self.queue.get(timeout=.1)
                except queue.Empty:
                    continue
                if not data:
                    continue
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '')
                    if text:
                        with self.queue.mutex:
                            self.queue.queue.clear()
                        yield ({"text": text, "words": result.get("result", [])}, True)
                else:
                    partial = json.loads(self.rec.PartialResult())
                    partial_text = partial.get('partial', '')
                    if partial_text and partial_text != last_partial:
                        last_partial = partial_text
                        yield (partial_text, False)


def transcribe_file(path, language, progress_callback=None):
    """Transcribe an audio file. Yields the same (payload, is_final) tuples
    as VoiceProcessor.processing_audio().

    Supports WAV natively; other formats (mp3, m4a, flac...) are converted
    with ffmpeg if available on PATH.
    """
    import wave
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    path = Path(path)
    model = LanguageManager.get_model(language)

    tmp_wav = None
    try:
        wav_path = path
        needs_convert = path.suffix.lower() != ".wav"
        if not needs_convert:
            # Even .wav files may be stereo/wrong rate; check first
            try:
                with wave.open(str(path), "rb") as wf:
                    needs_convert = (wf.getnchannels() != 1 or wf.getsampwidth() != 2
                                     or wf.getframerate() != 16000)
            except wave.Error:
                needs_convert = True

        if needs_convert:
            if not shutil.which("ffmpeg"):
                raise RuntimeError(
                    "This file needs conversion, but ffmpeg was not found. "
                    "Install it (e.g. 'brew install ffmpeg') or provide a "
                    "16 kHz mono WAV file.")
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_wav.close()
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(path), "-ar", "16000", "-ac", "1",
                 "-sample_fmt", "s16", tmp_wav.name],
                check=True, capture_output=True)
            wav_path = Path(tmp_wav.name)

        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(True)
        with wave.open(str(wav_path), "rb") as wf:
            total_frames = wf.getnframes()
            read_frames = 0
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                read_frames += 4000
                if progress_callback and total_frames:
                    progress_callback(min(read_frames / total_frames, 1.0))
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        yield ({"text": text, "words": result.get("result", [])}, True)
            final = json.loads(rec.FinalResult())
            if final.get("text"):
                yield ({"text": final["text"], "words": final.get("result", [])}, True)
    finally:
        if tmp_wav is not None:
            Path(tmp_wav.name).unlink(missing_ok=True)
