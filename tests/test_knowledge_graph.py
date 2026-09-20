import os

from backend.app.services.neo4j_service import get_knowledge_graph


def test_get_knowledge_graph_falls_back_to_local_dataset(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "your_password")

    graph = get_knowledge_graph()

    assert graph["nodes"]
    assert graph["edges"]
    assert any(node["type"] == "drug" for node in graph["nodes"])
    assert any(edge["relationship"] == "TREATS" for edge in graph["edges"])
