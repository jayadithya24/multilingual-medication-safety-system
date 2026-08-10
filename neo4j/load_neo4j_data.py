"""
NeoGraphMed - Drug Intelligence Module
Loads english_master_dataset.csv into Neo4j as a graph.
"""

import csv
import re
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
CSV_PATH = "english_master_dataset.csv"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_side_effects(text):
    if not text:
        return []
    first_sentence = text.split(".")[0]
    first_sentence = re.sub(r"\([^)]*\)", "", first_sentence)
    parts = [p.strip() for p in first_sentence.split(",")]
    return [p for p in parts if p and len(p) < 60]


def extract_interacting_drugs(text, known_drug_names):
    if not text:
        return []
    found = []
    lower_text = text.lower()
    for name in known_drug_names:
        if name.lower() in lower_text:
            found.append(name)
    return found


def main():
    rows = read_csv(CSV_PATH)
    known_drug_names = [r["drug_name"] for r in rows]

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database="neographmed") as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Cleared existing graph data.")

        diseases_created = set()
        side_effects_created = set()
        drug_count = 0
        side_effect_rel_count = 0
        interaction_rel_count = 0

        for row in rows:
            drug_name = row["drug_name"].strip()

            session.run(
                """
                MERGE (d:Drug {name: $name})
                SET d.generic_name = $generic_name,
                    d.drug_class = $drug_class,
                    d.description = $description,
                    d.contraindications = $contraindications,
                    d.warnings = $warnings
                """,
                name=drug_name,
                generic_name=row.get("generic_name", ""),
                drug_class=row.get("drug_class", ""),
                description=row.get("description", ""),
                contraindications=row.get("contraindications", ""),
                warnings=row.get("warnings", ""),
            )
            drug_count += 1

            disease_name = row["disease"].strip()
            session.run(
                """
                MERGE (dis:Disease {name: $disease_name})
                MERGE (d:Drug {name: $drug_name})
                MERGE (d)-[:TREATS]->(dis)
                """,
                disease_name=disease_name,
                drug_name=drug_name,
            )
            diseases_created.add(disease_name)

            effects = extract_side_effects(row.get("side_effects", ""))
            for effect in effects:
                session.run(
                    """
                    MERGE (s:SideEffect {name: $effect})
                    MERGE (d:Drug {name: $drug_name})
                    MERGE (d)-[:CAUSES]->(s)
                    """,
                    effect=effect,
                    drug_name=drug_name,
                )
                side_effects_created.add(effect)
                side_effect_rel_count += 1

            interacting = extract_interacting_drugs(
                row.get("major_interactions", ""), known_drug_names
            )
            for other_drug in interacting:
                if other_drug != drug_name:
                    session.run(
                        """
                        MATCH (d1:Drug {name: $d1})
                        MATCH (d2:Drug {name: $d2})
                        MERGE (d1)-[:INTERACTS_WITH]->(d2)
                        """,
                        d1=drug_name,
                        d2=other_drug,
                    )
                    interaction_rel_count += 1

        print(f"Drugs created: {drug_count}")
        print(f"Diseases created: {len(diseases_created)} -> {diseases_created}")
        print(f"Unique side effects created: {len(side_effects_created)}")
        print(f"CAUSES relationships created: {side_effect_rel_count}")
        print(f"INTERACTS_WITH relationships created: {interaction_rel_count}")

    driver.close()
    print("\nDone. Open Neo4j Browser and run: MATCH (n) RETURN n LIMIT 50")


if __name__ == "__main__":
    main()
