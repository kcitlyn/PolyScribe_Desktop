"""
PolyScribe Desktop GUI — real-time speech transcription and translation.
Run with:  python src/gui.py

Keyboard shortcuts:
  Ctrl/Cmd+Shift+S   start / stop listening
  Ctrl/Cmd+F         search the transcript
  Ctrl/Cmd+E         export transcript
  Ctrl/Cmd+plus / minus   bigger / smaller transcript text
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sounddevice as sd
from languages.languages import LanguageManager
from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor, transcribe_file
from languages.speak import Speak
from transcript import Transcript
import themes
from themes import THEMES, theme_display_names, theme_from_display_name
from widgets import PillButton, Card

LanguageManager.refresh()

FONT_BODY = ("Helvetica", 13)
FONT_SMALL = ("Helvetica", 11)
FONT_TITLE = ("Helvetica", 26, "bold")
FONT_SUBTITLE = ("Helvetica", 12)
MONO_FAMILY = "Menlo"


class PolyScribeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PolyScribe")
        self.geometry("1000x740")
        self.minsize(800, 580)

        self.theme_name = themes.load_theme_name()
        settings = themes.load_settings()
        self.mono_size = settings.get("font_size", 14)

        self._running = False
        self._thread = None
        self.transcript = None
        self.overlay = None

        self._themed_widgets = []
        self._cards = []
        self._pills = []

        self._build_layout()
        self._bind_hotkeys()
        self.apply_theme(self.theme_name)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _reg(self, widget, role):
        self._themed_widgets.append((widget, role))
        return widget

    def _build_layout(self):
        header = self._reg(tk.Frame(self), "bg")
        header.pack(fill=tk.X, padx=24, pady=(18, 6))

        title_box = self._reg(tk.Frame(header), "bg")
        title_box.pack(side=tk.LEFT)
        self._reg(tk.Label(title_box, text="PolyScribe", font=FONT_TITLE, anchor="w"),
                  "title").pack(anchor="w")
        self._reg(tk.Label(title_box, text="Offline speech transcription & translation",
                           font=FONT_SUBTITLE, anchor="w"), "subtext").pack(anchor="w")

        theme_box = self._reg(tk.Frame(header), "bg")
        theme_box.pack(side=tk.RIGHT)
        self._reg(tk.Label(theme_box, text="Theme", font=FONT_SMALL), "subtext").pack(anchor="e")
        self.theme_var = tk.StringVar(value=self.theme_name)
        theme_combo = ttk.Combobox(theme_box, textvariable=self.theme_var,
                                   values=theme_display_names(), state="readonly",
                                   width=16, font=FONT_SMALL)
        theme_combo.pack()
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=24, pady=(6, 18))

        self.transcribe_frame = self._reg(tk.Frame(self.notebook), "bg")
        self.models_frame = self._reg(tk.Frame(self.notebook), "bg")
        self.history_frame = self._reg(tk.Frame(self.notebook), "bg")
        self.notebook.add(self.transcribe_frame, text="  Transcribe  ")
        self.notebook.add(self.models_frame, text="  Models  ")
        self.notebook.add(self.history_frame, text="  History  ")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self._build_transcribe_tab()
        self._build_model_manager_tab()
        self._build_history_tab()

    def _build_transcribe_tab(self):
        frame = self.transcribe_frame

        # Settings card
        card = Card(frame)
        card.pack(fill=tk.X, padx=4, pady=(12, 8))
        self._cards.append(card)
        inner = self._reg(tk.Frame(card), "surface")
        inner.pack(fill=tk.X, padx=18, pady=14)

        def field(parent, label_text, col, row=0, colspan=1):
            box = self._reg(tk.Frame(parent), "surface")
            box.grid(row=row, column=col, columnspan=colspan, padx=10, pady=4, sticky="w")
            self._reg(tk.Label(box, text=label_text, font=FONT_SMALL), "label_on_surface").pack(anchor="w")
            return box

        mode_box = field(inner, "MODE", 0)
        self.mode_var = tk.StringVar(value="transcription")
        mode_combo = ttk.Combobox(mode_box, textvariable=self.mode_var,
                                  values=["transcription", "translation"],
                                  state="readonly", width=13, font=FONT_BODY)
        mode_combo.pack()
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self._toggle_to_lang())

        langs = sorted(LanguageManager.data.keys())
        from_box = field(inner, "SPEAK IN", 1)
        self.from_lang_var = tk.StringVar(value=langs[0] if langs else "")
        self.from_combo = ttk.Combobox(from_box, textvariable=self.from_lang_var,
                                       values=langs, state="readonly", width=13, font=FONT_BODY)
        self.from_combo.pack()

        to_box = field(inner, "TRANSLATE TO", 2)
        self.to_lang_var = tk.StringVar(value=langs[1] if len(langs) > 1 else "")
        self.to_combo = ttk.Combobox(to_box, textvariable=self.to_lang_var,
                                     values=langs, state="readonly", width=13, font=FONT_BODY)
        self.to_combo.pack()

        mic_box = field(inner, "MICROPHONE", 0, row=1, colspan=2)
        input_devs = {i: d for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0}
        mic_names = [f"({i}) {d['name']}" for i, d in input_devs.items()]
        self.mic_ids = list(input_devs.keys())
        self.mic_var = tk.StringVar(value=mic_names[0] if mic_names else "")
        ttk.Combobox(mic_box, textvariable=self.mic_var, values=mic_names,
                     state="readonly", width=38, font=FONT_BODY).pack()

        tts_box = field(inner, "READ ALOUD", 2, row=1)
        self.tts_var = tk.BooleanVar(value=False)
        self.tts_check = self._reg(
            tk.Checkbutton(tts_box, text="Speak results", variable=self.tts_var,
                           font=FONT_BODY, bd=0, highlightthickness=0),
            "check_on_surface")
        self.tts_check.pack(anchor="w")

        self._toggle_to_lang()

        # Action buttons
        btns = self._reg(tk.Frame(frame), "bg")
        btns.pack(pady=8)
        self.start_btn = PillButton(btns, "▶   Start", self._start, kind="primary")
        self.start_btn.pack(side=tk.LEFT, padx=6)
        self.stop_btn = PillButton(btns, "■   Stop", self._stop, kind="danger")
        self.stop_btn.pack(side=tk.LEFT, padx=6)
        self.stop_btn.set_enabled(False)
        self.detect_btn = PillButton(btns, "Detect language", self._detect_language, kind="ghost")
        self.detect_btn.pack(side=tk.LEFT, padx=6)
        self.file_btn = PillButton(btns, "Open audio file…", self._open_file, kind="ghost")
        self.file_btn.pack(side=tk.LEFT, padx=6)
        self.export_btn = PillButton(btns, "Export…", self._export, kind="ghost")
        self.export_btn.pack(side=tk.LEFT, padx=6)
        self.overlay_btn = PillButton(btns, "Overlay", self._toggle_overlay, kind="ghost")
        self.overlay_btn.pack(side=tk.LEFT, padx=6)
        self.clear_btn = PillButton(btns, "Clear", self._clear, kind="ghost")
        self.clear_btn.pack(side=tk.LEFT, padx=6)
        self._pills += [self.start_btn, self.stop_btn, self.detect_btn, self.file_btn,
                        self.export_btn, self.overlay_btn, self.clear_btn]

        # Search bar (hidden until Ctrl+F)
        self.search_frame = self._reg(tk.Frame(frame), "bg")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var,
                                     font=FONT_BODY, width=32, relief=tk.FLAT,
                                     highlightthickness=1)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self._do_search())
        self.search_entry.bind("<Escape>", lambda e: self._hide_search())
        self.search_count = self._reg(tk.Label(self.search_frame, text="", font=FONT_SMALL),
                                      "subtext")
        self.search_count.pack(side=tk.LEFT, padx=6)
        close_s = PillButton(self.search_frame, "✕", self._hide_search, kind="ghost")
        close_s.pack(side=tk.LEFT)
        self._pills.append(close_s)

        # Transcript card with font controls
        out_card = Card(frame)
        out_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 6))
        self._cards.append(out_card)

        font_bar = self._reg(tk.Frame(out_card), "surface")
        font_bar.pack(fill=tk.X, padx=8, pady=(6, 0))
        self._reg(tk.Label(font_bar, text="TRANSCRIPT", font=FONT_SMALL),
                  "label_on_surface").pack(side=tk.LEFT, padx=8)
        smaller = PillButton(font_bar, "A−", lambda: self._change_font(-2), kind="ghost")
        bigger = PillButton(font_bar, "A+", lambda: self._change_font(2), kind="ghost")
        bigger.configure(padx=10, pady=2)
        smaller.configure(padx=10, pady=2)
        bigger.pack(side=tk.RIGHT, padx=(2, 8))
        smaller.pack(side=tk.RIGHT, padx=2)
        self._pills += [smaller, bigger]

        self.output_text = tk.Text(out_card, wrap=tk.WORD,
                                   font=(MONO_FAMILY, self.mono_size),
                                   relief=tk.FLAT, padx=16, pady=12,
                                   state="disabled", bd=0, highlightthickness=0)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.status_var = tk.StringVar(value="Ready — pick a language and press Start (⌘⇧S)")
        self._reg(tk.Label(frame, textvariable=self.status_var, font=FONT_SMALL),
                  "subtext").pack(pady=(0, 8))

    def _build_model_manager_tab(self):
        from model_manager import ModelManagerFrame
        self.model_manager = ModelManagerFrame(self.models_frame, self)
        self.model_manager.pack(fill=tk.BOTH, expand=True)

    def _build_history_tab(self):
        frame = self.history_frame
        card = Card(frame)
        card.pack(fill=tk.BOTH, expand=True, padx=4, pady=12)
        self._cards.append(card)

        top = self._reg(tk.Frame(card), "surface")
        top.pack(fill=tk.X, padx=14, pady=(12, 4))
        self._reg(tk.Label(top, text="Past sessions", font=("Helvetica", 13, "bold")),
                  "label_on_surface").pack(side=tk.LEFT)

        cols = ("session", "preview")
        self.history_tree = ttk.Treeview(card, columns=cols, show="headings", height=8)
        self.history_tree.heading("session", text="Session")
        self.history_tree.heading("preview", text="Preview")
        self.history_tree.column("session", width=280)
        self.history_tree.column("preview", width=480)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        self.history_tree.bind("<Double-1>", lambda e: self._open_history_session())

        btns = self._reg(tk.Frame(card), "surface")
        btns.pack(padx=14, pady=(4, 12))
        openb = PillButton(btns, "Open", self._open_history_session, kind="primary")
        openb.pack(side=tk.LEFT, padx=4)
        exp = PillButton(btns, "Export…", self._export_history_session, kind="ghost")
        exp.pack(side=tk.LEFT, padx=4)
        delb = PillButton(btns, "Delete", self._delete_history_session, kind="danger")
        delb.pack(side=tk.LEFT, padx=4)
        self._pills += [openb, exp, delb]
        self._history_entries = []

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------

    def _bind_hotkeys(self):
        for mod in ("Control", "Command"):
            self.bind_all(f"<{mod}-Shift-S>", lambda e: self._toggle_listening())
            self.bind_all(f"<{mod}-Shift-s>", lambda e: self._toggle_listening())
            self.bind_all(f"<{mod}-f>", lambda e: self._show_search())
            self.bind_all(f"<{mod}-e>", lambda e: self._export())
            self.bind_all(f"<{mod}-plus>", lambda e: self._change_font(2))
            self.bind_all(f"<{mod}-equal>", lambda e: self._change_font(2))
            self.bind_all(f"<{mod}-minus>", lambda e: self._change_font(-2))

    def _toggle_listening(self):
        if self._running:
            self._stop()
        else:
            self._start()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _show_search(self):
        self.search_frame.pack(before=self._cards[1], pady=(0, 4))
        self.search_entry.focus_set()

    def _hide_search(self):
        self.output_text.tag_remove("search", "1.0", tk.END)
        self.search_frame.pack_forget()
        self.search_count.configure(text="")

    def _do_search(self):
        query = self.search_var.get()
        self.output_text.tag_remove("search", "1.0", tk.END)
        if not query:
            self.search_count.configure(text="")
            return
        count = 0
        start = "1.0"
        first = None
        while True:
            pos = self.output_text.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.output_text.tag_add("search", pos, end)
            if first is None:
                first = pos
            start = end
            count += 1
        self.search_count.configure(text=f"{count} match{'es' if count != 1 else ''}")
        if first:
            self.output_text.see(first)

    # ------------------------------------------------------------------
    # Font scaling
    # ------------------------------------------------------------------

    def _change_font(self, delta):
        self.mono_size = max(9, min(32, self.mono_size + delta))
        self.output_text.configure(font=(MONO_FAMILY, self.mono_size))
        settings = themes.load_settings()
        settings["font_size"] = self.mono_size
        themes.save_settings(settings)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export(self):
        if not self.transcript or not self.transcript.segments:
            messagebox.showinfo("Nothing to export", "Record something first!")
            return
        self._export_transcript(self.transcript)

    def _export_transcript(self, transcript):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Subtitles (SRT)", "*.srt"), ("JSON", "*.json")],
            initialfile="transcript")
        if path:
            transcript.export(path)
            self.status_var.set(f"Exported to {path}")

    # ------------------------------------------------------------------
    # Overlay (floating subtitle window)
    # ------------------------------------------------------------------

    def _toggle_overlay(self):
        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay.destroy()
            self.overlay = None
            return
        p = THEMES[self.theme_name]
        self.overlay = tk.Toplevel(self)
        self.overlay.title("PolyScribe Overlay")
        self.overlay.geometry("760x110+{}+{}".format(
            self.winfo_screenwidth() // 2 - 380, self.winfo_screenheight() - 220))
        self.overlay.attributes("-topmost", True)
        try:
            self.overlay.attributes("-alpha", 0.88)
        except tk.TclError:
            pass
        self.overlay.configure(bg=p["bg"])
        self.overlay_label = tk.Label(
            self.overlay, text="… listening for subtitles …",
            font=(MONO_FAMILY, 20, "bold"), bg=p["bg"], fg=p["text"],
            wraplength=720, justify="center")
        self.overlay_label.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        self.overlay.protocol("WM_DELETE_WINDOW", self._toggle_overlay)

    def _update_overlay(self, text):
        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay_label.configure(text=text)

    # ------------------------------------------------------------------
    # Auto language detection
    # ------------------------------------------------------------------

    def _detect_language(self):
        if not LanguageManager.data:
            messagebox.showinfo("No models", "Install at least one speech model first.")
            return
        if len(LanguageManager.data) == 1:
            only = next(iter(LanguageManager.data))
            self.from_lang_var.set(only)
            self.status_var.set(f"Only one model installed — set to {only}")
            return
        self.status_var.set("Speak now — detecting language (4s sample)…")
        self.detect_btn.set_enabled(False)
        threading.Thread(target=self._do_detect, daemon=True).start()

    def _do_detect(self):
        try:
            from language_detect import detect_language, record_sample
            mic_idx = self._current_mic()
            rate = sd.query_devices(mic_idx)['default_samplerate']
            sample = record_sample(mic_idx, rate, seconds=4)
            best, scores = detect_language(sample)
            if best:
                self.after(0, self.from_lang_var.set, best)
                self.after(0, self.status_var.set, f"Detected: {best}")
            else:
                self.after(0, self.status_var.set,
                           "Could not detect — no model recognized the sample")
        except Exception as e:
            self.after(0, self.status_var.set, f"Detection error: {e}")
        finally:
            self.after(0, lambda: self.detect_btn.set_enabled(True))

    # ------------------------------------------------------------------
    # Audio file transcription
    # ------------------------------------------------------------------

    def _open_file(self):
        if self._running:
            messagebox.showinfo("Busy", "Stop live listening first.")
            return
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac"),
                       ("All files", "*.*")])
        if not path:
            return
        from_lang = self.from_lang_var.get()
        if not from_lang:
            messagebox.showinfo("No model", "Install a speech model first.")
            return
        mode = self.mode_var.get()
        to_lang = self.to_lang_var.get()
        if mode == "translation" and not TextTranslator.model_exists(from_lang, to_lang):
            self._append_output(f"⚠ No translation model for {from_lang} → {to_lang}.\n", "final")
            return
        self._running = True
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.file_btn.set_enabled(False)
        self.status_var.set(f"Transcribing {Path(path).name}…")
        self.transcript = Transcript(from_lang, to_lang if mode == "translation" else "", mode)
        threading.Thread(target=self._file_loop, args=(path, from_lang, to_lang, mode),
                         daemon=True).start()

    def _file_loop(self, path, from_lang, to_lang, mode):
        try:
            def on_progress(frac):
                self.after(0, self.status_var.set,
                           f"Transcribing {Path(path).name}… {frac * 100:.0f}%")
            for payload, is_final in transcribe_file(path, from_lang, on_progress):
                if not self._running:
                    break
                translated = None
                if mode == "translation":
                    translated = TextTranslator(payload["text"], from_lang, to_lang).translate_text()
                self.after(0, self._show_final, payload, translated)
            self.after(0, self.status_var.set, f"Finished {Path(path).name}")
        except Exception as e:
            self.after(0, self._append_output, f"\n[Error: {e}]\n", "final")
        finally:
            self.after(0, self._on_stopped)

    # ------------------------------------------------------------------
    # Live transcription
    # ------------------------------------------------------------------

    def _current_mic(self):
        try:
            return int(self.mic_var.get().split(")")[0].replace("(", ""))
        except (ValueError, IndexError):
            return self.mic_ids[0] if self.mic_ids else 0

    def _toggle_to_lang(self):
        if self.mode_var.get() == "translation":
            self.to_combo.configure(state="readonly")
        else:
            self.to_combo.configure(state="disabled")

    def _start(self):
        if self._running:
            return
        from_lang = self.from_lang_var.get()
        to_lang = self.to_lang_var.get()
        mode = self.mode_var.get()

        if not from_lang:
            self._append_output("⚠ No speech model installed. "
                                "Open the Models tab to download one.\n", "final")
            return
        mic_idx = self._current_mic()
        if mode == "translation" and not TextTranslator.model_exists(from_lang, to_lang):
            self._append_output(
                f"⚠ No translation model installed for {from_lang} → {to_lang}.\n"
                "Download one in the Models tab.\n", "final")
            return

        sample_rate = sd.query_devices(mic_idx)['default_samplerate']
        self.transcript = Transcript(from_lang, to_lang if mode == "translation" else "", mode)

        self._running = True
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.status_var.set("Listening…")

        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(from_lang, to_lang, mode, sample_rate, mic_idx),
            daemon=True,
        )
        self._thread.start()

    def _listen_loop(self, from_lang, to_lang, mode, sample_rate, device_id):
        try:
            transcriber = VoiceProcessor(from_lang, sample_rate, device_id)
            for payload, is_final in transcriber.processing_audio():
                if not self._running:
                    break
                if is_final:
                    translated = None
                    if mode == "translation":
                        translated = TextTranslator(payload["text"], from_lang, to_lang).translate_text()
                    self.after(0, self._show_final, payload, translated)
                else:
                    self.after(0, self._show_partial, payload)
        except Exception as e:
            self.after(0, self._append_output, f"\n[Error: {e}]\n", "final")
        finally:
            self.after(0, self._on_stopped)

    def _show_partial(self, text):
        self.output_text.configure(state="normal")
        if self.output_text.tag_ranges("partial"):
            self.output_text.delete("partial.first", "partial.last")
        self.output_text.insert(tk.END, text, "partial")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")
        self._update_overlay(text)

    def _show_final(self, payload, translated=None):
        text = payload["text"]
        words = payload.get("words", [])
        segment = None
        if self.transcript is not None:
            segment = self.transcript.add_segment(text, words, translated)

        low_conf = self.transcript.low_confidence_words(segment) if segment else set()

        self.output_text.configure(state="normal")
        if self.output_text.tag_ranges("partial"):
            self.output_text.delete("partial.first", "partial.last")
        # Insert word by word so low-confidence words get their own tag
        for i, word in enumerate(text.split()):
            tag = "lowconf" if word in low_conf else "final"
            self.output_text.insert(tk.END, word + " ", tag)
        self.output_text.insert(tk.END, "\n", "final")
        if translated:
            self.output_text.insert(tk.END, f"  → {translated}\n", "translated")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

        self._update_overlay(translated if translated else text)

        if self.tts_var.get():
            speak_text = translated if translated else text
            threading.Thread(target=self._speak, args=(speak_text,), daemon=True).start()

    def _speak(self, text):
        try:
            Speak(200, 0.8).speak(text)
        except Exception:
            pass

    def _stop(self):
        self._running = False
        self.status_var.set("Stopping…")

    def _on_stopped(self):
        self._running = False
        self.start_btn.set_enabled(True)
        self.stop_btn.set_enabled(False)
        self.file_btn.set_enabled(True)
        if self.transcript and self.transcript.segments:
            saved = self.transcript.save_to_history()
            note = " — session saved to History" if saved else ""
            self.status_var.set(f"Stopped{note}")
        else:
            self.status_var.set("Stopped")

    def _clear(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state="disabled")

    def _append_output(self, text, tag="final"):
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _on_tab_change(self, event=None):
        if self.notebook.index(self.notebook.select()) == 2:
            self._refresh_history()

    def _refresh_history(self):
        self.history_tree.delete(*self.history_tree.get_children())
        self._history_entries = Transcript.list_history()
        for i, entry in enumerate(self._history_entries):
            self.history_tree.insert("", tk.END, iid=str(i),
                                     values=(entry["label"], entry["preview"]))

    def _selected_history_entry(self):
        sel = self.history_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a session first.")
            return None
        return self._history_entries[int(sel[0])]

    def _open_history_session(self):
        entry = self._selected_history_entry()
        if not entry:
            return
        t = Transcript.load(entry["path"])
        self.notebook.select(0)
        self._clear()
        self.output_text.configure(state="normal")
        for seg in t.segments:
            self.output_text.insert(tk.END, seg["text"] + "\n", "final")
            if seg.get("translation"):
                self.output_text.insert(tk.END, f"  → {seg['translation']}\n", "translated")
        self.output_text.configure(state="disabled")
        self.transcript = t
        self.status_var.set(f"Loaded session: {entry['label']}")

    def _export_history_session(self):
        entry = self._selected_history_entry()
        if entry:
            self._export_transcript(Transcript.load(entry["path"]))

    def _delete_history_session(self):
        entry = self._selected_history_entry()
        if not entry:
            return
        if messagebox.askyesno("Delete session", "Delete this saved session?"):
            Path(entry["path"]).unlink(missing_ok=True)
            self._refresh_history()

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def _on_theme_change(self, event=None):
        name = theme_from_display_name(self.theme_var.get())
        self.apply_theme(name)
        themes.save_theme_name(name)

    def apply_theme(self, name):
        self.theme_name = name
        p = THEMES[name]
        self.configure(bg=p["bg"])

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=p["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Helvetica", 12, "bold"),
                        padding=[16, 8], background=p["surface"],
                        foreground=p["subtext"], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", p["accent"])],
                  foreground=[("selected", "#ffffff")])
        style.configure("TCombobox", fieldbackground=p["surface2"],
                        background=p["surface2"], foreground=p["text"],
                        arrowcolor=p["accent"], borderwidth=0,
                        selectbackground=p["surface2"], selectforeground=p["text"])
        style.map("TCombobox", fieldbackground=[("readonly", p["surface2"])],
                  foreground=[("readonly", p["text"])])
        self.option_add("*TCombobox*Listbox.background", p["surface"])
        self.option_add("*TCombobox*Listbox.foreground", p["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", p["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        style.configure("Treeview", background=p["surface"], fieldbackground=p["surface"],
                        foreground=p["text"], borderwidth=0, font=FONT_BODY, rowheight=30)
        style.configure("Treeview.Heading", background=p["surface2"],
                        foreground=p["subtext"], font=("Helvetica", 11, "bold"),
                        borderwidth=0)
        style.map("Treeview", background=[("selected", p["accent"])],
                  foreground=[("selected", "#ffffff")])
        style.configure("TProgressbar", troughcolor=p["surface2"],
                        background=p["accent"], borderwidth=0, thickness=8)
        style.configure("Vertical.TScrollbar", background=p["surface2"],
                        troughcolor=p["surface"], borderwidth=0, arrowcolor=p["subtext"])

        for widget, role in self._themed_widgets:
            try:
                if role == "bg":
                    widget.configure(bg=p["bg"])
                elif role == "surface":
                    widget.configure(bg=p["surface"])
                elif role == "title":
                    widget.configure(bg=p["bg"], fg=p["accent"])
                elif role == "subtext":
                    widget.configure(bg=p["bg"], fg=p["subtext"])
                elif role == "label_on_surface":
                    widget.configure(bg=p["surface"], fg=p["muted"])
                elif role == "check_on_surface":
                    widget.configure(bg=p["surface"], fg=p["text"],
                                     activebackground=p["surface"],
                                     activeforeground=p["text"],
                                     selectcolor=p["surface2"])
            except tk.TclError:
                pass

        for card in self._cards:
            card.apply_theme(p)
        for pill in self._pills:
            pill.apply_theme(p)

        self.search_entry.configure(bg=p["surface2"], fg=p["text"],
                                    insertbackground=p["text"],
                                    highlightbackground=p["border"],
                                    highlightcolor=p["accent"])

        self.output_text.configure(bg=p["surface"], fg=p["text"],
                                   insertbackground=p["text"],
                                   selectbackground=p["accent"])
        self.output_text.tag_configure("partial", foreground=p["muted"])
        self.output_text.tag_configure("final", foreground=p["success"])
        self.output_text.tag_configure("translated", foreground=p["accent2"])
        self.output_text.tag_configure("lowconf", foreground="#e0af68", underline=True)
        self.output_text.tag_configure("search", background=p["accent"], foreground="#ffffff")

        if self.overlay is not None and self.overlay.winfo_exists():
            self.overlay.configure(bg=p["bg"])
            self.overlay_label.configure(bg=p["bg"], fg=p["text"])

        if hasattr(self, "model_manager"):
            self.model_manager.apply_theme(p)

    def refresh_languages(self):
        LanguageManager.refresh()
        langs = sorted(LanguageManager.data.keys())
        self.from_combo.configure(values=langs)
        self.to_combo.configure(values=langs)
        if langs and not self.from_lang_var.get():
            self.from_lang_var.set(langs[0])


if __name__ == "__main__":
    app = PolyScribeApp()
    app.mainloop()
