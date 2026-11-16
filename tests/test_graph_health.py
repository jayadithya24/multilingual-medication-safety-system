import pytest
from backend.app.services import graph_health


@pytest.mark.parametrize('failure,expected', [(None, 'verified'), (RuntimeError('mismatch'), 'drift'), (OSError('offline'), 'unavailable')])
def test_graph_health_reports_drift_and_outage_without_mutations(monkeypatch, failure, expected):
    calls = []
    class Loader:
        @staticmethod
        def prepare_graph():
            return {'nodes': [], 'edges': []}
        def __init__(self, *args):
            pass
        def verify(self, graph):
            calls.append('verify')
            if failure:
                raise failure
            return {'verified': True, 'nodes': 0, 'relationships': 0}
        def close(self):
            calls.append('close')
    for key in ('NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD'):
        monkeypatch.setenv(key, 'test-only')
    monkeypatch.setattr(graph_health, 'Neo4jLoader', Loader)
    assert graph_health.check_graph()['status'] == expected
    assert calls == ['verify', 'close']
