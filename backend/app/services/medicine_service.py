from functools import lru_cache
from pathlib import Path

import pandas as pd


DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "english_master_dataset.csv"


@lru_cache(maxsize=1)
def _load_dataset():
    """Load the medicine dataset once and reuse it for later searches."""

    try:
        dataframe = pd.read_csv(DATASET_PATH)
        dataframe["drug_name"] = dataframe["drug_name"].astype(str)
        return dataframe
    except FileNotFoundError:
        return None


def search_medicine(medicine_name):
    """Search the master dataset by drug name using case-insensitive partial matching."""

    try:
        if not medicine_name:
            return None

        dataframe = _load_dataset()
        if dataframe is None or "drug_name" not in dataframe.columns:
            return None

        normalized_name = str(medicine_name).strip().lower()
        if not normalized_name:
            return None

        matches = dataframe[
            dataframe["drug_name"].str.lower().str.contains(normalized_name, na=False, regex=False)
        ]

        if matches.empty:
            return None

        return matches.iloc[0].to_dict()

    except Exception:
        return None


def list_medicine_names():
    """Return a sorted list of unique medicine names for dropdown usage."""

    try:
        dataframe = _load_dataset()
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