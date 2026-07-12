"""
Theme definitions and persistence for the PolyScribe GUI.

Each theme defines a full palette. The user's chosen theme is saved to
settings.json next to this file and restored on next launch.
"""

import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"

# key: internal name -> palette
# bg        window background
# surface   cards / panels
# surface2  hover / inputs
# text      primary text
# subtext   secondary text
# accent    buttons, highlights, titles
# accent2   secondary accent (translated text)
# success   final transcription text
# muted     partial (in-progress) text
# border    card outlines
THEMES = {
    "Midnight": {
        "emoji": "🌙",
        "bg": "#11111b", "surface": "#1e1e2e", "surface2": "#313244",
        "text": "#cdd6f4", "subtext": "#a6adc8", "accent": "#89b4fa",
        "accent2": "#cba6f7", "success": "#a6e3a1", "muted": "#6c7086",
        "border": "#45475a", "dark": True,
    },
    "Daylight": {
        "emoji": "☀️",
        "bg": "#eff1f5", "surface": "#ffffff", "surface2": "#e6e9ef",
        "text": "#4c4f69", "subtext": "#6c6f85", "accent": "#1e66f5",
        "accent2": "#8839ef", "success": "#40a02b", "muted": "#9ca0b0",
        "border": "#dce0e8", "dark": False,
    },
    "Sakura": {
        "emoji": "🌸",
        "bg": "#fdf2f5", "surface": "#ffffff", "surface2": "#fce4ec",
        "text": "#5d4157", "subtext": "#96707f", "accent": "#e91e8c",
        "accent2": "#ab47bc", "success": "#66a06b", "muted": "#c9a9b8",
        "border": "#f3d1de", "dark": False,
    },
    "Strawberry Milk": {
        "emoji": "🍓",
        "bg": "#fff0f3", "surface": "#fffafb", "surface2": "#ffe0e9",
        "text": "#6b3844", "subtext": "#a3707e", "accent": "#ff6392",
        "accent2": "#c74b7c", "success": "#7fb069", "muted": "#d8a7b5",
        "border": "#ffd1dc", "dark": False,
    },
    "Matcha": {
        "emoji": "🍵",
        "bg": "#f3f7ee", "surface": "#fdfff8", "surface2": "#e4eed6",
        "text": "#3f4b32", "subtext": "#71805e", "accent": "#6a994e",
        "accent2": "#a7c957", "success": "#386641", "muted": "#a8b79a",
        "border": "#d5e3c0", "dark": False,
    },
    "Lavender": {
        "emoji": "💜",
        "bg": "#f5f2fb", "surface": "#fefcff", "surface2": "#eae3f7",
        "text": "#4a3f63", "subtext": "#7d719c", "accent": "#8b5cf6",
        "accent2": "#c084fc", "success": "#65a30d", "muted": "#b3a6d1",
        "border": "#ddd1f0", "dark": False,
    },
    "Ocean": {
        "emoji": "🌊",
        "bg": "#0f1c2e", "surface": "#16283e", "surface2": "#1f3a5c",
        "text": "#d6e5f3", "subtext": "#9db8d2", "accent": "#4cc9f0",
        "accent2": "#80ffdb", "success": "#72efdd", "muted": "#5e7f9e",
        "border": "#2c4a6e", "dark": True,
    },
    "Peach": {
        "emoji": "🍑",
        "bg": "#fff4ec", "surface": "#fffdfa", "surface2": "#ffe8d6",
        "text": "#6e4a35", "subtext": "#a17c62", "accent": "#f4845f",
        "accent2": "#f27059", "success": "#7fb069", "muted": "#d4b49c",
        "border": "#f8d9c0", "dark": False,
    },
}

DEFAULT_THEME = "Midnight"


def theme_display_names():
    """Names shown in the theme picker, e.g. '🌙 Midnight'."""
    return [f"{t['emoji']} {name}" for name, t in THEMES.items()]


def theme_from_display_name(display_name):
    """'🌙 Midnight' -> 'Midnight' (falls back to default)."""
    for name, t in THEMES.items():
        if display_name == f"{t['emoji']} {name}" or display_name == name:
            return name
    return DEFAULT_THEME


def load_settings():
    try:
        with open(SETTINGS_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass  # settings persistence is best-effort


def load_theme_name():
    name = load_settings().get("theme", DEFAULT_THEME)
    return name if name in THEMES else DEFAULT_THEME


def save_theme_name(name):
    settings = load_settings()
    settings["theme"] = name
    save_settings(settings)


def get_theme(name=None):
    return THEMES.get(name or load_theme_name(), THEMES[DEFAULT_THEME])
