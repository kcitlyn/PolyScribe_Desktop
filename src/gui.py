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
from languages.languages import LanguageManager, VOSK_MODELS_DIR
from translation.text_translate import TextTranslator
from translation.transcription import VoiceProcessor
from languages.speak import Speak

# Ensure we scan available models
LanguageManager.refresh()


class PolyScribeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PolyScribe — Offline Speech Transcription & Translation")
        self.geometry("900x650")
        self.minsize(700, 500)
        self.configure(bg="#1e1e2e")

        style = ttk.Style(self)
        style.theme_use("clam")
        self._configure_styles(style)

        self._running = False
        self._thread = None
        self._transcriber = None

        # Tab container
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.transcribe_frame = ttk.Frame(notebook, style="TFrame")
        self.models_frame = ttk.Frame(notebook, style="TFrame")
        notebook.add(self.transcribe_frame, text="  Transcribe / Translate  ")
        notebook.add(self.models_frame, text="  Model Manager  ")

        self._build_transcribe_tab()
        self._build_model_manager_tab()

    # ----- Styles -----

    def _configure_styles(self, style):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        surface = "#313244"
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 11))
        style.configure("Title.TLabel", background=bg, foreground=accent, font=("Segoe UI", 16, "bold"))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.map("TButton", background=[("active", accent)])
        style.configure("TCombobox", font=("Segoe UI", 11))
        style.configure("TNotebook", background=bg)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 4])

    # ----- Transcribe tab -----

    def _build_transcribe_tab(self):
        frame = self.transcribe_frame
        ttk.Label(frame, text="PolyScribe", style="Title.TLabel").pack(pady=(10, 2))
        ttk.Label(frame, text="Real-time offline speech recognition & translation").pack(pady=(0, 10))

        controls = ttk.Frame(frame, style="TFrame")
        controls.pack(fill=tk.X, padx=20)

        # Mode
        ttk.Label(controls, text="Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.mode_var = tk.StringVar(value="transcription")
        mode_combo = ttk.Combobox(controls, textvariable=self.mode_var,
                                  values=["transcription", "translation"], state="readonly", width=15)
        mode_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        # Source language
        ttk.Label(controls, text="From:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        langs = sorted(LanguageManager.data.keys())
        self.from_lang_var = tk.StringVar(value=langs[0] if langs else "")
        self.from_combo = ttk.Combobox(controls, textvariable=self.from_lang_var,
                                       values=langs, state="readonly", width=14)
        self.from_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Target language
        self.to_label = ttk.Label(controls, text="To:")
        self.to_label.grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.to_lang_var = tk.StringVar(value=langs[1] if len(langs) > 1 else "")
        self.to_combo = ttk.Combobox(controls, textvariable=self.to_lang_var,
                                     values=langs, state="readonly", width=14)
        self.to_combo.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self._toggle_to_lang()

        # Microphone
        ttk.Label(controls, text="Mic:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        input_devs = {i: d for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] > 0}
        mic_names = [f"({i}) {d['name']}" for i, d in input_devs.items()]
        self.mic_ids = list(input_devs.keys())
        self.mic_var = tk.StringVar(value=mic_names[0] if mic_names else "")
        mic_combo = ttk.Combobox(controls, textvariable=self.mic_var,
                                 values=mic_names, state="readonly", width=40)
        mic_combo.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        # TTS toggle
        self.tts_var = tk.BooleanVar(value=False)
        tts_check = ttk.Checkbutton(controls, text="Read aloud (TTS)", variable=self.tts_var)
        tts_check.grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky="w")

        # Start / Stop buttons
        btn_frame = ttk.Frame(frame, style="TFrame")
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="▶  Start", command=self._start)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        self.stop_btn = ttk.Button(btn_frame, text="■  Stop", command=self._stop, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self._clear)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        # Output text area
        self.output_text = tk.Text(frame, wrap=tk.WORD, font=("JetBrains Mono", 12),
                                   bg="#11111b", fg="#cdd6f4", insertbackground="#cdd6f4",
                                   relief=tk.FLAT, padx=10, pady=10, state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.output_text.tag_configure("partial", foreground="#6c7086")
        self.output_text.tag_configure("final", foreground="#a6e3a1")
        self.output_text.tag_configure("translated", foreground="#89b4fa")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.status_var).pack(side=tk.BOTTOM, pady=2)

    def _on_mode_change(self, event=None):
        self._toggle_to_lang()

    def _toggle_to_lang(self):
        if self.mode_var.get() == "translation":
            self.to_combo.configure(state="readonly")
            self.to_label.configure(foreground="#cdd6f4")
        else:
            self.to_combo.configure(state="disabled")
            self.to_label.configure(foreground="#585b70")

    # ----- Transcription logic -----

    def _start(self):
        if self._running:
            return
        from_lang = self.from_lang_var.get()
        to_lang = self.to_lang_var.get()
        mode = self.mode_var.get()
        mic_idx = self.mic_ids[list(self.mic_var.get()[1:]).index(")")]  # parse (N) ... -> N
        # Actually parse the mic index properly
        try:
            mic_idx = int(self.mic_var.get().split(")")[0].replace("(", ""))
        except (ValueError, IndexError):
            mic_idx = self.mic_ids[0] if self.mic_ids else 0

        if mode == "translation" and not TextTranslator.model_exists(from_lang, to_lang):
            self._append_output(
                f"⚠ No translation model installed for {from_lang} → {to_lang}.\n"
                "Download one in the Model Manager tab or from "
                "https://www.argosopentech.com/argospm/index/\n", "final")
            return

        sample_rate = sd.query_devices(mic_idx)['default_samplerate']

        self._running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("Listening…")

        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(from_lang, to_lang, mode, sample_rate, mic_idx),
            daemon=True,
        )
        self._thread.start()

    def _listen_loop(self, from_lang, to_lang, mode, sample_rate, device_id):
        self._transcriber = VoiceProcessor(from_lang, sample_rate, device_id)
        try:
            for chunk, is_final in self._transcriber.processing_audio():
                if not self._running:
                    break
                if is_final:
                    if mode == "translation":
                        translator = TextTranslator(chunk, from_lang, to_lang)
                        translated = translator.translate_text()
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
        # Delete any existing partial line
        if self.output_text.tag_ranges("partial"):
            self.output_text.delete("partial.first", "partial.last")
        self.output_text.insert(tk.END, text, "partial")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def _show_final(self, text, translated=None):
        self.output_text.configure(state="normal")
        # Remove partial text
        if self.output_text.tag_ranges("partial"):
            self.output_text.delete("partial.first", "partial.last")
        self.output_text.insert(tk.END, text + "\n", "final")
        if translated:
            self.output_text.insert(tk.END, f"  → {translated}\n", "translated")
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

        # TTS in background
        if self.tts_var.get():
            speak_text = translated if translated else text
            threading.Thread(target=self._speak, args=(speak_text,), daemon=True).start()

    def _speak(self, text):
        try:
            speaker = Speak(200, 0.8)
            speaker.speak(text)
        except Exception:
            pass  # TTS failure shouldn't crash the app

    def _stop(self):
        self._running = False
        self.status_var.set("Stopping…")

    def _on_stopped(self):
        self._running = False
        self._transcriber = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
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

    # ----- Model Manager tab -----

    def _build_model_manager_tab(self):
        from model_manager import ModelManagerFrame
        ModelManagerFrame(self.models_frame, self).pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = PolyScribeApp()
    app.mainloop()
