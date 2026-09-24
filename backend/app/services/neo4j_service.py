import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from neo4j import GraphDatabase

from backend.app.services.medicine_service import _load_dataset, search_medicine


def _get_driver():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    if not password or password.lower() in {"password", "your_password", "your_neo4j_password", "changeme"}:
        raise RuntimeError("Set real NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD values before using Neo4j.")
    return GraphDatabase.driver(uri, auth=(user, password), connection_timeout=2,
                               connection_acquisition_timeout=3, max_transaction_retry_time=2)


def get_drug_interaction(drug1: str, drug2: str, lang: str = "en"):
    """Return the Neo4j interaction relationship for two drug names."""
    if not drug1 or not drug2:
        return None

    driver = _get_driver()
    try:
        query = """
        MATCH (d1:Drug)-[r:INTERACTS_WITH]-(d2:Drug)
        WHERE (
            toLower(coalesce(d1.drug_name, d1.name, d1.drug_id)) = toLower($drug1)
            AND toLower(coalesce(d2.drug_name, d2.name, d2.drug_id)) = toLower($drug2)
        ) OR (
            toLower(coalesce(d1.drug_name, d1.name, d1.drug_id)) = toLower($drug2)
            AND toLower(coalesce(d2.drug_name, d2.name, d2.drug_id)) = toLower($drug1)
        )
        RETURN
            coalesce(d1.drug_name, d1.name, d1.drug_id) AS drug1,
            coalesce(d2.drug_name, d2.name, d2.drug_id) AS drug2,
            r.severity AS severity,
            r.description AS description,
            r.disclaimer AS disclaimer
        LIMIT 1
        """

        with driver.session() as session:
            record = session.run(query, drug1=drug1.strip(), drug2=drug2.strip()).single()

        if not record:
            return None

        return {
            "drug1": record["drug1"],
            "drug2": record["drug2"],
            "severity": record["severity"] or "Unknown",
            "description": record["description"] or "",
            "recommendation": record["disclaimer"] or "Consult your doctor before acting on this information.",
            "lang": lang,
        }
    finally:
        driver.close()


def _serialize_drug(
    record: Any,
    lang: str = "en"
) -> Dict[str, Any]:
    drug = record["drug"]

    interactions = record.get("interactions", [])
    diseases = record.get("diseases", [])
    side_effects = record.get("side_effects", [])
        # Normalize language
    lang = (lang or "en").strip().lower()

    if lang in ("tlu", "te"):
        lang = "tulu"

    # Select language-specific medicine information
    if lang == "kn":

        description = (
            drug.get("description_kn")
            or drug.get("description_en")
            or drug.get("description")
        )

        warnings = (
            drug.get("warnings_kn")
            or drug.get("warnings_en")
            or drug.get("warnings")
        )

        contraindications = (
            drug.get("contraindications_kn")
            or drug.get("contraindications_en")
            or drug.get("contraindications")
        )

    elif lang == "tulu":

        description = (
            drug.get("description_tulu")
            or drug.get("description_tlu")
            or drug.get("description_en")
            or drug.get("description")
        )

        warnings = (
            drug.get("warnings_tulu")
            or drug.get("warnings_tlu")
            or drug.get("warnings_en")
            or drug.get("warnings")
        )

        contraindications = (
            drug.get("contraindications_tulu")
            or drug.get("contraindications_tlu")
            or drug.get("contraindications_en")
            or drug.get("contraindications")
        )

    else:

        description = (
            drug.get("description_en")
            or drug.get("description")
        )

        warnings = (
            drug.get("warnings_en")
            or drug.get("warnings")
        )

        contraindications = (
            drug.get("contraindications_en")
            or drug.get("contraindications")
        )

    # Convert Neo4j values safely
    if diseases is None:
        diseases = []

    if side_effects is None:
        side_effects = []

    return {
        "drug_id": drug.get("drug_id") or drug.get("id") or drug.get("name"),
        "drug_name": drug.get("drug_name") or drug.get("name"),
        "generic_name": drug.get("generic_name"),
        "drug_class": drug.get("drug_class"),

        "active_ingredient": (
            drug.get("active_ingredient")
            or drug.get("activeIngredient")
        ),

        # Normalized fields expected by MedicineCard.jsx
        "description": description,

"side_effects": (
    drug.get("side_effects")
    or drug.get("side_effects_en")
    or ", ".join(
        str(x) for x in side_effects
        if x
    ) or None
),

"contraindications": contraindications,

"warnings": warnings,

        "disease": (
            drug.get("disease")
            or ", ".join(
                str(x) for x in diseases
                if x
            ) or None
        ),

        "major_interactions": (
            drug.get("major_interactions")
            or ", ".join(
                f"{i.get('drug_name')}: {i.get('description')}"
                for i in interactions
                if i.get("drug_name")
            ) or None
        ),

        # Keep multilingual fields too
        "description_en": (
            drug.get("description_en")
            or drug.get("description")
        ),
        "description_kn": drug.get("description_kn"),
        "description_tulu": drug.get("description_tulu"),

        "warnings_en": (
            drug.get("warnings_en")
            or drug.get("warnings")
        ),
        "warnings_kn": drug.get("warnings_kn"),
        "warnings_tulu": drug.get("warnings_tulu"),

        "contraindications_en": (
            drug.get("contraindications_en")
            or drug.get("contraindications")
        ),
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
            if i and i.get("drug_name")
        ],
    }
def _fallback_search(
    query: str,
    limit: int,
    lang: str = "en"
) -> List[Dict[str, Any]]:
    dataframe = _load_dataset(lang)
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
        return [
    _serialize_drug(
        {
            "drug": fallback,
            "interactions": []
        },
        lang=lang
    )
] if fallback else []

    results: List[Dict[str, Any]] = []
    for _, row in matches.head(limit).iterrows():
        results.append(
    _serialize_drug(
        {
            "drug": row.to_dict(),
            "interactions": []
        },
        lang=lang
    )
)
    return results


def search_drug_by_text(
    query: str,
    limit: int = 15,
    lang: str = "en"
) -> List[Dict[str, Any]]:
    if not query:
        return []

    # Patient search uses the same complete, cached multilingual data as OCR.
    dataset_results = _fallback_search(query, limit, lang=lang)
    if dataset_results:
        return dataset_results
    driver = None
    try:
        driver = _get_driver()
        with driver.session() as session:
            cypher = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS toLower($search_term)
   OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($search_term)

OPTIONAL MATCH (d)-[:TREATS]->(disease:Disease)

OPTIONAL MATCH (d)-[:CAUSES]->(side:SideEffect)

OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)

RETURN
    d AS drug,

    collect(DISTINCT disease.name) AS diseases,

    collect(DISTINCT side.name) AS side_effects,

    collect(DISTINCT {
        drug_id: o.name,
        drug_name: o.name,
        severity: r.severity,
        description: r.description
    }) AS interactions

LIMIT $limit
"""
            records = session.run(cypher, search_term=query, limit=limit)
            if records:
                # Neo4j confirms that the medicine exists.
                # Return the complete medicine information
                # from the main dataset, which is also used by OCR.
                dataset_results = _fallback_search(
    query,
    limit,
    lang=lang
)

                if dataset_results:
                    return dataset_results

                # If the medicine is not available in the dataset,
                # use the Neo4j result as a fallback.
                return [_serialize_drug(record, lang=lang) for record in records]

    except Exception as err:
        print(f"Neo4j unavailable, falling back to CSV: {err}")
    finally:
        if driver:
            driver.close()

    return _fallback_search(
    query,
    limit,
    lang=lang
)

def get_drug_by_id(drug_id: str) -> Dict[str, Any]:
    try:
        driver = _get_driver()
        with driver.session() as session:
            cypher = """
            MATCH (d:Drug)
WHERE d.name = $drug_id
   OR d.drug_id = $drug_id
            OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)

RETURN
    d AS drug,
    collect({
        drug_id: o.name,
        drug_name: o.name,
        severity: r.severity,
        description: r.description
    }) AS interactions
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

def _fallback_local_knowledge_graph() -> Dict[str, List[Dict[str, Any]]]:
    """Return a medication graph built from the local CSV datasets when Neo4j is unavailable."""
    project_root = Path(__file__).resolve().parents[3]
    datasets_dir = project_root / "datasets"

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_nodes = set()
    seen_edges = set()

    def add_node(node_id: Any, name: Any, node_type: str, extra: Optional[Dict[str, Any]] = None) -> None:
        if node_id is None or node_id == "" or name is None:
            return
        key = str(node_id).strip()
        if not key:
            return
        if key in seen_nodes:
            return
        payload = {
            "id": key,
            "node_id": key,
            "name": str(name).strip(),
            "type": node_type,
        }
        if extra:
            payload.update(extra)
        nodes.append(payload)
        seen_nodes.add(key)

    def add_edge(source: Any, target: Any, relationship: str, edge_type: str, extra: Optional[Dict[str, Any]] = None) -> None:
        if source is None or target is None:
            return
        source_key = str(source).strip()
        target_key = str(target).strip()
        if not source_key or not target_key:
            return
        edge_key = (source_key, target_key, relationship)
        if edge_key in seen_edges:
            return
        payload = {
            "source": source_key,
            "target": target_key,
            "relationship": relationship,
            "type": edge_type,
        }
        if extra:
            payload.update(extra)
        edges.append(payload)
        seen_edges.add(edge_key)

    master_path = datasets_dir / "english_master_dataset.csv"
    if master_path.exists():
        master_df = pd.read_csv(master_path)
        for _, row in master_df.iterrows():
            drug_id = row.get("drug_id") or str(row.get("drug_name", "")).strip().lower().replace(" ", "-")
            drug_name = row.get("drug_name") or row.get("generic_name")
            if drug_id is None:
                continue
            add_node(drug_id, drug_name or drug_id, "drug", {
                "generic_name": row.get("generic_name"),
                "drug_class": row.get("drug_class"),
            })

    disease_path = datasets_dir / "drug_disease.csv"
    if disease_path.exists():
        disease_df = pd.read_csv(disease_path)
        for _, row in disease_df.iterrows():
            drug_id = row.get("drug_id")
            disease_id = row.get("disease_id") or row.get("disease")
            disease_name = row.get("disease") or row.get("disease_id")
            if drug_id is not None:
                add_node(drug_id, drug_id, "drug")
            if disease_id is not None:
                add_node(disease_id, disease_name or disease_id, "disease")
            if drug_id is not None and disease_id is not None:
                add_edge(drug_id, disease_id, "TREATS", "treats")

    side_effect_path = datasets_dir / "drug_sideeffects.csv"
    if side_effect_path.exists():
        side_df = pd.read_csv(side_effect_path)
        for _, row in side_df.iterrows():
            drug_id = row.get("drug_id")
            side_effect = row.get("side_effect")
            if drug_id is not None and side_effect is not None:
                side_effect_id = "sideeffect:" + str(side_effect).strip().casefold()
                add_node(side_effect_id, side_effect, "sideeffect")
                add_edge(drug_id, side_effect_id, "CAUSES", "causes")

    interaction_path = datasets_dir / "drug_interactions.csv"
    if interaction_path.exists():
        interaction_df = pd.read_csv(interaction_path)
        for _, row in interaction_df.iterrows():
            if str(row.get("drug2_in_scope", "")).strip().lower() != "yes":
                continue
            drug1 = row.get("drug1_id") or row.get("drug1")
            drug2 = row.get("drug2_id") or row.get("drug2")
            severity = row.get("severity")
            if drug1 is None or drug2 is None:
                continue
            add_node(drug1, drug1, "drug")
            add_node(drug2, drug2, "drug")
            add_edge(drug1, drug2, "INTERACTS_WITH", "interaction", {"severity": severity})

    return {"nodes": nodes, "edges": edges, "source": "local_csv"}


def get_diseases() -> List[str]:
    """
    Return the diseases available in the Neo4j knowledge graph or dataset.
    """
    try:
        driver = _get_driver()

        with driver.session() as session:
            cypher = """
            MATCH (d:Disease)
            RETURN DISTINCT d.name AS disease
            ORDER BY disease
            """

            records = session.run(cypher)

            return [
                record["disease"]
                for record in records
                if record["disease"]
            ]

    except Exception as err:
        print(f"Neo4j disease lookup unavailable, falling back to CSV: {err}")

    dataframe = _load_dataset("en")
    if dataframe is None or "disease" not in dataframe.columns:
        return []

    return sorted(
        {
            str(disease).strip()
            for disease in dataframe["disease"].dropna()
            if str(disease).strip()
        },
        key=str.lower,
    )


def get_drugs_for_disease(disease_name: str) -> List[Dict[str, Any]]:
    """
    Return drugs connected to a disease through the TREATS relationship.
    """

    if not disease_name:
        return []

    try:
        driver = _get_driver()

        with driver.session() as session:
            cypher = """
            MATCH (drug:Drug)-[:TREATS]->(d:Disease)
            WHERE toLower(d.name) = toLower($disease_name)

            RETURN
                drug.name AS drug_id,
                drug.name AS drug_name,
                drug.generic_name AS generic_name,
                drug.drug_class AS drug_class,
                drug.description AS description_en,
                drug.warnings AS warnings_en,
                drug.contraindications AS contraindications_en

            ORDER BY drug.name
            """

            records = session.run(
                cypher,
                disease_name=disease_name.strip()
            )

            return [dict(record) for record in records]

    except Exception as err:
        print(f"Neo4j disease-drug lookup unavailable, falling back to CSV: {err}")

    dataframe = _load_dataset("en")
    if dataframe is None or "disease" not in dataframe.columns:
        return []

    matches = dataframe[
        dataframe["disease"].astype(str).str.strip().str.casefold()
        == disease_name.strip().casefold()
    ]

    return [
        {
            "drug_id": row.get("drug_id") or row.get("drug_name"),
            "drug_name": row.get("drug_name"),
            "generic_name": row.get("generic_name"),
            "drug_class": row.get("drug_class"),
            "description_en": row.get("description_en") or row.get("description", ""),
            "warnings_en": row.get("warnings_en") or row.get("warnings", ""),
            "contraindications_en": row.get("contraindications_en") or row.get("contraindications", ""),
        }
        for _, row in matches.sort_values("drug_name").iterrows()
    ]

{
  "status": "success",
  "nodes": [
    {
      "id": "4:xxx",
      "node_id": "metformin",
      "name": "Metformin",
      "type": "drug",
      "generic_name": "Metformin",
      "drug_class": "..."
    },
    {
      "id": "4:yyy",
      "node_id": "Diabetes",
      "name": "Diabetes",
      "type": "disease"
    }
  ],
  "edges": [
    {
      "source": "metformin",
      "target": "topiramate",
      "type": "interaction",
      "relationship": "INTERACTS_WITH",
      "severity": "Moderate"
    },
    {
      "source": "metformin",
      "target": "Diabetes",
      "type": "treats",
      "relationship": "TREATS"
    }
  ]
}

def get_knowledge_graph() -> Dict[str, List[Dict[str, Any]]]:
    """
    Return the complete medication knowledge graph.

    Includes:
        Drug
        Disease
        SideEffect

    Relationships:
        INTERACTS_WITH
        TREATS
        CAUSES
    """

    try:
        driver = _get_driver()

        with driver.session() as session:

            cypher = """
            MATCH (n)
            WHERE n:Drug OR n:Disease OR n:SideEffect

            OPTIONAL MATCH (n)-[r]->(m)
            WHERE m:Drug OR m:Disease OR m:SideEffect

            WITH
                collect(DISTINCT {
                    id: elementId(n),
                    node_id: coalesce(n.id, n.name),
                    name: coalesce(n.name, n.drug_name, n.id),
                    type: CASE
                        WHEN n:Drug THEN "drug"
                        WHEN n:Disease THEN "disease"
                        WHEN n:SideEffect THEN "sideeffect"
                        ELSE "unknown"
                    END,
                    generic_name: n.generic_name,
                    drug_class: n.drug_class
                }) AS nodes,

                collect(DISTINCT CASE
                    WHEN r IS NOT NULL AND m IS NOT NULL THEN {
                        source: coalesce(n.id, n.name),
                        target: coalesce(m.id, m.name),
                        type: CASE
                            WHEN type(r) = "INTERACTS_WITH"
                                THEN "interaction"
                            WHEN type(r) = "TREATS"
                                THEN "treats"
                            WHEN type(r) = "CAUSES"
                                THEN "causes"
                            ELSE toLower(type(r))
                        END,
                        relationship: type(r),
                        severity: coalesce(r.severity, "")
                    }
                    ELSE NULL
                END) AS edges

            RETURN nodes, edges
            """

            record = session.run(cypher).single()

            if not record:
                return {
                    "nodes": [],
                    "edges": []
                }

            nodes = record["nodes"]

            edges = [
                edge
                for edge in record["edges"]
                if edge is not None
            ]

            return {
                "nodes": nodes,
                "edges": edges,
                "source": "neo4j",
            }

    except Exception as err:
        print(f"Neo4j graph unavailable, falling back to local CSV data: {err}")
        return _fallback_local_knowledge_graph()
    finally:
        if "driver" in locals():
            driver.close()



def get_related_graph(drug_names: List[str], pair_only: bool = False) -> Dict[str, Any]:
    """Keep only recorded, direct relationships to the selected medicines."""
    graph = get_knowledge_graph()
    nodes = graph["nodes"]
    names = {name.strip().casefold() for name in drug_names if name.strip()}
    def node_id(node):
        return str(node.get("node_id") or node.get("id") or node.get("name"))
    selected = [node for node in nodes if node.get("type") == "drug"
                and str(node.get("name", "")).casefold() in names]
    selected_ids = {node_id(node) for node in selected}
    allowed = {node_id(node) for node in nodes
               if not pair_only or node.get("type") != "drug" or node_id(node) in selected_ids}
    links = [link for link in graph.get("links", graph.get("edges", []))
             if (str(link["source"]) in selected_ids or str(link["target"]) in selected_ids)
             and str(link["source"]) in allowed and str(link["target"]) in allowed]
    connected = selected_ids | {str(link[key]) for link in links for key in ("source", "target")}
    return {"nodes": [node for node in nodes if node_id(node) in connected],
            "links": links, "selected_drugs": [node["name"] for node in selected],
            "source": graph.get("source", "unknown")}


def get_interaction_graph(drug1: str, drug2: str) -> Dict[str, Any]:
    return get_related_graph([drug1, drug2], pair_only=True)
