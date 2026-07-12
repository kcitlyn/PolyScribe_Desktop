from pathlib import Path

from argostranslate import package

MODELS_PATH = Path(__file__).resolve().parent / "models" / "translation_models"

# Run this file anytime you add/download new .argosmodel files into the
# models/translation_models folder.


def install_packages(models_path=MODELS_PATH):
    models_path = Path(models_path)
    if not models_path.is_dir():
        print(f"No translation models folder found at {models_path}")
        return 0
    installed = 0
    for model_file in sorted(models_path.glob("*.argosmodel")):
        print(f"Installing: {model_file.name}")
        package.install_from_path(str(model_file))
        installed += 1
    if installed:
        print(f"Installed {installed} translation package(s) successfully!")
    else:
        print(f"No .argosmodel files found in {models_path}")
    return installed


if __name__ == "__main__":
    install_packages()
