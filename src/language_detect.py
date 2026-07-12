"""
Auto language detection: run a short audio sample through each installed
Vosk model and pick the one that recognizes the most (weighted by
confidence). Works offline with only the models the user already has.
"""

import json

from vosk import KaldiRecognizer

from languages.languages import LanguageManager


def score_sample(model, audio_bytes, sample_rate=16000):
    """Score how well `model` recognizes `audio_bytes` (16kHz mono int16).

    Returns total word confidence — more recognized words with higher
    confidence means the language likely matches.
    """
    rec = KaldiRecognizer(model, sample_rate)
    rec.SetWords(True)
    chunk = 8000
    for i in range(0, len(audio_bytes), chunk):
        rec.AcceptWaveform(audio_bytes[i:i + chunk])
    result = json.loads(rec.FinalResult())
    words = result.get("result", [])
    return sum(w.get("conf", 0.0) for w in words)


def detect_language(audio_bytes, sample_rate=16000, languages=None):
    """Return (language_name, scores) for the best-matching installed model.

    languages: restrict to a subset of LanguageManager.data keys; default all.
    Returns (None, {}) when no models are installed.
    """
    candidates = languages or list(LanguageManager.data.keys())
    scores = {}
    for lang in candidates:
        try:
            model = LanguageManager.get_model(lang)
        except (ValueError, Exception):
            continue
        try:
            scores[lang] = score_sample(model, audio_bytes, sample_rate)
        except Exception:
            scores[lang] = 0.0
    if not scores:
        return None, {}
    best = max(scores, key=scores.get)
    if scores[best] <= 0:
        return None, scores
    return best, scores


def record_sample(device_id, input_sample_rate, seconds=4):
    """Record a short mono sample from the mic and return 16kHz int16 bytes."""
    import numpy as np
    import sounddevice as sd
    from scipy.signal import resample_poly

    frames = int(seconds * input_sample_rate)
    audio = sd.rec(frames, samplerate=int(input_sample_rate), channels=1,
                   dtype="int16", device=device_id)
    sd.wait()
    audio = audio.flatten()
    resampled = resample_poly(audio, 16000, int(input_sample_rate))
    return resampled.astype(np.int16).tobytes()
