# app/services/voice_service.py

import io
import pandas as pd
from pathlib import Path
from gtts import gTTS

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"


def load_dataset_for_lang(lang: str) -> pd.DataFrame:
    dataset_files = {
        "kn": "kannada_master_dataset.csv",
        "tlu": "tulu_master_dataset.csv",
        "en": "english_master_dataset.csv"
    }

    file_name = dataset_files.get(lang.lower(), "english_master_dataset.csv")
    dataset_path = DATASETS_DIR / file_name

    if not dataset_path.exists():
        dataset_path = DATASETS_DIR / "english_master_dataset.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Master dataset file not found at {dataset_path}")

    return pd.read_csv(dataset_path)


def generate_conversational_response(medicine_name: str, user_query: str, lang: str = "kn") -> str:
    try:
        df = load_dataset_for_lang(lang)
    except Exception as e:
        return f"Error loading dataset: {str(e)}"

    name_col = next((c for c in df.columns if "name" in c.lower() or "drug" in c.lower()), df.columns[0])

    match = df[df[name_col].astype(str).str.lower() == medicine_name.lower()]
    if match.empty:
        match = df[df[name_col].astype(str).str.contains(medicine_name, case=False, na=False)]

    if match.empty:
        if lang == "kn":
            return f"{medicine_name} ಮಾತ್ರೆ ವಿವರಗಳು ಡೇಟಾಸೆಟ್‌ನಲ್ಲಿ ಕಂಡುಬಂದಿಲ್ಲ."
        elif lang == "tlu":
            return f"{medicine_name} ಮಾತ್ರೆದ ವಿವರೊಲು ಡೇಟಾಸೆಟ್‌ಡ್ ತಿಕ್ಕಿಜಿ."
        else:
            return f"{medicine_name} tablet details not found in dataset."

    disease_col = next((c for c in df.columns if any(k in c.lower() for k in ["disease", "indication", "use", "condition"])), None)

    if not disease_col:
        return "Disease column not found in dataset."

    dataset_disease = str(match.iloc[0][disease_col]).strip()
    query_words = [w.lower().strip() for w in user_query.split() if len(w) > 1]
    is_match = any(word in dataset_disease.lower() for word in query_words)

    if lang == "kn":
        return f"ಹೌದು, {medicine_name} ಮಾತ್ರೆ {dataset_disease} ಗಾಗಿ." if is_match else f"ಇಲ್ಲ, {medicine_name} ಮಾತ್ರೆ {dataset_disease} ಗಾಗಿ."
    elif lang == "tlu":
        return f"ಅಂದ್, {medicine_name} ಮಾತ್ರೆ {dataset_disease} ಗ್ ಆಪುಂಡು." if is_match else f"ಅತ್ತ್, {medicine_name} ಮಾತ್ರೆ {dataset_disease} ಗ್ ಆಪುಂಡು."
    else:
        return f"Yes, {medicine_name} is used for {dataset_disease}." if is_match else f"No, {medicine_name} is used for {dataset_disease}."


def text_to_speech_bytes(text: str, lang: str = "kn") -> bytes:
    gtts_lang = "kn" if lang in ["kn", "tlu"] else "en"
    tts = gTTS(text=text, lang=gtts_lang, slow=False)
    
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()