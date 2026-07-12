"""
Custom themed widgets for the PolyScribe GUI.

tk/ttk buttons ignore background colors on macOS, so we build our own
label-based buttons that render consistently on every platform.
"""

import tkinter as tk


class PillButton(tk.Label):
    """A flat, pill-style button built from a Label so colors work everywhere."""

    def __init__(self, parent, text, command, kind="primary", **kwargs):
        super().__init__(parent, text=text, cursor="hand2",
                         font=("Helvetica", 13, "bold"), padx=22, pady=8, **kwargs)
        self.command = command
        self.kind = kind  # primary | danger | ghost
        self._enabled = True
        self._palette = None
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self._enabled and self.command:
            self.command()

    def _on_enter(self, event=None):
        if self._enabled and self._palette:
            self.configure(bg=self._hover_color())

    def _on_leave(self, event=None):
        if self._palette:
            self.configure(bg=self._base_color())

    def _base_color(self):
        p = self._palette
        if not self._enabled:
            return p["surface2"]
        return {"primary": p["accent"], "danger": "#e05f78", "ghost": p["surface2"]}[self.kind]

    def _hover_color(self):
        p = self._palette
        return {"primary": p["accent2"], "danger": "#c94b63", "ghost": p["border"]}[self.kind]

    def _text_color(self):
        p = self._palette
        if not self._enabled:
            return p["muted"]
        if self.kind == "ghost":
            return p["text"]
        # White text on colored pills for dark themes; darker text for pastel accents
        return "#ffffff" if p["dark"] or self.kind == "danger" else "#ffffff"

    def apply_theme(self, palette):
        self._palette = palette
        self.configure(bg=self._base_color(), fg=self._text_color())

    def set_enabled(self, enabled):
        self._enabled = enabled
        if self._palette:
            self.apply_theme(self._palette)
        self.configure(cursor="hand2" if enabled else "arrow")


class Card(tk.Frame):
    """A surface panel with a subtle border, used to group controls."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bd=0, highlightthickness=1, **kwargs)

    def apply_theme(self, palette):
        self.configure(bg=palette["surface"],
                       highlightbackground=palette["border"],
                       highlightcolor=palette["border"])
