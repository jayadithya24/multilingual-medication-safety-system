# Neo4j validation — 24 September 2026

The local server accepts connections on 7474 and 7687. A fresh process using the current project configuration (`neo4j://127.0.0.1:7687`) fails authentication with `AuthError`. Successful application Cypher execution against this database has therefore not been established.

The running application's `/neo4j/graph` response exactly matches the CSV fallback: 224 nodes and 361 relationships. A rendered graph is not proof of a working Neo4j connection. The recent browser and regression tests establish UI behavior and filtering, not clinical correctness.

The read-only evidence is in `neo4j-audit-2026-09-24.json`. No database records or credentials were changed by the audit.

## 1. Verify the connection

Use the credentials for the running DBMS in Neo4j Desktop to log into Neo4j Browser at http://localhost:7474. Match `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in the project `.env` to that instance. The app's admin account is separate from the Neo4j database account. Restart the backend after editing `.env`; the environment loader does not replace already loaded values.

Run this read-only check from the project root:

```powershell
rtk proxy .venv/Scripts/python.exe tools/audit_neo4j.py
```

Require live node/relationship counts and no authentication/connection error. `verify_connectivity()` checks a real connection, including authentication: https://neo4j.com/docs/python-manual/current/connect/

## 2. Inspect actual records in Neo4j Browser

Run each statement separately, against the application's database.

```cypher
RETURN 1 AS connection_ok;
```

```cypher
MATCH (n)
RETURN labels(n) AS labels, count(*) AS nodes;
```

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS total;
```

Inspect a selected medicine visually:

```cypher
MATCH (d:Drug)-[r]-(other)
WHERE toLower(coalesce(d.name, d.drug_name, d.drug_id, d.id)) = 'celecoxib'
RETURN d, r, other;
```

Inspect exact direction and relationship evidence in table view:

```cypher
MATCH (d:Drug)-[r]-(other)
WHERE toLower(coalesce(d.name, d.drug_name, d.drug_id, d.id)) = 'celecoxib'
RETURN properties(startNode(r)) AS source,
       type(r) AS relationship,
       properties(endNode(r)) AS target,
       properties(r) AS evidence;
```

An empty result is not proof that the medicine has no relationships: check labels, field names, the selected database and import completeness.

## 3. Compare the graph with the source files

| Graph relationship | Expected source |
|---|---|
| TREATS | datasets/drug_disease.csv |
| CAUSES | datasets/drug_sideeffects.csv |
| INTERACTS_WITH | datasets/drug_interactions.csv, currently restricted to drug2_in_scope=yes |

Compare normalized endpoint identifiers, relationship type, direction, severity and duplicates. Every displayed relationship must have a source row; every in-scope source row must be accounted for. Check missing and extra relationships, not just aggregate counts.

For Celecoxib, the current files contain one disease row (Arthritis), 14 side-effect rows and one in-scope interaction row (Methotrexate). This describes dataset contents; it is not independent clinical verification. Other interaction rows are excluded from this graph by the current scope filter.

## 4. Resolve findings before declaring correctness

- The interaction CSV labels Ibuprofen–Methotrexate both Moderate and Severe. Source order must not decide which is medically correct.
- The CSV fallback reuses `hypertension` for a Disease ID and a SideEffect ID, merging distinct entity types. Namespace identifiers by type before considering node classifications verified.
- Side-effect spelling/case variants create duplicates, such as `Diarrhea` and `diarrhea`.
- Only 10 of 157 interaction rows are marked in scope. A missing graph edge does not establish absence of an interaction.
- `neo4j/load_data.py` does not agree with the current CSV and reader schema: it expects missing fields, uses `drug_name`/`disease_name` where graph readers expect `name`, and creates `HAS_SIDE_EFFECT` while readers expect `CAUSES`. Do not use it as proof of a valid import without correcting and testing these mappings.
- Per-interaction citations are absent from the interaction CSV. CSV agreement proves import consistency, not clinical validity. Record an authoritative source, relevant passage, review date and reviewer for each relationship and resolve conflicting evidence through qualified clinical review.

The graph's CAUSES wording is the existing data model; a side-effect listing alone does not establish individual causation. Clinical evidence and appropriate relationship terminology need review separately from Cypher execution.
