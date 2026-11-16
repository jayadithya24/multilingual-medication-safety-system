"""Read-only periodic structural/severity verification of the reference graph."""
from datetime import datetime, timezone
import os
from neo4j.load_data import Neo4jLoader


def check_graph():
    loader = None
    result = {'checked_at': datetime.now(timezone.utc).isoformat()}
    try:
        from backend.app.services.interaction_service import _load_interaction_table, _load_evidence
        _load_interaction_table.cache_clear()
        _load_evidence.cache_clear()
        graph = Neo4jLoader.prepare_graph()
        loader = Neo4jLoader(os.environ['NEO4J_URI'], os.environ['NEO4J_USER'],
                            os.environ['NEO4J_PASSWORD'], os.getenv('NEO4J_DATABASE', 'neo4j'))
        result.update(loader.verify(graph), status='verified')
    except RuntimeError:
        result.update(status='drift', message='Graph differs from reference data. Run the explicit dataset/graph synchronization workflow.')
    except Exception:
        result.update(status='unavailable', message='Graph verification unavailable. Check the Neo4j instance and configuration.')
    finally:
        if loader:
            loader.close()
    return result
