"""
Model Manager — Download Vosk speech models and Argos translation packages.
"""

import io
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from urllib.request import urlopen, Request
from zipfile import ZipFile

from languages.languages import LanguageManager, VOSK_MODELS_DIR, TRANSLATION_MODELS_DIR
from widgets import PillButton, Card

VOSK_MODELS = [
    {"name": "vosk-model-small-en-us-0.15", "size": "40 MB", "lang": "English (US) — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"},
    {"name": "vosk-model-en-us-0.22-lgraph", "size": "128 MB", "lang": "English (US) — large",
     "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"},
    {"name": "vosk-model-en-us-0.22", "size": "1.8 GB", "lang": "English (US) — full accuracy",
     "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"},
    {"name": "vosk-model-small-cn-0.22", "size": "42 MB", "lang": "Mandarin — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"},
    {"name": "vosk-model-cn-0.22", "size": "1.3 GB", "lang": "Mandarin — full accuracy",
     "url": "https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip"},
    {"name": "vosk-model-small-es-0.42", "size": "39 MB", "lang": "Spanish — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"},
    {"name": "vosk-model-small-fr-0.22", "size": "41 MB", "lang": "French — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"},
    {"name": "vosk-model-small-de-0.15", "size": "45 MB", "lang": "German — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip"},
    {"name": "vosk-model-small-ru-0.22", "size": "45 MB", "lang": "Russian — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"},
    {"name": "vosk-model-small-it-0.22", "size": "48 MB", "lang": "Italian — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"},
    {"name": "vosk-model-small-pt-0.3", "size": "31 MB", "lang": "Portuguese — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"},
    {"name": "vosk-model-small-ja-0.22", "size": "48 MB", "lang": "Japanese — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip"},
    {"name": "vosk-model-small-ko-0.22", "size": "42 MB", "lang": "Korean — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-ko-0.22.zip"},
    {"name": "vosk-model-small-tr-0.3", "size": "35 MB", "lang": "Turkish — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip"},
    {"name": "vosk-model-small-hi-0.22", "size": "42 MB", "lang": "Hindi — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"},
    {"name": "vosk-model-small-nl-0.22", "size": "39 MB", "lang": "Dutch — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-nl-0.22.zip"},
    {"name": "vosk-model-small-pl-0.22", "size": "50 MB", "lang": "Polish — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip"},
    {"name": "vosk-model-ar-mgb2-0.4", "size": "318 MB", "lang": "Arabic — medium",
     "url": "https://alphacephei.com/vosk/models/vosk-model-ar-mgb2-0.4.zip"},
    {"name": "vosk-model-small-uk-v3-small", "size": "46 MB", "lang": "Ukrainian — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-small.zip"},
    {"name": "vosk-model-small-sv-rhasspy-0.15", "size": "15 MB", "lang": "Swedish — small",
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-sv-rhasspy-0.15.zip"},
]

ARGOS_INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"


class ModelManagerFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bd=0, highlightthickness=0)
        self.app = app
        self._themed_widgets = []
        self._cards = []
        self._pills = []

        # Title area
        header = self._reg(tk.Frame(self), "bg")
        header.pack(fill=tk.X, padx=4, pady=(12, 6))
        self._reg(tk.Label(header, text="📦  Model Manager", font=("Helvetica", 18, "bold")),
                  "title").pack(side=tk.LEFT)
        self._reg(tk.Label(header, text="Download speech & translation models directly",
                           font=("Helvetica", 11)), "subtext").pack(side=tk.LEFT, padx=14)

        # Vosk section
        vosk_card = Card(self)
        vosk_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(6, 4))
        self._cards.append(vosk_card)
        self._build_vosk_list(vosk_card)

        # Argos section
        argos_card = Card(self)
        argos_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 4))
        self._cards.append(argos_card)
        self._build_argos_list(argos_card)

        # Progress
        progress_frame = self._reg(tk.Frame(self), "bg")
        progress_frame.pack(fill=tk.X, padx=10, pady=(4, 10))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, length=400, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=4)
        self.progress_label = self._reg(tk.Label(progress_frame, text="", font=("Helvetica", 11)),
                                        "subtext")
        self.progress_label.pack(pady=(2, 0))

    def _reg(self, widget, role):
        self._themed_widgets.append((widget, role))
        return widget

    # ----- Vosk -----

    def _build_vosk_list(self, parent):
        header = self._reg(tk.Frame(parent), "surface")
        header.pack(fill=tk.X, padx=14, pady=(12, 4))
        self._reg(tk.Label(header, text="🎙  Speech Recognition (Vosk)",
                           font=("Helvetica", 13, "bold")), "label_on_surface").pack(side=tk.LEFT)

        cols = ("language", "size", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=6)
        tree.heading("language", text="Language / Quality")
        tree.heading("size", text="Size")
        tree.heading("status", text="Status")
        tree.column("language", width=250)
        tree.column("size", width=80, anchor="center")
        tree.column("status", width=100, anchor="center")

        installed = {f.name for f in VOSK_MODELS_DIR.iterdir()} if VOSK_MODELS_DIR.is_dir() else set()
        for model in VOSK_MODELS:
            status = "✓ Installed" if model["name"] in installed else "—"
            tree.insert("", tk.END, iid=model["name"],
                        values=(model["lang"], model["size"], status))
        tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        btn_frame = self._reg(tk.Frame(parent), "surface")
        btn_frame.pack(padx=14, pady=(4, 12))
        dl = PillButton(btn_frame, "⬇ Download", lambda: self._download_vosk(tree), kind="primary")
        dl.pack(side=tk.LEFT, padx=4)
        rm = PillButton(btn_frame, "🗑 Delete", lambda: self._delete_vosk(tree), kind="danger")
        rm.pack(side=tk.LEFT, padx=4)
        rf = PillButton(btn_frame, "↻ Refresh", lambda: self._refresh_vosk(tree), kind="ghost")
        rf.pack(side=tk.LEFT, padx=4)
        self._pills += [dl, rm, rf]
        self.vosk_tree = tree

    def _refresh_vosk(self, tree):
        installed = {f.name for f in VOSK_MODELS_DIR.iterdir()} if VOSK_MODELS_DIR.is_dir() else set()
        for model in VOSK_MODELS:
            status = "✓ Installed" if model["name"] in installed else "—"
            tree.set(model["name"], "status", status)
        LanguageManager.refresh()
        self.app.refresh_languages()

    def _download_vosk(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a model from the list first.")
            return
        model_info = next((m for m in VOSK_MODELS if m["name"] == selected[0]), None)
        if model_info:
            threading.Thread(target=self._do_vosk_download, args=(model_info, tree), daemon=True).start()

    def _do_vosk_download(self, model_info, tree):
        url = model_info["url"]
        name = model_info["name"]
        self._set_progress(0, f"Downloading {name}…")
        try:
            VOSK_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            req = Request(url, headers={"User-Agent": "PolyScribe/1.0"})
            resp = urlopen(req, timeout=120)
            total = int(resp.headers.get("Content-Length", 0))
            data = io.BytesIO()
            downloaded = 0
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                data.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    self._set_progress(downloaded / total * 90,
                                       f"Downloading {name}… {downloaded // (1024*1024)} MB")
            self._set_progress(92, f"Extracting {name}…")
            data.seek(0)
            with ZipFile(data) as zf:
                zf.extractall(VOSK_MODELS_DIR)
            self._set_progress(100, f"✓ {name} installed!")
            self.after(0, lambda: self._refresh_vosk(tree))
        except Exception as e:
            self._set_progress(0, f"Error: {e}")

    def _delete_vosk(self, tree):
        import shutil
        selected = tree.selection()
        if not selected:
            return
        name = selected[0]
        path = VOSK_MODELS_DIR / name
        if not path.is_dir():
            messagebox.showinfo("Not installed", f"{name} is not installed.")
            return
        if messagebox.askyesno("Delete model", f"Delete {name}?\nThis cannot be undone."):
            shutil.rmtree(path)
            self._refresh_vosk(tree)
            self._set_progress(0, f"Deleted {name}")

    # ----- Argos -----

    def _build_argos_list(self, parent):
        header = self._reg(tk.Frame(parent), "surface")
        header.pack(fill=tk.X, padx=14, pady=(12, 4))
        self._reg(tk.Label(header, text="🌐  Translation (Argos)",
                           font=("Helvetica", 13, "bold")), "label_on_surface").pack(side=tk.LEFT)

        cols = ("pair", "size", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=5)
        tree.heading("pair", text="Language Pair")
        tree.heading("size", text="Size")
        tree.heading("status", text="Status")
        tree.column("pair", width=250)
        tree.column("size", width=80, anchor="center")
        tree.column("status", width=100, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        btn_frame = self._reg(tk.Frame(parent), "surface")
        btn_frame.pack(padx=14, pady=(4, 12))
        fetch = PillButton(btn_frame, "🔍 Fetch Index", lambda: self._fetch_argos_index(tree), kind="ghost")
        fetch.pack(side=tk.LEFT, padx=4)
        dl = PillButton(btn_frame, "⬇ Download", lambda: self._download_argos(tree), kind="primary")
        dl.pack(side=tk.LEFT, padx=4)
        self._pills += [fetch, dl]
        self.argos_tree = tree
        self.argos_packages = []

    def _fetch_argos_index(self, tree):
        threading.Thread(target=self._do_fetch_argos_index, args=(tree,), daemon=True).start()

    def _do_fetch_argos_index(self, tree):
        self._set_progress(20, "Fetching Argos package index…")
        try:
            req = Request(ARGOS_INDEX_URL, headers={"User-Agent": "PolyScribe/1.0"})
            resp = urlopen(req, timeout=30)
            data = json.loads(resp.read())
            self.argos_packages = data if isinstance(data, list) else []
            self._set_progress(100, f"Loaded {len(self.argos_packages)} translation packages")
            self.after(0, lambda: self._populate_argos_tree(tree))
        except Exception as e:
            self._set_progress(0, f"Error fetching index: {e}")

    def _populate_argos_tree(self, tree):
        tree.delete(*tree.get_children())
        for i, pkg in enumerate(self.argos_packages):
            from_name = pkg.get("from_name", pkg.get("from_code", "?"))
            to_name = pkg.get("to_name", pkg.get("to_code", "?"))
            pair = f"{from_name} → {to_name}"
            size = self._fmt_size(pkg.get("package_size", pkg.get("size", 0)))
            tree.insert("", tk.END, iid=str(i), values=(pair, size, "—"))

    def _download_argos(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a package first.\nClick Fetch Index to load them.")
            return
        idx = int(selected[0])
        if idx < len(self.argos_packages):
            pkg = self.argos_packages[idx]
            threading.Thread(target=self._do_argos_download, args=(pkg, tree, str(idx)), daemon=True).start()

    def _do_argos_download(self, pkg, tree, iid):
        links = pkg.get("links", [])
        url = links[0] if links else pkg.get("url", "")
        if not url:
            self._set_progress(0, "No download URL for this package")
            return
        from_code = pkg.get("from_code", "xx")
        to_code = pkg.get("to_code", "xx")
        filename = f"translate-{from_code}_{to_code}.argosmodel"
        self._set_progress(0, f"Downloading {filename}…")
        try:
            TRANSLATION_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            req = Request(url, headers={"User-Agent": "PolyScribe/1.0"})
            resp = urlopen(req, timeout=120)
            total = int(resp.headers.get("Content-Length", 0))
            out_path = TRANSLATION_MODELS_DIR / filename
            downloaded = 0
            with open(out_path, "wb") as f:
                while True:
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        self._set_progress(downloaded / total * 90,
                                           f"Downloading {filename}… {downloaded // (1024*1024)} MB")
            self._set_progress(92, f"Installing {filename}…")
            from argostranslate import package
            package.install_from_path(str(out_path))
            self._set_progress(100, f"✓ {filename} installed!")
            self.after(0, lambda: tree.set(iid, "status", "✓ Installed"))
        except Exception as e:
            self._set_progress(0, f"Error: {e}")

    # ----- Helpers -----

    def _set_progress(self, pct, msg):
        self.after(0, lambda: self.progress_var.set(pct))
        self.after(0, lambda: self.progress_label.configure(text=msg))

    def apply_theme(self, palette):
        self.configure(bg=palette["bg"])
        for widget, role in self._themed_widgets:
            try:
                if role == "bg":
                    widget.configure(bg=palette["bg"])
                elif role == "surface":
                    widget.configure(bg=palette["surface"])
                elif role == "title":
                    widget.configure(bg=palette["bg"], fg=palette["accent"])
                elif role == "subtext":
                    widget.configure(bg=palette["bg"], fg=palette["subtext"])
                elif role == "label_on_surface":
                    widget.configure(bg=palette["surface"], fg=palette["text"])
            except tk.TclError:
                pass
        for card in self._cards:
            card.apply_theme(palette)
        for pill in self._pills:
            pill.apply_theme(palette)

    @staticmethod
    def _fmt_size(nbytes):
        if not nbytes:
            return "?"
        try:
            nbytes = int(nbytes)
        except (TypeError, ValueError):
            return str(nbytes)
        if nbytes > 1024 * 1024 * 1024:
            return f"{nbytes / (1024**3):.1f} GB"
        return f"{nbytes / (1024**2):.0f} MB"
