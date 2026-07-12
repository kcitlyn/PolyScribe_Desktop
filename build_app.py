"""
Build a standalone PolyScribe app with PyInstaller.

Usage:
    pip install pyinstaller
    python build_app.py

Output lands in dist/:
    macOS   -> dist/PolyScribe.app
    Windows -> dist/PolyScribe/PolyScribe.exe
    Linux   -> dist/PolyScribe/PolyScribe

Models are NOT bundled — the app downloads them via the Model Manager
into a models/ folder next to the executable on first run.
"""

import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


def main():
    sep = ";" if platform.system() == "Windows" else ":"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "PolyScribe",
        "--paths", str(SRC),
        # data files the app reads at runtime
        "--add-data", f"{SRC / 'languages' / 'voice_config.json'}{sep}languages",
        # vosk ships a native library PyInstaller misses without this
        "--collect-all", "vosk",
        "--collect-all", "argostranslate",
        str(SRC / "gui.py"),
    ]
    print(" ".join(args))
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode == 0:
        print("\nBuild complete — see the dist/ folder.")
    else:
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
