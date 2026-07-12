# PolyScribe

PolyScribe is a lightweight desktop tool for fully offline live **speech transcription** and **translation**, powered by [Vosk](https://alphacephei.com/vosk/) and [Argos Translate](https://www.argosopentech.com/). It includes a desktop GUI with real-time transcription display, a built-in model downloader, and optional text-to-speech output.

## Features

- 🎙️ Real-time speech recognition (fully offline, powered by Vosk)
- 🌐 Translate spoken language into another language (supports 20+ languages via Argos Translate)
- 🔊 Text-to-speech output of transcribed or translated text
- 🖥️ Desktop GUI — live transcription display, model manager, dark theme
- 📦 Built-in model downloader — download Vosk and Argos models without leaving the app
- ⚙️ Auto-detects models — drop a Vosk model into `models/vosk_models/` and it's automatically available
- 🧪 Unit test suite (pytest) and GitHub Actions CI
- 💻 Terminal mode also available for headless/server use

## Requirements

- Python 3.11 (important: `sentencepiece` and `wheel` may break on later versions)
- Works on macOS, Windows, and Linux with compatible audio devices
- Tkinter (usually bundled with Python; on Linux: `sudo apt install python3-tk`)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/kcitlyn/PolyScribe_Desktop.git
cd PolyScribe_Desktop

# 2. Create virtual environment (Python 3.11 recommended)
python3.11 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the GUI
python src/gui.py
```

On first launch, use the **Model Manager** tab to download a Vosk speech model and any Argos translation packages you need. No manual file juggling required.

## Usage

### GUI Mode (recommended)

```bash
python src/gui.py
```

The GUI provides:
- **Transcribe / Translate tab** — select your microphone, source & target language, toggle TTS, and click Start
- **Model Manager tab** — browse & download Vosk models (small → full accuracy) and Argos translation packages with a progress bar

### Terminal Mode

```bash
python src/main.py
```

Follow the on-screen prompts to select microphone, mode (transcription vs. translation), and language preferences.

## Manual Model Setup (optional)

If you prefer to download models manually:

1. Create the folders:
   ```
   models/
   ├── vosk_models/      ← unzipped Vosk model folders go here
   └── translation_models/ ← .argosmodel files go here
   ```

2. Download Vosk models from https://alphacephei.com/vosk/models

3. Download Argos models from https://www.argosopentech.com/argospm/index/

4. Install Argos packages:
   ```bash
   python install_translation_package.py
   ```

PolyScribe auto-detects any Vosk model folder by its name (e.g. `vosk-model-small-fr-0.22` → French). No code changes needed.

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests run without any hardware or downloaded models — they validate logic, resampling math, and module interfaces.

## Project Structure

```
PolyScribe_Desktop/
├── src/
│   ├── gui.py                  # Desktop GUI (Tkinter)
│   ├── model_manager.py        # Model downloader UI
│   ├── main.py                 # Terminal mode entry point
│   ├── utils.py                # Terminal prompts & audio loop
│   ├── languages/
│   │   ├── languages.py        # Auto-scans vosk_models/, manages codes
│   │   ├── speak.py            # Text-to-speech (pyttsx3)
│   │   └── voice_config.json   # TTS defaults
│   └── translation/
│       ├── transcription.py    # Vosk streaming recognizer
│       └── text_translate.py   # Argos translation wrapper
├── tests/                      # pytest suite
├── models/                     # (gitignored) downloaded models
├── requirements.txt
├── install_translation_package.py
└── .github/workflows/test.yml  # CI
```

## Text-to-Speech Voices

The TTS feature uses `pyttsx3`, which relies on voices installed on your OS:

- **macOS:** Most languages come pre-installed.
- **Windows:** Settings → Time & Language → Speech → Add voices.
- **Linux:** Install `espeak-ng` or `festival` via your package manager.

List all available voices:
```python
from languages.speak import Speak
Speak.print_all_voices_available()
```

## Licenses and Third-Party Software

- [Vosk](https://github.com/alphacep/vosk-api) — Apache License 2.0 ([license](./third_party/vosk-api-LICENSE.txt))
- [Argos Translate](https://github.com/argosopentech/argos-translate) — GNU GPLv3 ([license](./third_party/argostranslate-LICENSE.txt))

---

If you found this project helpful or interesting, I'd really appreciate a ⭐! If you run into issues, have suggestions, or want to contribute, feel free to open an issue or submit a pull request.
