from argostranslate import translate, package
from pathlib import Path
models_path = Path(__file__).resolve().parent / "models" / "translation_models"

#run this file anytime you add/ download any new translation models into translation_models folder.

def install_packages():
    print("Looking in:", models_path)
    for model_file in models_path.glob("*.argosmodel"):
        print(f"Installing: {model_file}")
        package.install_from_path(str(model_file))
    print("Download of things inside transltion_models folder completed successfully!")

if __name__ == "__main__":
    install_packages()