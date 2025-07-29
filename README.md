# PolyScribe

PolyScribe is a lightweight desktop tool for fully offline live **speech transcription** and **translation**, powered by [Vosk](https://alphacephei.com/vosk/) and [Argos Translate](https://www.argosopentech.com/). It allows users to speak into their microphone and receive live transcriptions and/or translations spoken out loud, based on customizable language preferences.

## Features

- 🎙️ Real-time speech recognition (fully offline)
- 🌐 Translate spoken language into another language
- 🔊 Text-to-speech output of transcribed or translated text
- 🧠 Built using Vosk + Argos Translate
- ⚙️ Customizable models and preferences
- ✨ Currently terminal-Based (GUI coming soon)

## Requirements

- Python 3.11.9 (important: `sentencepiece` and `wheel` may break on later versions)
- Works on Windows with compatible audio devices
- Basic terminal/command line usage

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/PolyScribe.git
   cd PolyScribe
   ```

2. Set up virtual environment
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate.ps1
    ```

3. Install required packages
    ```bash
    pip install -r requirements.txt
    ```

4. Download and setup voice and translation models
    Create the following folder structure inside the provided models/ directory:
    models/
    ├── vosk_models/
    └── translation_models/
    Download Vosk models from:
    - https://alphacephei.com/vosk/models

    Download Argos Translate models from:
    - https://www.argosopentech.com/argospm/index/

    Place the downloaded model folders into their respective directories as-is. Keep the original folder names and structure!!

5. Install translation packages
    Run this script once (and again only if you add new translation models into your translation_models folder):
    ```bash
    python install_translation_packages.py
    ```

6. (optional) Check available voice models depending on system
    The text-to-speech package used in this project (`pyttsx3`) relies on **voice packages locally installed on your device**.

- **macOS:**  
  Most common languages and voices come pre-installed, so you usually don’t need to do anything extra.

- **Windows:**  
  By default, Windows typically only includes voice packages for the system’s native language (e.g., English).  
  To access more languages, you need to manually install additional voice packages:  
  1. Open **Settings**  
  2. Go to **Time & Language > Speech**  
  3. Under **Manage voices**, click **Add voices**  
  4. Select the desired language(s) and install  

- **Linux:**  
  Voice availability depends on the text-to-speech engine installed (such as `espeak`, `festival`, or `pico2wave`).  
  Most Linux distros come with basic voices installed (often English). To add more languages, you typically need to:  
  - Install additional speech synthesis packages via your package manager (e.g., `apt install espeak-ng` or `sudo apt install festival`)  
  - Download or configure language-specific voice packs depending on your TTS engine  
  - Some distros offer GUI tools for managing voices, but manual installation is common  

    Run this to print all of your systems downloaded local voice packages
        >>> from languages.speak import Speak   # adjust module path as needed
        >>> Speak.print_all_voices_available()

7. Run the application
  ```bash
    python3 main.py
  ```

8. Answer terminal prompts
  Follow the on-screen prompts to select your transcription and translation preferences. The program will then listen and respond accordingly.

## Notes

- Do not modify the structure or names of model folders. The app relies on consistent relative paths to find them.
- If your packages are being deleted on Windows, make sure you're working inside your virtual environment and that your IDE or antivirus isn't removing packages.

## Example Folder Structure

  PolyScribe/  
  ├── main.py  
  ├── install_translation_packages.py  
  ├── requirements.txt  
  ├── models/  
  │   ├── vosk_models/  
  │   │   └── vosk-model-small-en-us-0.15/  
  │   └── translation_models/  
  │       └── en_es/  
  ├── languages/  
  ├── translation/  
  ├── licenses/  
  └── ...  

## Licenses and Third-Party Software

This project uses the following open-source libraries:

- [Vosk](https://github.com/alphacep/vosk-api) - Speech recognition toolkit, licensed under the [Apache License 2.0](./third_party/vosk-api-LICENSE.txt) 
- [Argos Translate](https://github.com/argosopentech/argos-translate) - Machine translation library, licensed under the [GNU General Public License v3.0](./third_party/argostranslate-LICENSE.txt) 

See the third_party/ folder for full license texts.
