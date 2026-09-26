from backend.app.services import neo4j_service as service


def test_reference_keeps_only_direct_neighbors(monkeypatch):
    graph = {"nodes": [
        {"id": "neo-a", "node_id": "a", "name": "Alpha", "type": "drug"},
        {"node_id": "b", "name": "Beta", "type": "drug"},
        {"node_id": "c", "name": "Gamma", "type": "drug"},
        {"node_id": "d", "name": "Condition", "type": "disease"},
    ], "edges": [
        {"source": "a", "target": "b", "relationship": "INTERACTS_WITH"},
        {"source": "a", "target": "d", "relationship": "TREATS"},
        {"source": "c", "target": "d", "relationship": "TREATS"},
    ]}
    monkeypatch.setattr(service, "get_knowledge_graph", lambda: graph)
    result = service.get_related_graph([" ALPHA "])
    assert {n["node_id"] for n in result["nodes"]} == {"a", "b", "d"}
    assert len(result["links"]) == 2
    assert service.get_related_graph(["unknown"])["nodes"] == []
    pair = service.get_interaction_graph("Alpha", "Gamma")
    assert {n["node_id"] for n in pair["nodes"]} == {"a", "c", "d"}
    assert all(l["relationship"] == "TREATS" for l in pair["links"])


def test_pair_graph_works_offline_without_inventing_edges(monkeypatch):
    def offline():
        raise RuntimeError("offline")
    monkeypatch.setattr(service, "_get_driver", offline)
    graph = service.get_interaction_graph("Celecoxib", "Metformin")
    assert {n["name"] for n in graph["nodes"] if n["type"] == "drug"} == {"Celecoxib", "Metformin"}
    ids = {n["node_id"] for n in graph["nodes"]}
    assert graph["links"]
    assert all(l["source"] in ids and l["target"] in ids for l in graph["links"])
    assert not any(l["relationship"] == "INTERACTS_WITH" for l in graph["links"])
    interacting = service.get_interaction_graph("Celecoxib", "Methotrexate")
    assert any(l["relationship"] == "INTERACTS_WITH" for l in interacting["links"])
    assert graph["source"] == "local_csv"


def test_side_effect_identity_does_not_merge_conditions_or_case_variants():
    graph = service._fallback_local_knowledge_graph()
    effects = [n for n in graph["nodes"] if n["type"] == "sideeffect"]
    assert len({n["name"].casefold() for n in effects}) == len(effects)
    hypertension = [n for n in graph["nodes"] if n["name"].casefold() == "hypertension"]
    assert {n["type"] for n in hypertension} == {"disease", "sideeffect"}
    assert len({n["id"] for n in hypertension}) == 2
