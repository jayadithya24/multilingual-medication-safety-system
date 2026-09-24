import pytest
from fastapi import HTTPException
from backend.app.routes import neo4j
from backend.app.services.neo4j_service import _fallback_local_knowledge_graph


def unavailable(*args, **kwargs):
    raise RuntimeError("offline")


def test_graph_failure_does_not_invent_patients_or_relationships(monkeypatch):
    monkeypatch.setattr(neo4j, 'get_knowledge_graph', unavailable)
    with pytest.raises(HTTPException) as error:
        neo4j.knowledge_graph()
    assert error.value.status_code == 503


def test_pair_failure_does_not_invent_interaction(monkeypatch):
    monkeypatch.setattr(neo4j, 'get_interaction_graph', unavailable)
    with pytest.raises(HTTPException) as error:
        neo4j.interaction_graph('unknown-one', 'unknown-two')
    assert error.value.status_code == 503


def test_fallback_graph_uses_one_node_per_master_drug():
    graph = _fallback_local_knowledge_graph()
    drugs = [node for node in graph['nodes'] if node['type'] == 'drug']
    assert len(drugs) == 30
    ids = {node['id'] for node in graph['nodes']}
    assert all(edge['source'] in ids and edge['target'] in ids for edge in graph['edges'])
