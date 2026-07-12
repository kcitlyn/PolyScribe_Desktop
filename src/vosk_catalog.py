"""
Full catalog of Vosk speech recognition models, mirrored from the official
model list at https://alphacephei.com/vosk/models

Every entry downloads from https://alphacephei.com/vosk/models/<name>.zip

quality tiers:
  small  — lightweight (~40-150 MB), fast, good for real-time on any machine
  medium — mid-size, better accuracy, still desktop-friendly
  large  — big server-grade models (1 GB+), best accuracy, slower to load

`accuracy` is the word error rate (WER) reported upstream — lower is better.
Speaker-ID and punctuation models are excluded: PolyScribe can't use them.
"""

BASE_URL = "https://alphacephei.com/vosk/models"


def _m(name, lang, quality, size, accuracy="", license_="Apache 2.0"):
    return {
        "name": name,
        "lang": lang,
        "quality": quality,
        "size": size,
        "accuracy": accuracy,
        "license": license_,
        "url": f"{BASE_URL}/{name}.zip",
    }


VOSK_MODELS = [
    # --- English (US) ---
    _m("vosk-model-small-en-us-0.15", "English (US)", "small", "40 MB", "WER 9.85"),
    _m("vosk-model-en-us-0.22-lgraph", "English (US)", "medium", "128 MB", "WER 7.82"),
    _m("vosk-model-en-us-0.22", "English (US)", "large", "1.8 GB", "WER 5.69"),
    _m("vosk-model-en-us-0.42-gigaspeech", "English (US)", "large", "2.3 GB", "WER 5.64"),
    _m("vosk-model-en-us-daanzu-20200905", "English (US)", "large", "1.0 GB", "WER 7.08", "AGPL"),
    _m("vosk-model-en-us-daanzu-20200905-lgraph", "English (US)", "medium", "129 MB", "WER 8.20", "AGPL"),
    _m("vosk-model-en-us-librispeech-0.2", "English (US)", "large", "845 MB"),
    _m("vosk-model-small-en-us-zamia-0.5", "English (US)", "small", "49 MB", "WER 11.55", "LGPL-3.0"),
    _m("vosk-model-en-us-aspire-0.2", "English (US)", "large", "1.4 GB", "WER 13.64"),
    _m("vosk-model-en-us-0.21", "English (US)", "large", "1.6 GB", "WER 5.43"),
    # --- English (Indian) ---
    _m("vosk-model-small-en-in-0.4", "English (Indian)", "small", "36 MB", "WER 49.05"),
    _m("vosk-model-en-in-0.5", "English (Indian)", "large", "1.0 GB", "WER 36.12"),
    # --- Chinese ---
    _m("vosk-model-small-cn-0.22", "Chinese (Mandarin)", "small", "42 MB", "WER 23.54"),
    _m("vosk-model-cn-0.22", "Chinese (Mandarin)", "large", "1.3 GB", "WER 13.98"),
    _m("vosk-model-cn-kaldi-multicn-0.15", "Chinese (Mandarin)", "large", "1.5 GB", "WER 17.44"),
    # --- Russian ---
    _m("vosk-model-small-ru-0.22", "Russian", "small", "45 MB", "WER 22.71"),
    _m("vosk-model-ru-0.42", "Russian", "large", "1.8 GB", "WER 4.5"),
    _m("vosk-model-ru-0.22", "Russian", "large", "1.5 GB", "WER 5.74"),
    _m("vosk-model-ru-0.10", "Russian", "large", "2.5 GB", "WER 5.71"),
    # --- French ---
    _m("vosk-model-small-fr-0.22", "French", "small", "41 MB", "WER 23.95"),
    _m("vosk-model-fr-0.22", "French", "large", "1.4 GB", "WER 14.72"),
    _m("vosk-model-small-fr-pguyot-0.3", "French", "small", "39 MB", "WER 37.04", "CC BY-NC-SA 4.0"),
    _m("vosk-model-fr-0.6-linto-2.2.0", "French", "large", "1.5 GB", "WER 16.19", "AGPL"),
    # --- German ---
    _m("vosk-model-small-de-0.15", "German", "small", "45 MB", "WER 13.75"),
    _m("vosk-model-de-0.21", "German", "large", "1.9 GB", "WER 9.83"),
    _m("vosk-model-de-tuda-0.6-900k", "German", "large", "4.4 GB", "WER 9.48"),
    _m("vosk-model-small-de-zamia-0.3", "German", "small", "49 MB", "WER 14.81", "LGPL-3.0"),
    # --- Spanish ---
    _m("vosk-model-small-es-0.42", "Spanish", "small", "39 MB", "WER 16.02"),
    _m("vosk-model-es-0.42", "Spanish", "large", "1.4 GB", "WER 7.50"),
    # --- Portuguese ---
    _m("vosk-model-small-pt-0.3", "Portuguese", "small", "31 MB", "WER 32.60"),
    _m("vosk-model-pt-fb-v0.1.1-20220516_2113", "Portuguese", "large", "1.6 GB", "WER 27.70", "GPLv3.0"),
    # --- Greek ---
    _m("vosk-model-el-gr-0.7", "Greek", "large", "1.1 GB"),
    # --- Turkish ---
    _m("vosk-model-small-tr-0.3", "Turkish", "small", "35 MB"),
    # --- Vietnamese ---
    _m("vosk-model-small-vn-0.4", "Vietnamese", "small", "32 MB", "WER 15.70"),
    _m("vosk-model-vn-0.4", "Vietnamese", "medium", "78 MB", "WER 15.70"),
    # --- Italian ---
    _m("vosk-model-small-it-0.22", "Italian", "small", "48 MB", "WER 16.88"),
    _m("vosk-model-it-0.22", "Italian", "large", "1.2 GB", "WER 8.10"),
    # --- Dutch ---
    _m("vosk-model-small-nl-0.22", "Dutch", "small", "39 MB", "WER 22.45"),
    _m("vosk-model-nl-spraakherkenning-0.6", "Dutch", "large", "860 MB", "WER 20.40", "CC BY-NC-SA"),
    _m("vosk-model-nl-spraakherkenning-0.6-lgraph", "Dutch", "medium", "100 MB", "WER 22.82", "CC BY-NC-SA"),
    # --- Catalan ---
    _m("vosk-model-small-ca-0.4", "Catalan", "small", "42 MB"),
    # --- Arabic ---
    _m("vosk-model-ar-mgb2-0.4", "Arabic", "medium", "318 MB", "WER 16.40"),
    _m("vosk-model-ar-0.22-linto-1.1.0", "Arabic", "large", "1.3 GB", "WER 28.50", "AGPL"),
    # --- Arabic (Tunisian) ---
    _m("vosk-model-small-ar-tn-0.1-linto", "Arabic (Tunisian)", "medium", "158 MB", "WER 16.06"),
    _m("vosk-model-ar-tn-0.1-linto", "Arabic (Tunisian)", "medium", "517 MB", "WER 16.06"),
    # --- Farsi (Persian) ---
    _m("vosk-model-small-fa-0.42", "Farsi (Persian)", "small", "53 MB", "WER 23.4"),
    _m("vosk-model-fa-0.42", "Farsi (Persian)", "large", "1.6 GB", "WER 16.7"),
    _m("vosk-model-small-fa-0.5", "Farsi (Persian)", "small", "60 MB", "WER 31.2"),
    _m("vosk-model-fa-0.5", "Farsi (Persian)", "large", "1.0 GB", "WER 29.7"),
    # --- Filipino ---
    _m("vosk-model-tl-ph-generic-0.6", "Filipino (Tagalog)", "medium", "320 MB", "WER 18.87", "CC BY-NC-SA 4.0"),
    # --- Ukrainian ---
    _m("vosk-model-small-uk-v3-nano", "Ukrainian", "small", "73 MB"),
    _m("vosk-model-small-uk-v3-small", "Ukrainian", "small", "133 MB"),
    _m("vosk-model-uk-v3", "Ukrainian", "medium", "343 MB"),
    _m("vosk-model-uk-v3-lgraph", "Ukrainian", "medium", "325 MB"),
    # --- Kazakh ---
    _m("vosk-model-small-kz-0.42", "Kazakh", "small", "58 MB", "WER 9.7"),
    _m("vosk-model-kz-0.42", "Kazakh", "large", "1.3 GB", "WER 4.49"),
    # --- Swedish ---
    _m("vosk-model-small-sv-rhasspy-0.15", "Swedish", "medium", "289 MB", "", "MIT"),
    # --- Japanese ---
    _m("vosk-model-small-ja-0.22", "Japanese", "small", "48 MB", "CER 9.52"),
    _m("vosk-model-ja-0.22", "Japanese", "large", "1.0 GB", "CER 8.40"),
    # --- Esperanto ---
    _m("vosk-model-small-eo-0.42", "Esperanto", "small", "42 MB", "WER 7.24"),
    # --- Hindi ---
    _m("vosk-model-small-hi-0.22", "Hindi", "small", "42 MB", "WER 20.89"),
    _m("vosk-model-hi-0.22", "Hindi", "large", "1.5 GB", "WER 14.85"),
    # --- Czech ---
    _m("vosk-model-small-cs-0.4-rhasspy", "Czech", "small", "44 MB", "WER 21.29", "MIT"),
    # --- Polish ---
    _m("vosk-model-small-pl-0.22", "Polish", "small", "50 MB", "WER 18.36"),
    # --- Uzbek ---
    _m("vosk-model-small-uz-0.22", "Uzbek", "small", "49 MB", "WER 13.54"),
    # --- Korean ---
    _m("vosk-model-small-ko-0.22", "Korean", "small", "82 MB", "WER 28.1"),
    # --- Breton ---
    _m("vosk-model-br-0.8", "Breton", "medium", "70 MB", "WER 36.4", "MIT"),
    # --- Gujarati ---
    _m("vosk-model-small-gu-0.42", "Gujarati", "medium", "100 MB", "WER 20.49"),
    _m("vosk-model-gu-0.42", "Gujarati", "large", "700 MB", "WER 16.45"),
    # --- Tajik ---
    _m("vosk-model-small-tg-0.22", "Tajik", "small", "50 MB", "WER 38.4"),
    _m("vosk-model-tg-0.22", "Tajik", "medium", "327 MB", "WER 41.1"),
    # --- Telugu ---
    _m("vosk-model-small-te-0.42", "Telugu", "small", "58 MB"),
    # --- Kyrgyz ---
    _m("vosk-model-small-ky-0.42", "Kyrgyz", "small", "49 MB", "WER 16.96"),
    _m("vosk-model-ky-0.42", "Kyrgyz", "large", "1.1 GB", "WER 8.75"),
    # --- Georgian ---
    _m("vosk-model-small-ka-0.42", "Georgian", "small", "45 MB", "WER 14.2"),
    _m("vosk-model-ka-0.42", "Georgian", "large", "700 MB", "WER 5.2"),
]


def models_by_language():
    """Group the catalog: {language: [model, ...]} preserving catalog order."""
    grouped = {}
    for m in VOSK_MODELS:
        grouped.setdefault(m["lang"], []).append(m)
    return grouped


def find_model(name):
    return next((m for m in VOSK_MODELS if m["name"] == name), None)
