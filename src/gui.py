"""
PolyScribe Desktop GUI — real-time speech transcription and translation.
Run with:  python src/gui.py
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Ensure the src directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sounddevice as sd
from languages.languages import LanguageManager
from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor
from languages.speak import Speak
import themes
from themes import THEMES, theme_display_names, theme_from_display_name
from widgets import PillButton, Card

LanguageManager.refresh()

FONT_BODY = ("Helvetica", 13)
FONT_SMALL = ("Helvetica", 11)
FONT_TITLE = ("Helvetica", 26, "bold")
FONT_SUBTITLE = ("Helvetica", 12)
FONT_MONO = ("Menlo", 14)


class PolyScribeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PolyScribe")
        self.geometry("980x720")
        self.minsize(780, 560)

        self.theme_name = themes.load_theme_name()

        self._running = False
        self._thread = None

        self._themed_widgets = []   # (widget, role) pairs re-colored on theme change
        self._cards = []
        self._pills = []

        self._build_layout()
        self.apply_theme(self.theme_name)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _reg(self, widget, role):
        """Register a widget to be re-colored when the theme changes."""
        self._themed_widgets.append((widget, role))
        return widget

    def _build_layout(self):
        # ----- Header bar -----
        header = self._reg(tk.Frame(self), "bg")
        header.pack(fill=tk.X, padx=24, pady=(18, 6))

        title_box = self._reg(tk.Frame(header), "bg")
        title_box.pack(side=tk.LEFT)
        self._reg(tk.Label(title_box, text="PolyScribe", font=FONT_TITLE, anchor="w"),
                  "title").pack(anchor="w")
        self._reg(tk.Label(title_box, text="Offline speech transcription & translation",
                           font=FONT_SUBTITLE, anchor="w"), "subtext").pack(anchor="w")

        # Theme picker (top-right)
        theme_box = self._reg(tk.Frame(header), "bg")
        theme_box.pack(side=tk.RIGHT)
        self._reg(tk.Label(theme_box, text="Theme", font=FONT_SMALL), "subtext").pack(anchor="e")
        current = THEMES[self.theme_name]
        self.theme_var = tk.StringVar(value=f"{current['emoji']} {self.theme_name}")
        theme_combo = ttk.Combobox(theme_box, textvariable=self.theme_var,
                                   values=theme_display_names(), state="readonly",
                                   width=16, font=FONT_SMALL)
        theme_combo.pack()
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        # ----- Tabs -----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=24, pady=(6, 18))

        self.transcribe_frame = self._reg(tk.Frame(self.notebook), "bg")
        self.models_frame = self._reg(tk.Frame(self.notebook), "bg")
        self.notebook.add(self.transcribe_frame, text="  🎙  Transcribe  ")
        self.notebook.add(self.models_frame, text="  📦  Models  ")

        self._build_transcribe_tab()
        self._build_model_manager_tab()

    def _build_transcribe_tab(self):
        frame = self.transcribe_frame

        # ----- Settings card -----
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

        # Mode
        mode_box = field(inner, "MODE", 0)
        self.mode_var = tk.StringVar(value="transcription")
        mode_combo = ttk.Combobox(mode_box, textvariable=self.mode_var,
                                  values=["transcription", "translation"],
                                  state="readonly", width=13, font=FONT_BODY)
        mode_combo.pack()
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self._toggle_to_lang())

        # From language
        langs = sorted(LanguageManager.data.keys())
        from_box = field(inner, "SPEAK IN", 1)
        self.from_lang_var = tk.StringVar(value=langs[0] if langs else "")
        self.from_combo = ttk.Combobox(from_box, textvariable=self.from_lang_var,
                                       values=langs, state="readonly", width=13, font=FONT_BODY)
        self.from_combo.pack()

        # To language
        to_box = field(inner, "TRANSLATE TO", 2)
        self.to_lang_var = tk.StringVar(value=langs[1] if len(langs) > 1 else "")
        self.to_combo = ttk.Combobox(to_box, textvariable=self.to_lang_var,
                                     values=langs, state="readonly", width=13, font=FONT_BODY)
        self.to_combo.pack()

        # Microphone (second row, wide)
        mic_box = field(inner, "MICROPHONE", 0, row=1, colspan=2)
        input_devs = {i: d for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0}
        mic_names = [f"({i}) {d['name']}" for i, d in input_devs.items()]
        self.mic_ids = list(input_devs.keys())
        self.mic_var = tk.StringVar(value=mic_names[0] if mic_names else "")
        ttk.Combobox(mic_box, textvariable=self.mic_var, values=mic_names,
                     state="readonly", width=38, font=FONT_BODY).pack()

        # TTS toggle (custom check, themed)
        tts_box = field(inner, "READ ALOUD", 2, row=1)
        self.tts_var = tk.BooleanVar(value=False)
        self.tts_check = self._reg(
            tk.Checkbutton(tts_box, text="Speak results", variable=self.tts_var,
                           font=FONT_BODY, bd=0, highlightthickness=0),
            "check_on_surface")
        self.tts_check.pack(anchor="w")

        self._toggle_to_lang()

        # ----- Action buttons -----
        btns = self._reg(tk.Frame(frame), "bg")
        btns.pack(pady=10)
        self.start_btn = PillButton(btns, "▶   Start listening", self._start, kind="primary")
        self.start_btn.pack(side=tk.LEFT, padx=8)
        self.stop_btn = PillButton(btns, "■   Stop", self._stop, kind="danger")
        self.stop_btn.pack(side=tk.LEFT, padx=8)
        self.stop_btn.set_enabled(False)
        self.clear_btn = PillButton(btns, "Clear", self._clear, kind="ghost")
        self.clear_btn.pack(side=tk.LEFT, padx=8)
        self._pills += [self.start_btn, self.stop_btn, self.clear_btn]

        # ----- Transcript card -----
        out_card = Card(frame)
        out_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 6))
        self._cards.append(out_card)

        self.output_text = tk.Text(out_card, wrap=tk.WORD, font=FONT_MONO,
                                   relief=tk.FLAT, padx=16, pady=14,
                                   state="disabled", bd=0, highlightthickness=0)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ----- Status bar -----
        self.status_var = tk.StringVar(value="Ready — pick a language and press Start")
        self._reg(tk.Label(frame, textvariable=self.status_var, font=FONT_SMALL),
                  "subtext").pack(pady=(0, 8))

    def _build_model_manager_tab(self):
        from model_manager import ModelManagerFrame
        self.model_manager = ModelManagerFrame(self.models_frame, self)
        self.model_manager.pack(fill=tk.BOTH, expand=True)

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

        # ttk styles (combobox, notebook, treeview, progressbar)
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

        # Plain-tk widgets by role
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

        # Transcript colors
        self.output_text.configure(bg=p["surface"], fg=p["text"],
                                   insertbackground=p["text"],
                                   selectbackground=p["accent"])
        self.output_text.tag_configure("partial", foreground=p["muted"])
        self.output_text.tag_configure("final", foreground=p["success"])
        self.output_text.tag_configure("translated", foreground=p["accent2"])

        # Model manager tab re-theme
        if hasattr(self, "model_manager"):
            self.model_manager.apply_theme(p)

    # ------------------------------------------------------------------
    # Transcription logic
    # ------------------------------------------------------------------

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
        try:
            mic_idx = int(self.mic_var.get().split(")")[0].replace("(", ""))
        except (ValueError, IndexError):
            mic_idx = self.mic_ids[0] if self.mic_ids else 0

        if mode == "translation" and not TextTranslator.model_exists(from_lang, to_lang):
            self._append_output(
                f"⚠ No translation model installed for {from_lang} → {to_lang}.\n"
                "Download one in the Models tab.\n", "final")
            return

        sample_rate = sd.query_devices(mic_idx)['default_samplerate']

        self._running = True
        self.start_btn.set_enabled(False)
        self.stop_btn.set_enabled(True)
        self.status_var.set("Listening…  🎙")

        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(from_lang, to_lang, mode, sample_rate, mic_idx),
            daemon=True,
        )
        self._thread.start()

    def _listen_loop(self, from_lang, to_lang, mode, sample_rate, device_id):
        try:
            transcriber = VoiceProcessor(from_lang, sample_rate, device_id)
            for chunk, is_final in transcriber.processing_audio():
                if not self._running:
                    break
                if is_final:
                    if mode == "translation":
                        translated = TextTranslator(chunk, from_lang, to_lang).translate_text()
                        self.after(0, self._show_final, chunk, translated)
                    else:
                        self.after(0, self._show_final, chunk, None)
                else:
                    self.after(0, self._show_partial, chunk)
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

    def _show_final(self, text, translated=None):
        self.output_text.configure(state="normal")
        if self.output_text.tag_ranges("partial"):
            self.output_text.delete("partial.first", "partial.last")
        self.output_text.insert(tk.END, text + "\n", "final")
        if translated:
            self.output_text.insert(tk.END, f"  → {translated}\n", "translated")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

        if self.tts_var.get():
            speak_text = translated if translated else text
            threading.Thread(target=self._speak, args=(speak_text,), daemon=True).start()

    def _speak(self, text):
        try:
            Speak(200, 0.8).speak(text)
        except Exception:
            pass  # TTS failure shouldn't crash the app

    def _stop(self):
        self._running = False
        self.status_var.set("Stopping…")

    def _on_stopped(self):
        self._running = False
        self.start_btn.set_enabled(True)
        self.stop_btn.set_enabled(False)
        self.status_var.set("Stopped — press Start to listen again")

    def _clear(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state="disabled")

    def _append_output(self, text, tag="final"):
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text, tag)
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def refresh_languages(self):
        """Called by the model manager after a download completes."""
        LanguageManager.refresh()
        langs = sorted(LanguageManager.data.keys())
        self.from_combo.configure(values=langs)
        self.to_combo.configure(values=langs)
        if langs and not self.from_lang_var.get():
            self.from_lang_var.set(langs[0])


if __name__ == "__main__":
    app = PolyScribeApp()
    app.mainloop()
