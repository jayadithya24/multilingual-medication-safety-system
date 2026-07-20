from functools import lru_cache
from pathlib import Path

import json
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "datasets"
CSV_PATH = DATA_DIR / "drug_interactions.csv"
JSON_PATH = DATA_DIR / "drug_interactions.json"


def _normalize_drug_name(drug_name):
    return str(drug_name).strip().lower()


@lru_cache(maxsize=1)
def _load_interaction_table():
    """Load interaction data from CSV or JSON once and reuse it."""

    try:
        if CSV_PATH.exists():
            dataframe = pd.read_csv(CSV_PATH)
        elif JSON_PATH.exists():
            with open(JSON_PATH, "r", encoding="utf-8") as file_handle:
                payload = json.load(file_handle)
            dataframe = pd.DataFrame(payload)
        else:
            return None

        expected_columns = {
            "drug_1",
            "drug_2",
            "severity",
            "description",
            "recommendation",
        }

        if not expected_columns.issubset(dataframe.columns):
            return None

        for column in expected_columns:
            dataframe[column] = dataframe[column].astype(str)

        return dataframe
    except Exception:
        return None


def get_interaction(drug1, drug2):
    """Return the first matching interaction for the two drugs regardless of order."""

    if not drug1 or not drug2:
        return None

    dataframe = _load_interaction_table()
    if dataframe is None:
        return None

    normalized_drug1 = _normalize_drug_name(drug1)
    normalized_drug2 = _normalize_drug_name(drug2)

    if not normalized_drug1 or not normalized_drug2:
        return None

    drug_a = dataframe["drug_1"].str.lower().str.strip()
    drug_b = dataframe["drug_2"].str.lower().str.strip()

    forward_match = (drug_a == normalized_drug1) & (drug_b == normalized_drug2)
    reverse_match = (drug_a == normalized_drug2) & (drug_b == normalized_drug1)

    matches = dataframe[forward_match | reverse_match]

    if matches.empty:
        return None

    first_match = matches.iloc[0]

    return {
        "severity": first_match["severity"],
        "description": first_match["description"],
        "recommendation": first_match["recommendation"],
    }