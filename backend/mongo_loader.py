from pathlib import Path
import re
import os
from typing import Dict, Any, List

import pandas as pd


def _slugify(text: str) -> str:
    text = str(text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"(^-|-$)", "", text)
    return text or None


def load_csvs(root: Path = None) -> Dict[str, pd.DataFrame]:
    root = Path(root or Path(__file__).parent.parent)
    ds = Path(root) / "datasets"
    return {
        "english": pd.read_csv(ds / "english_master_dataset.csv"),
        "kannada": pd.read_csv(ds / "kannada_master_dataset.csv"),
        "tulu": pd.read_csv(ds / "tulu_master_dataset.csv"),
        "disease": pd.read_csv(ds / "drug_disease.csv"),
        "side": pd.read_csv(ds / "drug_sideeffects.csv"),
        "interactions": pd.read_csv(ds / "drug_interactions.csv"),
    }


def build_documents(dfs: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict[str, Any]]]:
    eng = dfs["english"].fillna("")
    kn = dfs["kannada"].fillna("")
    tu = dfs["tulu"].fillna("")
    disease = dfs["disease"].fillna("")
    side = dfs["side"].fillna("")
    inter = dfs["interactions"].fillna("")

    # Normalize ids in language files
    if "drug_id" in kn.columns:
        kn["drug_id"] = kn["drug_id"].astype(str).str.strip().str.lower()
    if "drug_id" in tu.columns:
        tu["drug_id"] = tu["drug_id"].astype(str).str.strip().str.lower()

    name_to_id = dict(zip(kn["drug_name"].astype(str).str.strip(), kn.get("drug_id", kn["drug_name"]).astype(str)))

    drugs = []
    for _, row in eng.iterrows():
        name = str(row.get("drug_name", "")).strip()
        drug_id = name_to_id.get(name) or _slugify(name)
        doc = {
            "drug_id": drug_id,
            "drug_name": name,
            "generic_name": row.get("generic_name", ""),
            "disease": row.get("disease", ""),
            "drug_class": row.get("drug_class", ""),
            "active_ingredient": row.get("active_ingredient", ""),
            "description": row.get("description", ""),
            "side_effects": row.get("side_effects", ""),
            "contraindications": row.get("contraindications", ""),
            "warnings": row.get("warnings", ""),
            "major_interactions": row.get("major_interactions", ""),
            "source": row.get("source", ""),
            "translations": {
                "english": {"drug_name": name},
                "kannada": {},
                "tulu": {},
            },
        }
        # attempt to pull translations
        kn_row = kn[kn["drug_name"].astype(str).str.strip() == name]
        if not kn_row.empty:
            kr = kn_row.iloc[0]
            doc["translations"]["kannada"] = {"drug_id": str(kr.get("drug_id", "")), "drug_name": kr.get("drug_name", "")}
        tu_row = tu[tu["drug_name"].astype(str).str.strip() == name]
        if not tu_row.empty:
            tr = tu_row.iloc[0]
            doc["translations"]["tulu"] = {"drug_id": str(tr.get("drug_id", "")), "drug_name": tr.get("drug_name", "")}

        drugs.append(doc)

    # disease docs
    diseases = []
    for _, row in disease.iterrows():
        diseases.append({"drug_id": str(row.get("drug_id", "")).strip().lower(), "disease": row.get("disease", "")})

    side_effects = [
        {"drug_id": str(r.get("drug_id", "")).strip().lower(), "side_effect": r.get("side_effect", "")}
        for _, r in side.iterrows()
    ]

    interactions = [
        {
            "drug1_id": str(r.get("drug1_id", "")).strip().lower(),
            "drug2_id": str(r.get("drug2_id", "")).strip().lower(),
            "severity": r.get("severity", ""),
            "drug2_in_scope": str(r.get("drug2_in_scope", "")).strip().lower(),
            "notes": r.get("notes", ""),
        }
        for _, r in inter.iterrows()
    ]

    return {
        "drugs": drugs,
        "diseases": diseases,
        "side_effects": side_effects,
        "interactions": interactions,
    }


def insert_to_mongo(uri: str, db_name: str, documents: Dict[str, List[Dict[str, Any]]]) -> None:
    try:
        from pymongo import MongoClient
    except Exception:
        raise RuntimeError("pymongo is required to insert documents to MongoDB. Install backend/requirements.txt and try again.")

    client = MongoClient(uri)
    db = client[db_name]

    # Insert or replace collections
    for coll_name, docs in documents.items():
        if not docs:
            continue
        col = db[coll_name]
        # replace collection with new data for initial load
        col.delete_many({})
        col.insert_many(docs)


if __name__ == "__main__":
    # Allow running as a simple loader script when MONGO_URI and MONGO_DB are set
    dfs = load_csvs()
    docs = build_documents(dfs)
    mongo_uri = os.environ.get("MONGO_URI")
    mongo_db = os.environ.get("MONGO_DB", "meds")
    if mongo_uri:
        print("Inserting documents to MongoDB", mongo_db)
        insert_to_mongo(mongo_uri, mongo_db, docs)
    else:
        print("Built documents summary:")
        print({k: len(v) for k, v in docs.items()})
