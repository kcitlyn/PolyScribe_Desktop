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

# Vosk model catalog (subset of most-used models — full list at alphacephei.com/vosk/models)
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

# Argos translation packages — fetched live from their index if available.
ARGOS_INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"


class ModelManagerFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app

        # Title
        ttk.Label(self, text="Model Manager", style="Title.TLabel").pack(pady=(10, 2))
        ttk.Label(self, text="Download speech & translation models directly").pack(pady=(0, 10))

        # Sub-notebook for Vosk vs Argos
        sub_nb = ttk.Notebook(self)
        sub_nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        vosk_frame = ttk.Frame(sub_nb, style="TFrame")
        argos_frame = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(vosk_frame, text="  Speech (Vosk)  ")
        sub_nb.add(argos_frame, text="  Translation (Argos)  ")

        self._build_vosk_list(vosk_frame)
        self._build_argos_list(argos_frame)

        # Progress area
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=(5, 2))
        self.progress_label = ttk.Label(self, text="")
        self.progress_label.pack(pady=(0, 10))

    # ----- Vosk models list -----

    def _build_vosk_list(self, parent):
        cols = ("language", "size", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        tree.heading("language", text="Language / Quality")
        tree.heading("size", text="Size")
        tree.heading("status", text="Status")
        tree.column("language", width=250)
        tree.column("size", width=80, anchor="center")
        tree.column("status", width=120, anchor="center")

        installed = {f.name for f in VOSK_MODELS_DIR.iterdir()} if VOSK_MODELS_DIR.is_dir() else set()
        for model in VOSK_MODELS:
            status = "✓ Installed" if model["name"] in installed else "—"
            tree.insert("", tk.END, iid=model["name"],
                        values=(model["lang"], model["size"], status))
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(parent, style="TFrame")
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Download Selected", command=lambda: self._download_vosk(tree)).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=lambda: self._delete_vosk(tree)).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=lambda: self._refresh_vosk(tree)).pack(
            side=tk.LEFT, padx=5)

        self.vosk_tree = tree

    def _refresh_vosk(self, tree):
        installed = {f.name for f in VOSK_MODELS_DIR.iterdir()} if VOSK_MODELS_DIR.is_dir() else set()
        for model in VOSK_MODELS:
            status = "✓ Installed" if model["name"] in installed else "—"
            tree.set(model["name"], "status", status)
        LanguageManager.refresh()
        self._refresh_main_combos()

    def _download_vosk(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a model from the list first.")
            return
        model_name = selected[0]
        model_info = next((m for m in VOSK_MODELS if m["name"] == model_name), None)
        if model_info is None:
            return
        threading.Thread(target=self._do_vosk_download, args=(model_info, tree), daemon=True).start()

    def _do_vosk_download(self, model_info, tree):
        url = model_info["url"]
        name = model_info["name"]
        self._set_progress(0, f"Downloading {name}…")
        try:
            VOSK_MODELS_DIR.mkdir(parents=True, exist_ok=True)
            req = Request(url, headers={"User-Agent": "PolyScribe/1.0"})
            resp = urlopen(req, timeout=60)
            total = int(resp.headers.get("Content-Length", 0))
            data = io.BytesIO()
            downloaded = 0
            chunk_size = 1024 * 256
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                data.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    self._set_progress(pct, f"Downloading {name}… {downloaded // (1024*1024)} MB")
            self._set_progress(95, f"Extracting {name}…")
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
        model_name = selected[0]
        path = VOSK_MODELS_DIR / model_name
        if not path.is_dir():
            messagebox.showinfo("Not installed", f"{model_name} is not installed.")
            return
        if messagebox.askyesno("Delete model", f"Delete {model_name}?\nThis cannot be undone."):
            shutil.rmtree(path)
            self._refresh_vosk(tree)
            self._set_progress(0, f"Deleted {model_name}")

    # ----- Argos translation models -----

    def _build_argos_list(self, parent):
        cols = ("pair", "size", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        tree.heading("pair", text="Language Pair")
        tree.heading("size", text="Size")
        tree.heading("status", text="Status")
        tree.column("pair", width=250)
        tree.column("size", width=80, anchor="center")
        tree.column("status", width=120, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(parent, style="TFrame")
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Fetch Index", command=lambda: self._fetch_argos_index(tree)).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Download Selected", command=lambda: self._download_argos(tree)).pack(
            side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text="(Click Fetch Index to load available packages)").pack(side=tk.LEFT, padx=10)

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
            self._set_progress(100, f"Loaded {len(self.argos_packages)} packages")
            self.after(0, lambda: self._populate_argos_tree(tree))
        except Exception as e:
            self._set_progress(0, f"Error fetching index: {e}")

    def _populate_argos_tree(self, tree):
        tree.delete(*tree.get_children())
        # Check which .argosmodel files we already have
        installed_files = set()
        if TRANSLATION_MODELS_DIR.is_dir():
            installed_files = {f.stem for f in TRANSLATION_MODELS_DIR.glob("*.argosmodel")}
        for pkg in self.argos_packages:
            from_name = pkg.get("from_name", pkg.get("from_code", "?"))
            to_name = pkg.get("to_name", pkg.get("to_code", "?"))
            pair = f"{from_name} → {to_name}"
            size = self._fmt_size(pkg.get("package_size", pkg.get("size", 0)))
            iid = pkg.get("package_version", "") or f"{from_name}_{to_name}"
            links = pkg.get("links", [])
            url = links[0] if links else pkg.get("url", "")
            status = "—"
            tree.insert("", tk.END, iid=iid, values=(pair, size, status))

    def _download_argos(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a package first.")
            return
        iid = selected[0]
        pkg = None
        for p in self.argos_packages:
            pkg_id = p.get("package_version", "") or f"{p.get('from_name', '')}_{p.get('to_name', '')}"
            if pkg_id == iid:
                pkg = p
                break
        if pkg is None:
            return
        threading.Thread(target=self._do_argos_download, args=(pkg, tree, iid), daemon=True).start()

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
            resp = urlopen(req, timeout=60)
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

    def _refresh_main_combos(self):
        """Update the language dropdowns in the main transcribe tab."""
        langs = sorted(LanguageManager.data.keys())
        if hasattr(self.app, "from_combo"):
            self.app.from_combo.configure(values=langs)
            self.app.to_combo.configure(values=langs)

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
