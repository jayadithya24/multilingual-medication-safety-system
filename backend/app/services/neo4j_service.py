import os
from typing import Any, Dict, List

from neo4j import GraphDatabase

from backend.app.services.medicine_service import _load_dataset, search_medicine


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


def _fallback_search(query: str, limit: int) -> List[Dict[str, Any]]:
    dataframe = _load_dataset("en")
    if dataframe is None:
        return []

    normalized_query = str(query).strip().lower()
    if not normalized_query:
        return []

    search_columns = [
        column for column in ["drug_name", "generic_name", "active_ingredient"] if column in dataframe.columns
    ]
    if not search_columns:
        return []

    exact_mask = None
    partial_mask = None
    for column in search_columns:
        series = dataframe[column].astype(str).str.lower().str.strip()
        column_exact = series == normalized_query
        column_partial = series.str.contains(normalized_query, na=False, regex=False)
        exact_mask = column_exact if exact_mask is None else (exact_mask | column_exact)
        partial_mask = column_partial if partial_mask is None else (partial_mask | column_partial)

    if exact_mask is not None and exact_mask.any():
        matches = dataframe[exact_mask]
    else:
        matches = dataframe[partial_mask] if partial_mask is not None else dataframe.iloc[0:0]

    if matches.empty:
        fallback = search_medicine(query, lang="en")
        return [_serialize_drug({"drug": fallback, "interactions": []})] if fallback else []

    results: List[Dict[str, Any]] = []
    for _, row in matches.head(limit).iterrows():
        results.append(_serialize_drug({"drug": row.to_dict(), "interactions": []}))
    return results


def search_drug_by_text(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    if not query:
        return []

    try:
        driver = _get_driver()
        with driver.session() as session:
            cypher = """
            MATCH (d:Drug)
            WHERE toLower(d.drug_name) CONTAINS toLower($query)
               OR toLower(d.generic_name) CONTAINS toLower($query)
               OR toLower(d.active_ingredient) CONTAINS toLower($query)
            OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)
            RETURN d AS drug, collect({drug_id:o.drug_id, drug_name:o.drug_name, severity:r.severity, description:r.description}) AS interactions
            LIMIT $limit
            """
            records = session.run(cypher, query=query, limit=limit)
            results = [_serialize_drug(record) for record in records]
            if results:
                return results
    except Exception as err:
        print(f"Neo4j unavailable, falling back to CSV: {err}")

    return _fallback_search(query, limit)


def get_drug_by_id(drug_id: str) -> Dict[str, Any]:
    try:
        driver = _get_driver()
        with driver.session() as session:
            cypher = """
            MATCH (d:Drug {drug_id: $drug_id})
            OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)
            RETURN d AS drug, collect({drug_id:o.drug_id, drug_name:o.drug_name, severity:r.severity, description:r.description}) AS interactions
            """
            record = session.run(cypher, drug_id=drug_id).single()
            if record:
                return _serialize_drug(record)
    except Exception as err:
        print(f"Neo4j unavailable, falling back to CSV: {err}")

    fallback = search_medicine(drug_id, lang="en")
    if not fallback:
        return {}

    return {
        "drug_id": fallback.get("drug_id"),
        "drug_name": fallback.get("drug_name"),
        "generic_name": fallback.get("generic_name"),
        "drug_class": fallback.get("drug_class"),
        "active_ingredient": fallback.get("active_ingredient"),
        "description_en": fallback.get("description_en"),
        "description_kn": fallback.get("description_kn"),
        "description_tulu": fallback.get("description_tulu"),
        "warnings_en": fallback.get("warnings_en"),
        "warnings_kn": fallback.get("warnings_kn"),
        "warnings_tulu": fallback.get("warnings_tulu"),
        "contraindications_en": fallback.get("contraindications_en"),
        "contraindications_kn": fallback.get("contraindications_kn"),
        "contraindications_tulu": fallback.get("contraindications_tulu"),
        "interactions": [],
    }
