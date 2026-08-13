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

        search_columns = [
            column
            for column in ["drug_name", "generic_name", "active_ingredient"]
            if column in dataframe.columns
        ]
        if not search_columns:
            return None

        normalized_columns = {
            column: dataframe[column].astype(str).str.lower().str.strip()
            for column in search_columns
        }

        # Search exact match first, then partial match
        exact_mask = None
        for series in normalized_columns.values():
            column_mask = series == normalized_name
            exact_mask = column_mask if exact_mask is None else (exact_mask | column_mask)

        exact_matches = dataframe[exact_mask] if exact_mask is not None else dataframe.iloc[0:0]
        if not exact_matches.empty:
            match_dict = exact_matches.iloc[0].to_dict()
            match_dict["lang"] = lang
            return match_dict

        partial_mask = None
        for series in normalized_columns.values():
            column_mask = series.str.contains(normalized_name, na=False, regex=False)
            partial_mask = column_mask if partial_mask is None else (partial_mask | column_mask)

        matches = dataframe[partial_mask] if partial_mask is not None else dataframe.iloc[0:0]

        if matches.empty:
            # Fallback to English if not found in requested language
            if lang != "en":
                en_df = _load_dataset("en")
                if en_df is not None:
                    available_columns = [
                        column
                        for column in ["drug_name", "generic_name", "active_ingredient"]
                        if column in en_df.columns
                    ]
                    if available_columns:
                        fallback_mask = None
                        for column in available_columns:
                            series = en_df[column].astype(str).str.lower().str.strip()
                            column_mask = series.str.contains(normalized_name, na=False, regex=False)
                            fallback_mask = column_mask if fallback_mask is None else (fallback_mask | column_mask)
                        matches = en_df[fallback_mask] if fallback_mask is not None else en_df.iloc[0:0]

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
        dataframe = _load_dataset(lang)
        if dataframe is None:
            dataframe = _load_dataset("en")
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
