"""Read-only Neo4j and local graph audit; never imports or deletes graph data."""
import json
import sys
import os
import socket
import argparse
import urllib.request
from urllib.parse import urlsplit
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Save the read-only audit as JSON')
    args = parser.parse_args()
    import pandas as pd
    from backend.env_loader import load_project_env
    load_project_env()
    from backend.app.services.neo4j_service import _get_driver, _fallback_local_knowledge_graph
    report = {}
    endpoint = urlsplit(os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687'))
    report['configured_connection'] = {
        'scheme': endpoint.scheme, 'host': endpoint.hostname,
        'port': endpoint.port or 7687,
        'local': endpoint.hostname in {'localhost', '127.0.0.1', '::1'},
    }
    report['local_ports'] = {}
    for port in (7474, 7687):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=2):
                report['local_ports'][str(port)] = 'accepting connections'
        except OSError:
            report['local_ports'][str(port)] = 'not reachable'
    for filename in ('english_master_dataset', 'drug_disease', 'drug_sideeffects', 'drug_interactions'):
        frame = pd.read_csv(ROOT / 'datasets' / f'{filename}.csv').fillna('')
        report[filename] = {'rows': len(frame), 'columns': list(frame.columns)}
    frame = pd.read_csv(ROOT / 'datasets/drug_interactions.csv').fillna('')
    pairs = defaultdict(set)
    counts = Counter()
    for row in frame.to_dict('records'):
        pair = tuple(sorted((row['drug1_id'], row['drug2_id'])))
        pairs[pair].add(row['severity'])
        counts[pair] += 1
    report['interaction_audit'] = {
        'unique_pairs': len(pairs),
        'in_scope_rows': int(frame.drug2_in_scope.eq('yes').sum()),
        'duplicate_pairs': sum(count > 1 for count in counts.values()),
        'conflicting_severities': [{'pair': pair, 'severities': sorted(values)} for pair, values in pairs.items() if len(values) > 1],
    }
    graph = _fallback_local_knowledge_graph()
    ids = {node['id'] for node in graph['nodes']}
    report['fallback_graph'] = {
        'node_types': dict(Counter(n['type'] for n in graph['nodes'])),
        'edge_types': dict(Counter(e['relationship'] for e in graph['edges'])),
        'dangling_edges': sum(e['source'] not in ids or e['target'] not in ids for e in graph['edges']),
    }
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/neo4j/graph', timeout=15) as response:
            api_graph = json.load(response)
        canonical = lambda rows: sorted(json.dumps(row, sort_keys=True) for row in rows)
        report['running_backend_graph'] = {
            'source': api_graph.get('source', 'unknown'),
            'nodes': len(api_graph.get('nodes', [])),
            'relationships': len(api_graph.get('links', [])),
            'exactly_matches_csv_fallback': canonical(api_graph.get('nodes', [])) == canonical(graph['nodes'])
                and canonical(api_graph.get('links', [])) == canonical(graph['edges']),
        }
    except Exception as error:
        report['running_backend_graph'] = {'error_type': type(error).__name__}
    # IDs reused across entity types can silently merge a condition and a side effect.
    diseases = pd.read_csv(ROOT / 'datasets/drug_disease.csv').fillna('')
    effects = pd.read_csv(ROOT / 'datasets/drug_sideeffects.csv').fillna('')
    disease_ids = set(diseases.disease_id.astype(str).str.strip())
    effect_names = set(effects.side_effect.astype(str).str.strip())
    report['identity_audit'] = {
        'condition_side_effect_id_collisions': sorted(disease_ids & effect_names),
        'side_effect_case_variants': [sorted(values) for values in (
            {name for name in effect_names if name.casefold() == key}
            for key in sorted({name.casefold() for name in effect_names})
        ) if len(values) > 1],
    }
    report['celecoxib_source_records'] = {
        'conditions': diseases[diseases.drug_id.eq('celecoxib')].to_dict('records'),
        'side_effects': effects[effects.drug_id.eq('celecoxib')].side_effect.tolist(),
        'interactions': frame[frame.drug1_id.eq('celecoxib') | frame.drug2_id.eq('celecoxib')].to_dict('records'),
    }
    try:
        with _get_driver() as driver:
            driver.verify_connectivity()
            with driver.session(default_access_mode='READ') as session:
                report['live_graph'] = {
                    'nodes': session.run('MATCH (n) RETURN count(n) AS total').single()['total'],
                    'relationships': session.run('MATCH ()-[r]->() RETURN count(r) AS total').single()['total'],
                    'interaction_properties': session.run('MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS total, count(r.severity) AS with_severity, count(r.description) AS with_description').single().data(),
                }
    except Exception as error:
        report['live_graph'] = {'available': False, 'error_type': type(error).__name__}
    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    if args.output:
        args.output.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)


if __name__ == '__main__':
    main()
