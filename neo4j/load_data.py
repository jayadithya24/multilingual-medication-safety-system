"""Import and verify the application's graph. Use --apply to write to Neo4j."""
import argparse
import csv
import json
import os
from pathlib import Path
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
LABELS = {"drug": "Drug", "disease": "Disease", "sideeffect": "SideEffect"}


class Neo4jLoader:
    @staticmethod
    def resolve_drug_id(row):
        if row.get("drug_id"):
            return str(row["drug_id"]).strip()
        return str(row.get("drug_name") or row.get("Drug Name") or "").strip().lower().replace(" ", "-")

    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=5)
        self.database = database

    def close(self):
        self.driver.close()

    @staticmethod
    def prepare_graph():
        from backend.app.services.neo4j_service import _fallback_local_knowledge_graph
        graph = _fallback_local_knowledge_graph()
        nodes = {n["node_id"]: n for n in graph["nodes"]}
        for language, filename in (("en", "english"), ("kn", "kannada"), ("tulu", "tulu")):
            with (ROOT / "datasets" / f"{filename}_master_dataset.csv").open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    node = nodes[Neo4jLoader.resolve_drug_id(row)]
                    if language == "en":
                        node.update(row)
                        node["drug_id"] = node["node_id"]
                    for field in ("description", "warnings", "contraindications", "side_effects", "major_interactions"):
                        node[f"{field}_{language}"] = row.get(f"{field}_{language}") or row.get(field, "")
        for node in nodes.values():
            if node["type"] == "disease":
                node.update(disease_id=node["node_id"], disease_name=node["name"])
        if any(e["source"] not in nodes or e["target"] not in nodes for e in graph["edges"]):
            raise ValueError("Dataset contains missing relationship endpoints")
        return graph

    def create_constraints_and_indexes(self):
        schema = (Path(__file__).parent / "schema.cypher").read_text(encoding="utf-8")
        with self.driver.session(database=self.database) as session:
            for statement in schema.split(";"):
                if statement.strip():
                    session.run(statement).consume()

    @staticmethod
    def _import(tx, graph):
        nodes = {n["node_id"]: n for n in graph["nodes"]}
        for label in LABELS.values():
            rows = [dict(n, id=n["node_id"]) for n in nodes.values() if LABELS[n["type"]] == label]
            tx.run(f"UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) SET n += row", rows=rows).consume()
        for edge in graph["edges"]:
            source_label = LABELS[nodes[edge["source"]]["type"]]
            target_label = LABELS[nodes[edge["target"]]["type"]]
            relationship = edge["relationship"]
            if relationship not in {"TREATS", "CAUSES", "INTERACTS_WITH"}:
                raise ValueError("Unsupported relationship")
            properties = {k: v for k, v in edge.items() if k not in {"source", "target", "relationship", "type"}}
            tx.run(f"MATCH (a:{source_label} {{id: $source}}), (b:{target_label} {{id: $target}}) "
                   f"MERGE (a)-[r:{relationship}]->(b) SET r += $properties",
                   source=edge["source"], target=edge["target"], properties=properties).consume()

    def verify(self, graph):
        with self.driver.session(database=self.database) as session:
            nodes = list(session.run("MATCH (n) WHERE n:Drug OR n:Disease OR n:SideEffect RETURN n.type AS kind, n.id AS id"))
            rows = list(session.run("MATCH (a)-[r:TREATS|CAUSES|INTERACTS_WITH]->(b) "
                                    "RETURN a.id AS source, b.id AS target, type(r) AS relationship, r.severity AS severity"))
        expected_nodes = {(n["type"], n["node_id"]) for n in graph["nodes"]}
        expected_edges = {(e["source"], e["target"], e["relationship"], e.get("severity")) for e in graph["edges"]}
        actual_nodes = {(n["kind"], n["id"]) for n in nodes}
        actual_edges = {(r["source"], r["target"], r["relationship"], r["severity"]) for r in rows}
        if actual_nodes != expected_nodes or actual_edges != expected_edges or len(rows) != len(expected_edges) or len(nodes) != len(expected_nodes):
            raise RuntimeError("Live graph differs from the dataset. Inspect existing records; no data was deleted.")
        return {"nodes": len(nodes), "relationships": len(rows), "verified": True}

    def run_full_pipeline(self):
        graph = self.prepare_graph()
        self.driver.verify_connectivity()
        self.create_constraints_and_indexes()
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._import, graph)
        return self.verify(graph)


def main():
    from backend.env_loader import load_project_env
    load_project_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    graph = Neo4jLoader.prepare_graph()
    if not args.apply:
        print(json.dumps({"nodes": len(graph["nodes"]), "relationships": len(graph["edges"]), "dry_run": True}))
        return
    loader = Neo4jLoader(os.environ["NEO4J_URI"], os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"], os.getenv("NEO4J_DATABASE", "neo4j"))
    try:
        print(json.dumps(loader.run_full_pipeline()))
    finally:
        loader.close()


if __name__ == "__main__":
    main()
