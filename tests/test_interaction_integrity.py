import pytest
from backend.app.services import interaction_service as service
from backend.app.services.neo4j_service import _fallback_local_knowledge_graph
from neo4j.load_data import Neo4jLoader


def test_conflicting_ratings_are_order_independent():
    forward = service.get_interaction("Ibuprofen", "Methotrexate")
    reverse = service.get_interaction("Methotrexate", "Ibuprofen")
    assert forward == reverse
    assert forward["severity"] == "Review required"
    assert forward["source_severities"] == ["Moderate", "Severe"]
    assert len(forward["source_rows"]) == 2
    assert service.get_multi_drug_interactions(["Ibuprofen", "Methotrexate"])["max_severity"] == "Review required"


def test_partial_names_do_not_match():
    assert service.get_interaction("ibu", "methotrexate") is None


def test_reference_lists_recorded_interactions():
    from backend.app.services.neo4j_service import search_drug_by_text
    result = search_drug_by_text("Celecoxib")[0]
    assert {i["drug_name"] for i in result["interactions"]} >= {"Methotrexate", "Warfarin"}


def test_unavailable_data_is_not_a_negative_result(monkeypatch):
    monkeypatch.setattr(service, "_load_interaction_table", lambda: None)
    with pytest.raises(RuntimeError):
        service.get_interaction("Ibuprofen", "Methotrexate")


def test_graph_has_one_edge_per_unordered_interaction():
    graph = _fallback_local_knowledge_graph()
    edges = [e for e in graph["edges"] if e["relationship"] == "INTERACTS_WITH"]
    assert len(edges) == len({tuple(sorted((e["source"], e["target"]))) for e in edges}) == 8
    conflict = next(e for e in edges if {e["source"], e["target"]} == {"ibuprofen", "methotrexate"})
    assert conflict["severity"] == "Review required"


def test_import_preserves_multilingual_fields_and_endpoints():
    graph = Neo4jLoader.prepare_graph()
    nodes = {n["node_id"]: n for n in graph["nodes"]}
    for lang in ("en", "kn", "tulu"):
        assert nodes["metformin"][f"description_{lang}"]
    assert all(e["source"] in nodes and e["target"] in nodes for e in graph["edges"])
    assert nodes["sideeffect:hypertension"]["type"] == "sideeffect"
    assert nodes["hypertension"]["type"] == "disease"
