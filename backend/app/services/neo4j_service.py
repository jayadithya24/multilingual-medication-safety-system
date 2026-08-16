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
        "drug_id": drug.get("drug_id") or drug.get("id") or drug.get("name"),
        "drug_name": drug.get("drug_name") or drug.get("name"),
        "generic_name": drug.get("generic_name"),
        "drug_class": drug.get("drug_class"),
        "active_ingredient": drug.get("active_ingredient"),
        "description_en": drug.get("description_en") or drug.get("description"),
        "description_kn": drug.get("description_kn"),
        "description_tulu": drug.get("description_tulu"),
        "warnings_en": drug.get("warnings_en") or drug.get("warnings"),
        "warnings_kn": drug.get("warnings_kn"),
        "warnings_tulu": drug.get("warnings_tulu"),
        "contraindications_en": drug.get("contraindications_en") or drug.get("contraindications"),
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
            if i.get("drug_name")
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
WHERE toLower(d.name) CONTAINS toLower($query)
   OR toLower(coalesce(d.generic_name, "")) CONTAINS toLower($query)
   OR toLower(coalesce(d.active_ingredient, "")) CONTAINS toLower($query)

OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->(o:Drug)

RETURN
    d AS drug,
    collect({
        drug_id: o.name,
        drug_name: o.name,
        severity: r.severity,
        description: r.description
    }) AS interactions

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

def get_diseases() -> List[str]:
    """
    Return the diseases available in the Neo4j knowledge graph.
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
        print(f"Neo4j disease lookup unavailable: {err}")
        raise


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
        print(f"Neo4j disease-drug lookup unavailable: {err}")

    return []

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

    driver = _get_driver()

    try:
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
                "edges": edges
            }

    finally:
        driver.close()



def get_interaction_graph(
    drug1: str,
    drug2: str
) -> Dict[str, Any]:

    if not drug1 or not drug2:
        return {
            "status": "success",
            "nodes": [],
            "links": [],
            "disease": None,
            "selected_drugs": []
        }

    driver = _get_driver()

    try:
        with driver.session() as session:

            # =====================================================
            # 1. Find ONLY the two selected medicines
            # =====================================================

            selected_query = """
            MATCH (d1:Drug), (d2:Drug)

            WHERE toLower(d1.name) = toLower($drug1)
              AND toLower(d2.name) = toLower($drug2)

            RETURN d1, d2
            """

            selected = session.run(
                selected_query,
                drug1=drug1.strip(),
                drug2=drug2.strip()
            ).single()

            if not selected:
                return {
                    "status": "success",
                    "nodes": [],
                    "links": [],
                    "disease": None,
                    "selected_drugs": []
                }

            d1 = selected["d1"]
            d2 = selected["d2"]

            selected_drug_names = [
                d1["name"],
                d2["name"]
            ]


            # =====================================================
            # 2. Prepare nodes and links
            # =====================================================

            nodes = []
            links = []
            node_ids = set()


            def add_drug_node(drug):

                if not drug:
                    return

                node_id = str(
                    drug.get("name") or
                    drug.get("drug_id") or
                    drug.get("id")
                ).strip()

                if not node_id:
                    return

                if node_id in node_ids:
                    return

                nodes.append({
                    "id": node_id,
                    "node_id": node_id,
                    "name": drug.get("name") or node_id,
                    "type": "drug",
                    "generic_name": drug.get("generic_name"),
                    "drug_class": drug.get("drug_class")
                })

                node_ids.add(node_id)


            def add_disease_node(disease):

                if not disease:
                    return

                node_id = str(
                    disease.get("name") or
                    disease.get("id")
                ).strip()

                if not node_id:
                    return

                if node_id in node_ids:
                    return

                nodes.append({
                    "id": node_id,
                    "node_id": node_id,
                    "name": disease.get("name") or node_id,
                    "type": "disease"
                })

                node_ids.add(node_id)


            def add_side_effect_node(side_effect):

                if not side_effect:
                    return

                node_id = str(
                    side_effect.get("name") or
                    side_effect.get("id")
                ).strip()

                if not node_id:
                    return

                if node_id in node_ids:
                    return

                nodes.append({
                    "id": node_id,
                    "node_id": node_id,
                    "name": side_effect.get("name") or node_id,
                    "type": "sideeffect"
                })

                node_ids.add(node_id)


            # =====================================================
            # 3. Add ONLY the two selected drug nodes
            # =====================================================

            add_drug_node(d1)
            add_drug_node(d2)


            # =====================================================
            # 4. Find diseases connected ONLY to these two drugs
            #
            # Methotrexate ── TREATS ──> Arthritis
            # Ibuprofen    ── TREATS ──> Arthritis
            #
            # We do NOT fetch other drugs.
            # =====================================================

            disease_query = """
            MATCH (drug:Drug)-[:TREATS]->(d:Disease)

            WHERE toLower(drug.name) IN [
                toLower($drug1),
                toLower($drug2)
            ]

            RETURN DISTINCT
                drug.name AS drug_name,
                d AS disease

            ORDER BY d.name
            """

            disease_records = session.run(
                disease_query,
                drug1=drug1.strip(),
                drug2=drug2.strip()
            )


            diseases = []

            for record in disease_records:

                drug_name = record["drug_name"]
                disease = record["disease"]

                if not disease:
                    continue

                disease_name = disease.get("name")

                if not disease_name:
                    continue

                # Add disease node
                add_disease_node(disease)

                # Add relationship:
                #
                # Drug ── TREATS ──> Disease
                #
                links.append({
                    "source": drug_name,
                    "target": disease_name,
                    "relationship": "TREATS",
                    "type": "treats"
                })

                diseases.append(disease_name)


            # =====================================================
            # 5. Find side effects ONLY for the two selected drugs
            #
            # IMPORTANT:
            # We are NOT finding side effects for every medicine
            # associated with the disease.
            # =====================================================

            side_effect_query = """
            MATCH (drug:Drug)-[:CAUSES]->(side:SideEffect)

            WHERE toLower(drug.name) IN [
                toLower($drug1),
                toLower($drug2)
            ]

            RETURN DISTINCT
                drug.name AS drug_name,
                side AS side_effect

            ORDER BY drug_name, side_effect.name
            """

            side_effect_records = session.run(
                side_effect_query,
                drug1=drug1.strip(),
                drug2=drug2.strip()
            )


            for record in side_effect_records:

                drug_name = record["drug_name"]
                side_effect = record["side_effect"]

                if not drug_name or not side_effect:
                    continue

                side_effect_name = (
                    side_effect.get("name")
                    or side_effect.get("id")
                )

                if not side_effect_name:
                    continue


                # Add side effect node
                add_side_effect_node(side_effect)


                # Add CAUSES relationship
                links.append({
                    "source": drug_name,
                    "target": side_effect_name,
                    "relationship": "CAUSES",
                    "type": "causes"
                })


            # =====================================================
            # 6. Find interaction ONLY between the two selected
            # medicines
            #
            # Methotrexate ── INTERACTS_WITH ── Ibuprofen
            # =====================================================

            interaction_query = """
            MATCH (d1:Drug)-[r:INTERACTS_WITH]-(d2:Drug)

            WHERE (
                    toLower(d1.name) = toLower($drug1)
                    AND
                    toLower(d2.name) = toLower($drug2)
                  )
               OR (
                    toLower(d1.name) = toLower($drug2)
                    AND
                    toLower(d2.name) = toLower($drug1)
                  )

            RETURN DISTINCT
                d1.name AS source,
                d2.name AS target,
                r.severity AS severity,
                r.description AS description
            """

            interaction_records = session.run(
                interaction_query,
                drug1=drug1.strip(),
                drug2=drug2.strip()
            )


            for record in interaction_records:

                source = record["source"]
                target = record["target"]

                if not source or not target:
                    continue

                links.append({
                    "source": source,
                    "target": target,
                    "relationship": "INTERACTS_WITH",
                    "type": "interaction",
                    "severity": record["severity"],
                    "description": record["description"]
                })


            # =====================================================
            # 7. Remove duplicate relationships
            # =====================================================

            unique_links = []
            seen = set()

            for link in links:

                source = link["source"]
                target = link["target"]
                relationship = link["relationship"]

                if relationship == "INTERACTS_WITH":

                    key = (
                        tuple(sorted([source, target])),
                        relationship
                    )

                else:

                    key = (
                        source,
                        target,
                        relationship
                    )

                if key in seen:
                    continue

                seen.add(key)
                unique_links.append(link)


            # =====================================================
            # 8. Return graph
            # =====================================================

            return {
                "status": "success",

                "nodes": nodes,

                "links": unique_links,

                "disease": diseases,

                "selected_drugs": selected_drug_names
            }

    finally:
        driver.close()