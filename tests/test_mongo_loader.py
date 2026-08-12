import os
from pathlib import Path

from backend import mongo_loader


def test_build_documents_counts():
    root = Path(__file__).resolve().parent.parent
    dfs = mongo_loader.load_csvs(root)
    docs = mongo_loader.build_documents(dfs)

    # Basic sanity checks
    assert "drugs" in docs and "diseases" in docs and "interactions" in docs
    eng = dfs["english"]
    assert len(docs["drugs"]) == len(eng)


def test_drug_ids_present():
    root = Path(__file__).resolve().parent.parent
    dfs = mongo_loader.load_csvs(root)
    docs = mongo_loader.build_documents(dfs)
    # ensure every drug document has a drug_id
    for d in docs["drugs"]:
        assert d.get("drug_id")
