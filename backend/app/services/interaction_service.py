from functools import lru_cache
from pathlib import Path
import json
import itertools
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT_CSV = PROJECT_ROOT / "datasets" / "drug_interactions.csv"
APP_CSV = Path(__file__).resolve().parents[1] / "datasets" / "drug_interactions.csv"
JSON_PATH = Path(__file__).resolve().parents[1] / "datasets" / "drug_interactions.json"


@lru_cache(maxsize=1)
def _load_evidence():
    with (PROJECT_ROOT / "datasets" / "interaction_evidence.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _matching_rule(drug1, drug2):
    for rule in _load_evidence()["rules"]:
        left = {name.lower() for name in rule["left"]}
        right = {name.lower() for name in rule["right"]}
        if (drug1 in left and drug2 in right) or (drug2 in left and drug1 in right):
            return rule
    return None


def _rule_terms(name, rule):
    terms = {name}
    for side in ("left", "right"):
        if name in {item.lower() for item in rule[side]}:
            terms.update(item.lower() for item in rule.get(f"{side}_terms", []))
    for medicine, aliases in rule.get("terms_by_drug", {}).items():
        if medicine.lower() == name:
            terms.update(item.lower() for item in aliases)
    return terms


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
        raise RuntimeError("Interaction dataset is unavailable")

    # Handle root dataset column names (drug1, drug2)
    if "drug1" in dataframe.columns and "drug2" in dataframe.columns:
        dataframe["drug_1"] = dataframe["drug1"].astype(str)
        dataframe["drug_2"] = dataframe["drug2"].astype(str)

    if "drug_1" not in dataframe.columns or "drug_2" not in dataframe.columns:
        raise RuntimeError("Interaction dataset has no medicine columns")

    dataframe["drug_1"] = dataframe["drug_1"].astype(str)
    dataframe["drug_2"] = dataframe["drug_2"].astype(str)

    if "severity" not in dataframe.columns:
        dataframe["severity"] = "Unknown"
    else:
        dataframe["severity"] = dataframe["severity"].fillna("Unknown").astype(str)

    if "description" not in dataframe.columns:
        dataframe["description"] = "An interaction is recorded in the local dataset; a supporting clinical description is not provided."

    if "recommendation" not in dataframe.columns:
        dataframe["recommendation"] = "No source-backed management recommendation is available in this dataset."

    return dataframe


def get_interaction(drug1, drug2, lang: str = "en"):
    """Match exact names in either order and preserve conflicting source ratings."""
    if not drug1 or not drug2:
        return None

    dataframe = _load_interaction_table()
    if dataframe is None:
        raise RuntimeError("Interaction dataset is unavailable")

    normalized_drug1 = _normalize_drug_name(drug1)
    normalized_drug2 = _normalize_drug_name(drug2)

    if not normalized_drug1 or not normalized_drug2:
        return None

    drug_a = dataframe["drug_1"].str.lower().str.strip()
    drug_b = dataframe["drug_2"].str.lower().str.strip()

    forward_match = (drug_a == normalized_drug1) & (drug_b == normalized_drug2)
    reverse_match = (drug_a == normalized_drug2) & (drug_b == normalized_drug1)

    matches = dataframe[forward_match | reverse_match]
    rule = _matching_rule(normalized_drug1, normalized_drug2)
    match_basis = "Named medicine pair in the project dataset."
    if matches.empty and rule:
        terms1 = _rule_terms(normalized_drug1, rule)
        terms2 = _rule_terms(normalized_drug2, rule)
        matches = dataframe[(drug_a.isin(terms1) & drug_b.isin(terms2)) |
                            (drug_a.isin(terms2) & drug_b.isin(terms1))]
        match_basis = rule["basis"]

    if matches.empty and not rule:
        return None

    first_match = matches.iloc[0] if not matches.empty else {}
    severities = sorted({str(value).strip().capitalize() or "Unknown" for value in matches["severity"]})
    conflict = len(severities) > 1
    names = sorted((str(drug1).strip(), str(drug2).strip()), key=str.lower)
    if rule:
        canonical = {name.lower(): name for side in ("left", "right") for name in rule[side]}
        names = sorted((canonical[normalized_drug1], canonical[normalized_drug2]), key=str.lower)
    else:
        names = [str(first_match["drug_1"]), str(first_match["drug_2"])]
    result = {
        "drug1": names[0],
        "drug2": names[1],
        "severity": "Review required" if conflict or (rule and rule.get("review_note")) else (severities[0] if severities else "Not graded"),
        "source_severities": severities,
        "review_required": conflict or not severities or "Unknown" in severities or bool(rule and rule.get("review_note")),
        "source": "local_dataset",
        "source_rows": [int(index) + 2 for index in matches.index],
        "description": ("Source records disagree on severity: " + ", ".join(severities) + ". Clinical review is required before assigning a rating.") if conflict else str(first_match.get("description", "")),
        "recommendation": str(first_match.get("recommendation", "")),
        "match_basis": match_basis,
        "severity_basis": "Project dataset rating; prescribing labels do not assign this severity scale." if severities else "The prescribing label identifies a risk but does not assign a Mild, Moderate, or Severe rating.",
        "evidence_sources": [],
        "lang": lang,
    }
    if rule:
        result.update(description=rule["description"], recommendation=rule["recommendation"],
                      evidence_sources=rule["sources"], evidence_rule=rule["id"],
                      evidence_basis=rule["basis"], evidence_reviewed_on=_load_evidence()["reviewed_on"],
                      review_note=rule.get("review_note", "Source severity ratings disagree; clinical review is required." if conflict else ""))
    return result


def get_medicine_interactions(name, lang="en"):
    """Return all recorded partners, reconciling duplicate reverse rows."""
    table = _load_interaction_table()
    normalized = _normalize_drug_name(name)
    partners = set()
    for row in table.to_dict("records"):
        if _normalize_drug_name(row["drug_1"]) == normalized:
            partners.add(row["drug_2"])
        elif _normalize_drug_name(row["drug_2"]) == normalized:
            partners.add(row["drug_1"])
    for rule in _load_evidence()["rules"]:
        if normalized in {n.lower() for n in rule["left"]}:
            partners.update(rule["right"])
        if normalized in {n.lower() for n in rule["right"]}:
            partners.update(rule["left"])
    return [dict(get_interaction(name, partner, lang), drug_name=partner,
                 drug_id=_normalize_drug_name(partner).replace(" ", "-"))
            for partner in sorted(partners)]


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
    if any(item["review_required"] for item in interactions):
        max_sev = "Review required"

    return {
        "status": "success",
        "drugs_analyzed": clean_drugs,
        "total_interactions_found": len(interactions),
        "max_severity": max_sev,
        "interactions": interactions,
        "lang": lang,
    }
