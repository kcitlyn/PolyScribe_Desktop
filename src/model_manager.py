"""
Model Manager — browse, filter, download, and manage Vosk speech models
and Argos translation packages.
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
from vosk_catalog import VOSK_MODELS, models_by_language, find_model
from widgets import PillButton, Card

ARGOS_INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"


class ModelManagerFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bd=0, highlightthickness=0)
        self.app = app
        self._themed_widgets = []
        self._cards = []
        self._pills = []

        # Title
        header = self._reg(tk.Frame(self), "bg")
        header.pack(fill=tk.X, padx=4, pady=(12, 6))
        self._reg(tk.Label(header, text="Model Manager", font=("Helvetica", 18, "bold")),
                  "title").pack(side=tk.LEFT)
        self._reg(tk.Label(header, text=f"{len(VOSK_MODELS)} speech models available",
                           font=("Helvetica", 11)), "subtext").pack(side=tk.LEFT, padx=14)

        # ----- Vosk section -----
        vosk_card = Card(self)
        vosk_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(6, 4))
        self._cards.append(vosk_card)
        self._build_vosk_section(vosk_card)

        # ----- Argos section -----
        argos_card = Card(self)
        argos_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 4))
        self._cards.append(argos_card)
        self._build_argos_section(argos_card)

        # Progress bar
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

    # ====================================================================
    # Vosk speech models (full catalog with filters)
    # ====================================================================

    def _build_vosk_section(self, parent):
        # Header + filter bar
        top = self._reg(tk.Frame(parent), "surface")
        top.pack(fill=tk.X, padx=14, pady=(12, 4))
        self._reg(tk.Label(top, text="Speech Recognition (Vosk)",
                           font=("Helvetica", 13, "bold")), "label_on_surface").pack(side=tk.LEFT)

        filter_bar = self._reg(tk.Frame(parent), "surface")
        filter_bar.pack(fill=tk.X, padx=14, pady=(2, 4))

        self._reg(tk.Label(filter_bar, text="Language:", font=("Helvetica", 11)),
                  "label_on_surface").pack(side=tk.LEFT, padx=(0, 4))
        langs = ["All"] + sorted(set(m["lang"] for m in VOSK_MODELS))
        self.vosk_lang_filter = tk.StringVar(value="All")
        lang_cb = ttk.Combobox(filter_bar, textvariable=self.vosk_lang_filter,
                               values=langs, state="readonly", width=20, font=("Helvetica", 11))
        lang_cb.pack(side=tk.LEFT, padx=(0, 12))
        lang_cb.bind("<<ComboboxSelected>>", lambda e: self._populate_vosk_tree())

        self._reg(tk.Label(filter_bar, text="Size:", font=("Helvetica", 11)),
                  "label_on_surface").pack(side=tk.LEFT, padx=(0, 4))
        sizes = ["All", "small", "medium", "large"]
        self.vosk_size_filter = tk.StringVar(value="All")
        size_cb = ttk.Combobox(filter_bar, textvariable=self.vosk_size_filter,
                               values=sizes, state="readonly", width=10, font=("Helvetica", 11))
        size_cb.pack(side=tk.LEFT, padx=(0, 12))
        size_cb.bind("<<ComboboxSelected>>", lambda e: self._populate_vosk_tree())

        self.vosk_installed_only = tk.BooleanVar(value=False)
        ic = self._reg(
            tk.Checkbutton(filter_bar, text="Installed only", variable=self.vosk_installed_only,
                           font=("Helvetica", 11), bd=0, highlightthickness=0,
                           command=self._populate_vosk_tree),
            "check_on_surface")
        ic.pack(side=tk.LEFT, padx=(0, 4))

        # Treeview with more columns
        cols = ("language", "quality", "size", "accuracy", "license", "status")
        self.vosk_tree = ttk.Treeview(parent, columns=cols, show="headings", height=7)
        self.vosk_tree.heading("language", text="Language")
        self.vosk_tree.heading("quality", text="Quality")
        self.vosk_tree.heading("size", text="Size")
        self.vosk_tree.heading("accuracy", text="Accuracy")
        self.vosk_tree.heading("license", text="License")
        self.vosk_tree.heading("status", text="Status")
        self.vosk_tree.column("language", width=170)
        self.vosk_tree.column("quality", width=70, anchor="center")
        self.vosk_tree.column("size", width=70, anchor="center")
        self.vosk_tree.column("accuracy", width=100, anchor="center")
        self.vosk_tree.column("license", width=100, anchor="center")
        self.vosk_tree.column("status", width=90, anchor="center")
        self.vosk_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.vosk_tree.yview)
        self.vosk_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        self._populate_vosk_tree()

        # Buttons
        btn_frame = self._reg(tk.Frame(parent), "surface")
        btn_frame.pack(padx=14, pady=(4, 12))
        dl = PillButton(btn_frame, "Download", self._download_vosk, kind="primary")
        dl.pack(side=tk.LEFT, padx=4)
        rm = PillButton(btn_frame, "Delete", self._delete_vosk, kind="danger")
        rm.pack(side=tk.LEFT, padx=4)
        rf = PillButton(btn_frame, "Refresh", lambda: self._populate_vosk_tree(), kind="ghost")
        rf.pack(side=tk.LEFT, padx=4)
        self._pills += [dl, rm, rf]

    def _get_installed_vosk(self):
        if VOSK_MODELS_DIR.is_dir():
            return {f.name for f in VOSK_MODELS_DIR.iterdir() if f.is_dir()}
        return set()

    def _populate_vosk_tree(self):
        tree = self.vosk_tree
        tree.delete(*tree.get_children())
        installed = self._get_installed_vosk()
        lang_filter = self.vosk_lang_filter.get()
        size_filter = self.vosk_size_filter.get()
        installed_only = self.vosk_installed_only.get()

        for model in VOSK_MODELS:
            if lang_filter != "All" and model["lang"] != lang_filter:
                continue
            if size_filter != "All" and model["quality"] != size_filter:
                continue
            is_installed = model["name"] in installed
            if installed_only and not is_installed:
                continue
            status = "✓ Installed" if is_installed else "—"
            tree.insert("", tk.END, iid=model["name"],
                        values=(model["lang"], model["quality"], model["size"],
                                model["accuracy"], model["license"], status))

    def _download_vosk(self):
        selected = self.vosk_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a model from the list first.")
            return
        model_info = find_model(selected[0])
        if model_info:
            threading.Thread(target=self._do_vosk_download, args=(model_info,), daemon=True).start()

    def _do_vosk_download(self, model_info):
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
                    mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    self._set_progress(
                        downloaded / total * 90,
                        f"Downloading {name}… {mb:.0f} / {total_mb:.0f} MB")
            self._set_progress(92, f"Extracting {name}…")
            data.seek(0)
            with ZipFile(data) as zf:
                zf.extractall(VOSK_MODELS_DIR)
            self._set_progress(100, f"Done — {name} installed")
            LanguageManager.refresh()
            self.after(0, self._populate_vosk_tree)
            self.after(0, self.app.refresh_languages)
        except Exception as e:
            self._set_progress(0, f"Error: {e}")

    def _delete_vosk(self):
        import shutil
        selected = self.vosk_tree.selection()
        if not selected:
            return
        name = selected[0]
        path = VOSK_MODELS_DIR / name
        if not path.is_dir():
            messagebox.showinfo("Not installed", f"{name} is not installed.")
            return
        if messagebox.askyesno("Delete model", f"Delete {name}?\nThis cannot be undone."):
            shutil.rmtree(path)
            LanguageManager.refresh()
            self._populate_vosk_tree()
            self.app.refresh_languages()
            self._set_progress(0, f"Deleted {name}")

    # ====================================================================
    # Argos translation models (live index)
    # ====================================================================

    def _build_argos_section(self, parent):
        top = self._reg(tk.Frame(parent), "surface")
        top.pack(fill=tk.X, padx=14, pady=(12, 4))
        self._reg(tk.Label(top, text="Translation (Argos Translate)",
                           font=("Helvetica", 13, "bold")), "label_on_surface").pack(side=tk.LEFT)

        cols = ("pair", "size", "status")
        self.argos_tree = ttk.Treeview(parent, columns=cols, show="headings", height=5)
        self.argos_tree.heading("pair", text="Language Pair")
        self.argos_tree.heading("size", text="Size")
        self.argos_tree.heading("status", text="Status")
        self.argos_tree.column("pair", width=250)
        self.argos_tree.column("size", width=80, anchor="center")
        self.argos_tree.column("status", width=90, anchor="center")
        self.argos_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        self.argos_packages = []

        btn_frame = self._reg(tk.Frame(parent), "surface")
        btn_frame.pack(padx=14, pady=(4, 12))
        fetch = PillButton(btn_frame, "Load index", self._fetch_argos_index, kind="ghost")
        fetch.pack(side=tk.LEFT, padx=4)
        dl = PillButton(btn_frame, "Download", self._download_argos, kind="primary")
        dl.pack(side=tk.LEFT, padx=4)
        self._pills += [fetch, dl]

    def _fetch_argos_index(self):
        threading.Thread(target=self._do_fetch_argos_index, daemon=True).start()

    def _do_fetch_argos_index(self):
        self._set_progress(20, "Fetching Argos package index…")
        try:
            req = Request(ARGOS_INDEX_URL, headers={"User-Agent": "PolyScribe/1.0"})
            resp = urlopen(req, timeout=30)
            data = json.loads(resp.read())
            self.argos_packages = data if isinstance(data, list) else []
            self._set_progress(100, f"Loaded {len(self.argos_packages)} translation packages")
            self.after(0, self._populate_argos_tree)
        except Exception as e:
            self._set_progress(0, f"Error fetching index: {e}")

    def _populate_argos_tree(self):
        tree = self.argos_tree
        tree.delete(*tree.get_children())
        for i, pkg in enumerate(self.argos_packages):
            from_name = pkg.get("from_name", pkg.get("from_code", "?"))
            to_name = pkg.get("to_name", pkg.get("to_code", "?"))
            pair = f"{from_name} → {to_name}"
            size = self._fmt_size(pkg.get("package_size", pkg.get("size", 0)))
            tree.insert("", tk.END, iid=str(i), values=(pair, size, "—"))

    def _download_argos(self):
        selected = self.argos_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a package first.\nClick 'Load index' to fetch them.")
            return
        idx = int(selected[0])
        if idx < len(self.argos_packages):
            pkg = self.argos_packages[idx]
            threading.Thread(target=self._do_argos_download, args=(pkg, str(idx)), daemon=True).start()

    def _do_argos_download(self, pkg, iid):
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
                        mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        self._set_progress(
                            downloaded / total * 90,
                            f"Downloading {filename}… {mb:.0f} / {total_mb:.0f} MB")
            self._set_progress(92, f"Installing {filename}…")
            from argostranslate import package
            package.install_from_path(str(out_path))
            self._set_progress(100, f"Done — {filename} installed")
            self.after(0, lambda: self.argos_tree.set(iid, "status", "✓ Installed"))
        except Exception as e:
            self._set_progress(0, f"Error: {e}")

    # ====================================================================
    # Helpers
    # ====================================================================

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
                elif role == "check_on_surface":
                    widget.configure(bg=palette["surface"], fg=palette["text"],
                                     activebackground=palette["surface"],
                                     activeforeground=palette["text"],
                                     selectcolor=palette["surface2"])
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
