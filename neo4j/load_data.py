#!/usr/bin/env python3
"""Load medication data into Neo4j graph database"""

import pandas as pd
from neo4j import GraphDatabase
import os

class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.uri = uri
        self.user = user
        self.password = password

    def close(self):
        self.driver.close()

    def create_constraints_and_indexes(self):
        """Step 1: Create constraints and indexes"""
        print("Step 1: Creating constraints and indexes...")

        with self.driver.session() as session:
            # Read and execute schema from file
            schema_file = os.path.join(os.path.dirname(__file__), 'schema.cypher')
            with open(schema_file, 'r') as f:
                schema_cypher = f.read()
            session.run(schema_cypher)

        print("✓ Constraints and indexes created")

    def load_diseases(self):
        """Step 2: MERGE Disease nodes"""
        print("Step 2: Loading Disease nodes...")

        with self.driver.session() as session:
            # Read drug_disease.csv to get unique diseases
            drugs_disease_file = os.path.join(os.path.dirname(__file__), '../datasets/drug_disease.csv')
            df = pd.read_csv(drugs_disease_file)

            for _, row in df.iterrows():
                cypher = """
                MERGE (d:Disease {
                    disease_id: $disease_id,
                    disease_name: $disease_name,
                    disease_name_kn: $disease_name_kn,
                    disease_name_tulu: $disease_name_tulu
                })
                """
                session.run(cypher,
                           disease_id=row['disease_id'],
                           disease_name=row['disease_name'],
                           disease_name_kn=row.get('disease_name_kn', row['disease_name']),
                           disease_name_tulu=row.get('disease_name_tulu', row['disease_name']))

        print(f"✓ Loaded {len(df)} disease nodes")

    def load_drugs(self):
        """Step 3: MERGE Drug nodes"""
        print("Step 3: Loading Drug nodes...")

        with self.driver.session() as session:
            # Read english_master_dataset.csv
            drugs_file = os.path.join(os.path.dirname(__file__), '../datasets/english_master_dataset.csv')
            df = pd.read_csv(drugs_file)

            for _, row in df.iterrows():
                cypher = """
                MERGE (d:Drug {
                    drug_id: $drug_id,
                    drug_name: $drug_name,
                    generic_name: $generic_name,
                    drug_class: $drug_class,
                    active_ingredient: $active_ingredient,
                    description_en: $description_en,
                    description_kn: $description_kn,
                    description_tulu: $description_tulu,
                    warnings_en: $warnings_en,
                    warnings_kn: $warnings_kn,
                    warnings_tulu: $warnings_tulu,
                    contraindications_en: $contraindications_en,
                    contraindications_kn: $contraindications_kn,
                    contraindications_tulu: $contraindications_tulu,
                    source: $source
                })
                """
                session.run(cypher,
                           drug_id=row['drug_id'],
                           drug_name=row['drug_name'],
                           generic_name=row.get('generic_name', ''),
                           drug_class=row.get('drug_class', ''),
                           active_ingredient=row.get('active_ingredient', ''),
                           description_en=row.get('description_en', ''),
                           description_kn=row.get('description_kn', ''),
                           description_tulu=row.get('description_tulu', ''),
                           warnings_en=row.get('warnings_en', ''),
                           warnings_kn=row.get('warnings_kn', ''),
                           warnings_tulu=row.get('warnings_tulu', ''),
                           contraindications_en=row.get('contraindications_en', ''),
                           contraindications_kn=row.get('contraindications_kn', ''),
                           contraindications_tulu=row.get('contraindications_tulu', ''),
                           source=row.get('source', ''))

        print(f"✓ Loaded {len(df)} drug nodes")

    def load_drug_relationships(self):
        """Step 4 & 5: CREATE TREATS and HAS_SIDE_EFFECT relationships"""
        print("Step 4 & 5: Loading drug relationships...")

        with self.driver.session() as session:
            # Load drug_disease.csv for TREATS relationships
            drugs_disease_file = os.path.join(os.path.dirname(__file__), '../datasets/drug_disease.csv')
            df_disease = pd.read_csv(drugs_disease_file)

            for _, row in df_disease.iterrows():
                cypher = """
                MATCH (d:Drug {drug_id: $drug_id})
                MATCH (dis:Disease {disease_id: $disease_id})
                CREATE (d)-[:TREATS]->(dis)
                """
                session.run(cypher,
                           drug_id=row['drug_id'],
                           disease_id=row['disease_id'])

            print(f"✓ Created {len(df_disease)} TREATS relationships")

            # Load drug_sideeffects.csv for HAS_SIDE_EFFECT relationships
            drugs_sideeffects_file = os.path.join(os.path.dirname(__file__), '../datasets/drug_sideeffects.csv')
            df_sideeffects = pd.read_csv(drugs_sideeffects_file)

            for _, row in df_sideeffects.iterrows():
                cypher = """
                MATCH (d:Drug {drug_id: $drug_id})
                MATCH (se:SideEffect {name: $side_effect_name})
                CREATE (d)-[:HAS_SIDE_EFFECT]->(se)
                """
                session.run(cypher,
                           drug_id=row['drug_id'],
                           side_effect_name=row['side_effect'])

            print(f"✓ Created {len(df_sideeffects)} HAS_SIDE_EFFECT relationships")

    def load_interactions(self):
        """Step 6: MERGE Interaction nodes + INTERACTS_WITH relationships"""
        print("Step 6: Loading interactions...")

        with self.driver.session() as session:
            # Read drug_interactions.csv
            drugs_interactions_file = os.path.join(os.path.dirname(__file__), '../datasets/drug_interactions.csv')
            df = pd.read_csv(drugs_interactions_file)

            for _, row in df.iterrows():
                # Only create graph edges for drug2_in_scope = "yes"
                if row.get('drug2_in_scope', '').lower() == 'yes':
                    cypher = """
                    MATCH (d1:Drug {drug_id: $drug1_id})
                    MATCH (d2:Drug {drug_id: $drug2_id})
                    MERGE (i:Interaction {
                        interaction_id: $interaction_id,
                        severity: $severity,
                        description: $description,
                        disclaimer: $disclaimer,
                        drug2_in_scope: $drug2_in_scope
                    })
                    CREATE (d1)-[r:INTERACTS_WITH {severity: $severity, description: $description, disclaimer: $disclaimer}]->(d2)
                    """
                    session.run(cypher,
                               interaction_id=row['interaction_id'],
                               drug1_id=row['drug1_id'],
                               drug2_id=row['drug2_id'],
                               severity=row['severity'],
                               description=row.get('description', ''),
                               disclaimer=row.get('disclaimer', ''),
                               drug2_in_scope=row.get('drug2_in_scope', ''))

        print(f"✓ Created {len(df[df.get('drug2_in_scope', '').str.lower() == 'yes'])} INTERACTS_WITH relationships")

    def add_multilingual_properties(self):
        """Step 7: Add multilingual properties to Drug nodes"""
        print("Step 7: Adding multilingual properties to Drug nodes...")

        with self.driver.session() as session:
            # Load kannada_master_dataset.csv
            kannada_file = os.path.join(os.path.dirname(__file__), '../datasets/kannada_master_dataset.csv')
            df_kannada = pd.read_csv(kannada_file)

            for _, row in df_kannada.iterrows():
                cypher = """
                MATCH (d:Drug {drug_id: $drug_id})
                SET d.description_kn = $description_kn,
                    d.warnings_kn = $warnings_kn,
                    d.contraindications_kn = $contraindications_kn
                """
                session.run(cypher,
                           drug_id=row['drug_id'],
                           description_kn=row.get('description_kn', ''),
                           warnings_kn=row.get('warnings_kn', ''),
                           contraindications_kn=row.get('contraindications_kn', ''))

            # Load tulu_master_dataset.csv
            tulu_file = os.path.join(os.path.dirname(__file__), '../datasets/tulu_master_dataset.csv')
            df_tulu = pd.read_csv(tulu_file)

            for _, row in df_tulu.iterrows():
                cypher = """
                MATCH (d:Drug {drug_id: $drug_id})
                SET d.description_tulu = $description_tulu,
                    d.warnings_tulu = $warnings_tulu,
                    d.contraindications_tulu = $contraindications_tulu
                """
                session.run(cypher,
                           drug_id=row['drug_id'],
                           description_tulu=row.get('description_tulu', ''),
                           warnings_tulu=row.get('warnings_tulu', ''),
                           contraindications_tulu=row.get('contraindications_tulu', ''))

        print("✓ Added multilingual properties to Drug nodes")

    def run_full_pipeline(self):
        """Run the complete Neo4j data pipeline"""
        print("Starting Neo4j data pipeline...")
        print(f"Neo4j URI: {self.uri}")
        print(f"User: {self.user}")
        print()

        try:
            self.create_constraints_and_indexes()
            print()

            self.load_diseases()
            print()

            self.load_drugs()
            print()

            self.load_drug_relationships()
            print()

            self.load_interactions()
            print()

            self.add_multilingual_properties()
            print()

            print("✅ Neo4j data pipeline completed successfully!")

        except Exception as e:
            print(f"❌ Error in pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file

    # Configuration from environment variables
    URI = os.getenv("NEO4J_URI", "neo4j+s://xxxx.databases.neo4j.io")
    USER = os.getenv("NEO4J_USER", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

    print("Note: Using environment variables for Neo4j connection.")
    print("To override, set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env or environment.")
    print(f"URI: {URI}")
    print(f"User: {USER}")
    print()

    # Check if using placeholder values
    if "xxxx.databases.neo4j.io" in URI or PASSWORD == "your_password":
        print("��⚠��️  Warning: Using placeholder Neo4j credentials!")
        print("   Please update your .env file with actual Neo4j Aura credentials.")
        print()

        if input("Continue anyway? (y/n): ").lower() != 'y':
            print("Please update your .env file and run again.")
            exit(1)

    loader = Neo4jLoader(URI, USER, PASSWORD)
    try:
        loader.run_full_pipeline()
    finally:
        loader.close()