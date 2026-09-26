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
    assert len(edges) == len({tuple(sorted((e["source"], e["target"]))) for e in edges}) == 27
    conflict = next(e for e in edges if {e["source"], e["target"]} == {"ibuprofen", "methotrexate"})
    assert conflict["severity"] == "Review required"
    glucose = next(e for e in edges if {e["source"], e["target"]} == {"acarbose", "chlorthalidone"})
    assert glucose["severity"] == "Not graded"
    assert glucose["evidence_urls"]


def test_label_only_risk_is_not_given_an_invented_severity():
    result = service.get_interaction("Acarbose", "Chlorthalidone")
    assert result == service.get_interaction("chlorthalidone", " ACARBOSE ")
    assert result["severity"] == "Not graded"
    assert result["review_required"]
    assert result["source_severities"] == []
    assert "blood glucose" in result["description"]
    assert len(result["evidence_sources"]) == 2


@pytest.mark.parametrize("first,second", [("Ibuprofen", "Losartan"), ("Diclofenac", "Enalapril"), ("Celecoxib", "Telmisartan")])
def test_explicit_class_mapping_preserves_provenance(first, second):
    result = service.get_interaction(first, second)
    assert result == service.get_interaction(second, first)
    assert result["severity"] == "Moderate"
    assert result["source_rows"] and result["evidence_sources"]
    assert set((result["drug1"], result["drug2"])) == {first, second}
    assert "Kidney" in result["description"]


def test_no_inference_from_unmapped_classes_or_shared_disease():
    assert service.get_interaction("Acarbose", "Metformin") is None
    assert service.get_interaction("Diclofenac", "Amlodipine") is None
    assert service.get_interaction("Ibu", "Losartan") is None


def test_label_warning_flags_legacy_mild_rating_for_review():
    result = service.get_interaction("Telmisartan", "Ramipril")
    assert result["severity"] == "Review required"
    assert result["source_severities"] == ["Mild"]
    assert result["review_note"]


def test_live_graph_result_does_not_discard_evidence(monkeypatch):
    import asyncio
    from backend.app.routes import interaction
    monkeypatch.setattr(interaction, "get_drug_interaction", lambda *args, **kwargs: {"severity": "Moderate"})
    result = asyncio.run(interaction.check_interaction("Naproxen", "Methotrexate", "en"))["interaction"]
    assert result["source"] == "neo4j"
    assert result["evidence_sources"]
    assert "toxicity" in result["description"]


def test_ungraded_risk_is_not_reported_as_no_interaction_in_multi_check():
    result = service.get_multi_drug_interactions(["Acarbose", "Chlorthalidone"])
    assert result["total_interactions_found"] == 1
    assert result["max_severity"] == "Review required"


def test_import_preserves_multilingual_fields_and_endpoints():
    graph = Neo4jLoader.prepare_graph()
    nodes = {n["node_id"]: n for n in graph["nodes"]}
    for lang in ("en", "kn", "tulu"):
        assert nodes["metformin"][f"description_{lang}"]
    assert all(e["source"] in nodes and e["target"] in nodes for e in graph["edges"])
    assert nodes["sideeffect:hypertension"]["type"] == "sideeffect"
    assert nodes["hypertension"]["type"] == "disease"
