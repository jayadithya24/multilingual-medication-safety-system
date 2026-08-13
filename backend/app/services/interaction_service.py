from functools import lru_cache
from pathlib import Path
import json
import itertools
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT_CSV = PROJECT_ROOT / "datasets" / "drug_interactions.csv"
APP_CSV = Path(__file__).resolve().parents[1] / "datasets" / "drug_interactions.csv"
JSON_PATH = Path(__file__).resolve().parents[1] / "datasets" / "drug_interactions.json"


def _normalize_drug_name(drug_name):
    return str(drug_name).strip().lower()


@lru_cache(maxsize=1)
def _load_interaction_table():
    """Load interaction data from root or app dataset once and normalize columns."""
    paths = [ROOT_CSV, APP_CSV]
    
    dataframe = None
    for path in paths:
        if path.exists():
            try:
                dataframe = pd.read_csv(path)
                break
            except Exception:
                continue

    if dataframe is None and JSON_PATH.exists():
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as file_handle:
                payload = json.load(file_handle)
            dataframe = pd.DataFrame(payload)
        except Exception:
            dataframe = None

    if dataframe is None:
        return None

    # Handle root dataset column names (drug1, drug2)
    if "drug1" in dataframe.columns and "drug2" in dataframe.columns:
        dataframe["drug_1"] = dataframe["drug1"].astype(str)
        dataframe["drug_2"] = dataframe["drug2"].astype(str)

    if "drug_1" not in dataframe.columns or "drug_2" not in dataframe.columns:
        return None

    dataframe["drug_1"] = dataframe["drug_1"].astype(str)
    dataframe["drug_2"] = dataframe["drug_2"].astype(str)

    if "severity" not in dataframe.columns:
        dataframe["severity"] = "Moderate"
    else:
        dataframe["severity"] = dataframe["severity"].astype(str)

    if "description" not in dataframe.columns:
        dataframe["description"] = dataframe.apply(
            lambda r: f"Co-administration of {r['drug_1']} and {r['drug_2']} has a recognized {r['severity']} interaction potential.",
            axis=1,
        )

    if "recommendation" not in dataframe.columns:
        dataframe["recommendation"] = dataframe.apply(
            lambda r: f"Clinical monitoring advised when combining {r['drug_1']} and {r['drug_2']}.",
            axis=1,
        )

    return dataframe


def get_interaction(drug1, drug2, lang: str = "en"):
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

    # Also try partial matching on drug names if exact fails
    matches = dataframe[forward_match | reverse_match]

    if matches.empty:
        forward_partial = (drug_a.str.contains(normalized_drug1, regex=False)) & (
            drug_b.str.contains(normalized_drug2, regex=False)
        )
        reverse_partial = (drug_a.str.contains(normalized_drug2, regex=False)) & (
            drug_b.str.contains(normalized_drug1, regex=False)
        )
        matches = dataframe[forward_partial | reverse_partial]

    if matches.empty:
        return None

    first_match = matches.iloc[0]

    return {
        "drug1": str(first_match["drug_1"]),
        "drug2": str(first_match["drug_2"]),
        "severity": str(first_match["severity"]),
        "description": str(first_match["description"]),
        "recommendation": str(first_match["recommendation"]),
        "lang": lang,
    }


def get_multi_drug_interactions(drugs, lang: str = "en"):
    """Evaluate pairwise interactions across a list of 2 or more drugs."""
    if not drugs or len(drugs) < 2:
        return {
            "status": "error",
            "message": "At least 2 drugs are required for multi-drug interaction checking.",
            "interactions": [],
            "max_severity": "None",
        }

    clean_drugs = list(dict.fromkeys([str(d).strip() for d in drugs if str(d).strip()]))
    interactions = []
    severities_found = []

    for d1, d2 in itertools.combinations(clean_drugs, 2):
        match = get_interaction(d1, d2, lang=lang)
        if match:
            interactions.append(match)
            severities_found.append(match["severity"].capitalize())

    # Order max severity: Severe > Moderate > Mild > None
    severity_order = {"Severe": 3, "High": 3, "Moderate": 2, "Low": 1, "Mild": 1}
    max_sev = "None"
    if severities_found:
        max_sev = max(severities_found, key=lambda s: severity_order.get(s, 0))

    return {
        "status": "success",
        "drugs_analyzed": clean_drugs,
        "total_interactions_found": len(interactions),
        "max_severity": max_sev,
        "interactions": interactions,
        "lang": lang,
    }
