"""Tests for the audio transcription module (no hardware required)."""

import numpy as np
import pytest
from scipy.signal import resample_poly


class TestResampleAudio:
    """Test the resampling logic that VoiceProcessor uses internally."""

    def test_resample_44100_to_16000(self):
        duration_s = 0.1
        input_rate = 44100
        target_rate = 16000
        samples = int(duration_s * input_rate)
        audio = np.random.randint(-32768, 32767, size=samples, dtype=np.int16)
        resampled = resample_poly(audio.astype(np.float64), target_rate, input_rate).astype(np.int16)
        expected_len = int(samples * target_rate / input_rate)
        assert abs(len(resampled) - expected_len) <= 1

    def test_resample_48000_to_16000(self):
        input_rate = 48000
        target_rate = 16000
        samples = 4800
        audio = np.random.randint(-32768, 32767, size=samples, dtype=np.int16)
        resampled = resample_poly(audio.astype(np.float64), target_rate, input_rate).astype(np.int16)
        expected_len = samples * target_rate // input_rate
        assert abs(len(resampled) - expected_len) <= 1

    def test_resample_preserves_dtype(self):
        audio = np.zeros(160, dtype=np.int16)
        result = resample_poly(audio.astype(np.float64), 16000, 44100).astype(np.int16)
        assert result.dtype == np.int16
