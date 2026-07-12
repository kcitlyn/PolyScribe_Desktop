"""
Transcript data model: accumulates recognized segments with word-level
timing/confidence, exports to .txt / .srt / .json, and persists session
history to disk.
"""

import json
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path(__file__).resolve().parent.parent / "history"

LOW_CONFIDENCE = 0.7  # words below this confidence get flagged in the UI


class Transcript:
    def __init__(self, from_language="", to_language="", mode="transcription"):
        self.from_language = from_language
        self.to_language = to_language
        self.mode = mode
        self.started_at = datetime.now()
        self.segments = []  # {"text", "words", "translation", "start", "end"}

    def add_segment(self, text, words=None, translation=None):
        words = words or []
        segment = {
            "text": text,
            "words": words,
            "translation": translation,
            "start": words[0]["start"] if words else None,
            "end": words[-1]["end"] if words else None,
        }
        self.segments.append(segment)
        return segment

    @property
    def full_text(self):
        return " ".join(s["text"] for s in self.segments)

    @property
    def full_translation(self):
        return " ".join(s["translation"] for s in self.segments if s.get("translation"))

    def low_confidence_words(self, segment):
        """Return the set of words in a segment below the confidence threshold."""
        return {w["word"] for w in segment.get("words", [])
                if w.get("conf", 1.0) < LOW_CONFIDENCE}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_txt(self):
        lines = []
        for s in self.segments:
            lines.append(s["text"])
            if s.get("translation"):
                lines.append(f"  → {s['translation']}")
        return "\n".join(lines) + "\n"

    def to_srt(self):
        """SubRip subtitle format. Falls back to 3s-per-segment spacing
        when word timestamps are unavailable."""
        blocks = []
        fallback_t = 0.0
        for i, s in enumerate(self.segments, start=1):
            start = s["start"] if s["start"] is not None else fallback_t
            end = s["end"] if s["end"] is not None else start + 3.0
            fallback_t = end
            text = s["text"]
            if s.get("translation"):
                text += f"\n{s['translation']}"
            blocks.append(f"{i}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n")
        return "\n".join(blocks)

    def to_json(self):
        return json.dumps({
            "from_language": self.from_language,
            "to_language": self.to_language,
            "mode": self.mode,
            "started_at": self.started_at.isoformat(),
            "segments": self.segments,
        }, indent=2, ensure_ascii=False)

    def export(self, path):
        """Write the transcript to `path`; format chosen by extension."""
        path = Path(path)
        ext = path.suffix.lower()
        if ext == ".srt":
            content = self.to_srt()
        elif ext == ".json":
            content = self.to_json()
        else:
            content = self.to_txt()
        path.write_text(content, encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Session history
    # ------------------------------------------------------------------

    def save_to_history(self):
        """Persist this session (if non-empty) to the history folder."""
        if not self.segments:
            return None
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        stamp = self.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        path = HISTORY_DIR / f"session_{stamp}.json"
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @staticmethod
    def list_history():
        """Return history entries newest-first: [{path, label, preview}]."""
        if not HISTORY_DIR.is_dir():
            return []
        entries = []
        for f in sorted(HISTORY_DIR.glob("session_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            started = data.get("started_at", "")[:19].replace("T", "  ")
            mode = data.get("mode", "transcription")
            lang = data.get("from_language", "?")
            if data.get("to_language") and mode == "translation":
                lang += f" → {data['to_language']}"
            text = " ".join(s.get("text", "") for s in data.get("segments", []))
            preview = text[:80] + ("…" if len(text) > 80 else "")
            entries.append({"path": f, "label": f"{started}   {lang}", "preview": preview})
        return entries

    @staticmethod
    def load(path):
        """Load a saved session back into a Transcript."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        t = Transcript(data.get("from_language", ""), data.get("to_language", ""),
                       data.get("mode", "transcription"))
        try:
            t.started_at = datetime.fromisoformat(data["started_at"])
        except (KeyError, ValueError):
            pass
        t.segments = data.get("segments", [])
        return t


def _srt_time(seconds):
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"
