from functools import lru_cache
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT_DATASETS = PROJECT_ROOT / "datasets"
APP_DATASETS = Path(__file__).resolve().parents[1] / "datasets"


@lru_cache(maxsize=3)
def _load_dataset(lang: str = "en"):
    """Load English, Kannada, or Tulu dataset dynamically."""
    lang = (lang or "en").strip().lower()

    filename = "english_master_dataset.csv"
    if lang == "kn":
        filename = "kannada_master_dataset.csv"
    elif lang == "tulu":
        filename = "tulu_master_dataset.csv"

    possible_paths = [
        ROOT_DATASETS / filename,
        APP_DATASETS / filename,
        ROOT_DATASETS / "english_master_dataset.csv",
        APP_DATASETS / "english_master_dataset.csv",
    ]

    for path in possible_paths:
        if path.exists():
            try:
                dataframe = pd.read_csv(path)
                if "drug_name" in dataframe.columns:
                    dataframe["drug_name"] = dataframe["drug_name"].astype(str)
                    return dataframe
            except Exception:
                continue

    return None


def search_medicine(medicine_name: str, lang: str = "en"):
    """Search the master dataset by drug name using case-insensitive partial matching."""
    try:
        if not medicine_name:
            return None

        dataframe = _load_dataset(lang)
        if dataframe is None or "drug_name" not in dataframe.columns:
            dataframe = _load_dataset("en")

        if dataframe is None or "drug_name" not in dataframe.columns:
            return None

        normalized_name = str(medicine_name).strip().lower()
        if not normalized_name:
            return None

        # Search exact match first, then partial match
        exact_matches = dataframe[
            dataframe["drug_name"].str.lower().str.strip() == normalized_name
        ]
        if not exact_matches.empty:
            match_dict = exact_matches.iloc[0].to_dict()
            match_dict["lang"] = lang
            return match_dict

        matches = dataframe[
            dataframe["drug_name"].str.lower().str.contains(normalized_name, na=False, regex=False)
        ]

        if matches.empty:
            # Fallback to English if not found in requested language
            if lang != "en":
                en_df = _load_dataset("en")
                if en_df is not None:
                    matches = en_df[
                        en_df["drug_name"].str.lower().str.contains(normalized_name, na=False, regex=False)
                    ]

        if matches.empty:
            return None

        match_dict = matches.iloc[0].to_dict()
        match_dict["lang"] = lang
        return match_dict

    except Exception as err:
        print(f"Error in search_medicine: {err}")
        return None


def list_medicine_names(lang: str = "en"):
    """Return a sorted list of unique medicine names for dropdown usage."""
    try:
        dataframe = _load_dataset(lang) or _load_dataset("en")
        if dataframe is None or "drug_name" not in dataframe.columns:
            return []

        medicines = (
            dataframe["drug_name"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        medicines = [medicine for medicine in medicines if medicine]
        return sorted(set(medicines), key=str.lower)

    except Exception:
        return []