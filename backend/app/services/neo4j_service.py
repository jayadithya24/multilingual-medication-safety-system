import os
from typing import Any, Dict, List

from neo4j import GraphDatabase


def _get_driver():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def _serialize_drug(record: Any) -> Dict[str, Any]:
    drug = record["drug"]
    interactions = record.get("interactions", [])
    return {
        "drug_id": drug.get("drug_id"),
        "drug_name": drug.get("drug_name"),
        "generic_name": drug.get("generic_name"),
        "drug_class": drug.get("drug_class"),
        "active_ingredient": drug.get("active_ingredient"),
        "description_en": drug.get("description_en"),
        "description_kn": drug.get("description_kn"),
        "description_tulu": drug.get("description_tulu"),
        "warnings_en": drug.get("warnings_en"),
        "warnings_kn": drug.get("warnings_kn"),
        "warnings_tulu": drug.get("warnings_tulu"),
        "contraindications_en": drug.get("contraindications_en"),
        "contraindications_kn": drug.get("contraindications_kn"),
        "contraindications_tulu": drug.get("contraindications_tulu"),
        "interactions": [
            {
                "drug_id": i.get("drug_id"),
                "drug_name": i.get("drug_name"),
                "severity": i.get("severity"),
                "description": i.get("description"),
            }
            for i in interactions
        ],
    }


def search_drug_by_text(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    if not query:
        return []

    driver = _get_driver()
    with driver.session() as session:
        cypher = """
        MATCH (d:Drug)
        WHERE toLower(d.drug_name) CONTAINS toLower($query)
           OR toLower(d.generic_name) CONTAINS toLower($query)
        OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)
        RETURN d AS drug, collect({drug_id:o.drug_id, drug_name:o.drug_name, severity:r.severity, description:r.description}) AS interactions
        LIMIT $limit
        """
        records = session.run(cypher, query=query, limit=limit)
        return [_serialize_drug(record) for record in records]


def get_drug_by_id(drug_id: str) -> Dict[str, Any]:
    driver = _get_driver()
    with driver.session() as session:
        cypher = """
        MATCH (d:Drug {drug_id: $drug_id})
        OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)
        RETURN d AS drug, collect({drug_id:o.drug_id, drug_name:o.drug_name, severity:r.severity, description:r.description}) AS interactions
        """
        record = session.run(cypher, drug_id=drug_id).single()
        if not record:
            return {}
        return _serialize_drug(record)
