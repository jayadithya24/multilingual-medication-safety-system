import sys
import types
import mongomock
from pathlib import Path

from backend import mongo_loader


def test_insert_to_mongo_with_mongomock(monkeypatch):
    # Monkeypatch a fake pymongo module where MongoClient is mongomock's
    fake_pymongo = types.ModuleType("pymongo")
    client = mongomock.MongoClient()
    fake_pymongo.MongoClient = lambda *args, **kwargs: client
    monkeypatch.setitem(sys.modules, "pymongo", fake_pymongo)

    dfs = mongo_loader.load_csvs(Path(__file__).resolve().parent.parent)
    docs = mongo_loader.build_documents(dfs)

    # Now call insert_to_mongo which will pick up our fake pymongo
    mongo_loader.insert_to_mongo("mongodb://fake", "test_meds", docs)

    # Verify inserted counts in the fake DB
    db = client["test_meds"]
    for collection, documents in docs.items():
        assert db[collection].count_documents({}) == len(documents)
