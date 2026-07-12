"""Tests for the Transcript model: segments, export formats, history."""

import json
import pytest
from transcript import Transcript, _srt_time, LOW_CONFIDENCE


def make_transcript():
    t = Transcript("english", "spanish", "translation")
    t.add_segment("hello world",
                  words=[{"word": "hello", "start": 0.5, "end": 1.0, "conf": 0.98},
                         {"word": "world", "start": 1.1, "end": 1.6, "conf": 0.55}],
                  translation="hola mundo")
    t.add_segment("goodbye", words=[], translation="adiós")
    return t


class TestSegments:
    def test_full_text(self):
        assert make_transcript().full_text == "hello world goodbye"

    def test_full_translation(self):
        assert make_transcript().full_translation == "hola mundo adiós"

    def test_segment_timing_from_words(self):
        seg = make_transcript().segments[0]
        assert seg["start"] == 0.5
        assert seg["end"] == 1.6

    def test_segment_without_words_has_no_timing(self):
        seg = make_transcript().segments[1]
        assert seg["start"] is None

    def test_low_confidence_words(self):
        t = make_transcript()
        low = t.low_confidence_words(t.segments[0])
        assert low == {"world"}
        assert LOW_CONFIDENCE > 0.55


class TestExport:
    def test_txt(self):
        out = make_transcript().to_txt()
        assert "hello world" in out
        assert "→ hola mundo" in out

    def test_srt_structure(self):
        srt = make_transcript().to_srt()
        assert srt.startswith("1\n")
        assert "00:00:00,500 --> 00:00:01,600" in srt
        assert "hola mundo" in srt

    def test_srt_fallback_timing(self):
        # Second segment has no word timing; should follow the first
        srt = make_transcript().to_srt()
        assert "00:00:01,600 --> 00:00:04,600" in srt

    def test_json_roundtrip(self):
        t = make_transcript()
        data = json.loads(t.to_json())
        assert data["from_language"] == "english"
        assert len(data["segments"]) == 2

    def test_export_file(self, tmp_path):
        t = make_transcript()
        for ext in (".txt", ".srt", ".json"):
            p = t.export(tmp_path / f"out{ext}")
            assert p.exists()
            assert p.read_text(encoding="utf-8")


class TestHistory:
    def test_save_and_load(self, tmp_path, monkeypatch):
        import transcript as transcript_mod
        monkeypatch.setattr(transcript_mod, "HISTORY_DIR", tmp_path)
        t = make_transcript()
        path = t.save_to_history()
        assert path is not None and path.exists()

        entries = Transcript.list_history()
        assert len(entries) == 1
        assert "english → spanish" in entries[0]["label"]
        assert "hello world" in entries[0]["preview"]

        loaded = Transcript.load(path)
        assert loaded.full_text == t.full_text
        assert loaded.mode == "translation"

    def test_empty_transcript_not_saved(self, tmp_path, monkeypatch):
        import transcript as transcript_mod
        monkeypatch.setattr(transcript_mod, "HISTORY_DIR", tmp_path)
        assert Transcript().save_to_history() is None


class TestSrtTime:
    def test_zero(self):
        assert _srt_time(0) == "00:00:00,000"

    def test_full(self):
        assert _srt_time(3661.25) == "01:01:01,250"
