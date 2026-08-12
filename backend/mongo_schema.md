# MongoDB Collections & Schema (Phase 1)

This document defines the authoritative MongoDB collections, field contracts, indexes and validation guidance for Phase 1 of the project.

Collections
-----------

- `drugs` — master drug documents combining English + translations and core clinical fields
- `diseases` — mapping of `drug_id` -> disease records
- `side_effects` — mapping of `drug_id` -> side-effect records
- `interactions` — pairwise drug interaction records
- `validation_stats` — metrics produced by the validation service
- `users` — minimal user/auth data for admin operations (optional; required for JWT-backed admin endpoints)

Design principles
-----------------
- Keep `drug_id` as the canonical, stable string identifier (lowercased slug). All relationships reference `drug_id`.
- Store multilingual fields under `translations` so a single `drugs` document contains localized names and convenience lookups.
- Use unique index on `drug_id` and a case-insensitive/sanitized text index for fuzzy `drug_name` searches.
- Interaction records are stored as directed pairs (`drug1_id`, `drug2_id`) with a `severity` domain `{"Mild","Moderate","Severe"}` and boolean `drug2_in_scope`.

1) `drugs` document shape

Example:

```json
{
  "_id": ObjectId("..."),
  "drug_id": "paracetamol",
  "drug_name": "Paracetamol",
  "generic_name": "Acetaminophen",
  "drug_class": "Analgesic",
  "active_ingredient": "Paracetamol",
  "description": "Short description text...",
  "side_effects": "Comma separated or bullet text",
  "contraindications": "...",
  "warnings": "...",
  "major_interactions": "...",
  "source": "datasets/english_master_dataset.csv",
  "translations": {
    "english": {"drug_name": "Paracetamol"},
    "kannada": {"drug_id":"paracetamol","drug_name":"ಪ್ಯಾರಸೆಟಮಾಲ್"},
    "tulu": {"drug_id":"paracetamol","drug_name":"Paracetamol (Tulu)"}
  },
  "created_at": ISODate("2026-08-12T00:00:00Z")
}
```

Required fields: `drug_id`, `drug_name`. Other fields should be present where available.

Indexes:
- `{drug_id: 1}` unique
- `{drug_name: "text", "translations.kannada.drug_name": "text", "translations.tulu.drug_name": "text"}` for cross-language fuzzy search
- optional case-insensitive index for exact matches: `{drug_name_lower: 1}` maintained by loader

2) `diseases` document shape

One document per mapping row (or grouped per drug_id).

Example:

```json
{ "_id": ..., "drug_id": "paracetamol", "disease": "Fever" }
```

Indexes:
- `{drug_id:1}`

3) `side_effects` document shape

Example:

```json
{ "_id": ..., "drug_id": "paracetamol", "side_effect": "Nausea" }
```

Indexes:
- `{drug_id:1}`, optional `{side_effect: "text"}` for search

4) `interactions` document shape

Example:

```json
{
  "_id": ..., 
  "drug1_id": "paracetamol",
  "drug2_id": "warfarin",
  "severity": "Moderate",
  "drug2_in_scope": true,
  "notes": "Take care when co-administered",
  "created_at": ISODate("2026-08-12T00:00:00Z")
}
```

Constraints and indexes:
- Compound unique index on `{drug1_id:1, drug2_id:1}` to prevent duplicate pair rows.
- Index on `{drug2_id:1}` to support reverse lookups.

Field semantics and domain rules:
- `severity`: must be one of `"Mild"`, `"Moderate"`, `"Severe"`.
- `drug2_in_scope`: boolean in the DB; the loader should convert `yes`/`no` to true/false.

5) `validation_stats` document shape

Used by runtime validation service to publish metrics per run/user.

Example:

```json
{
  "_id": ..., 
  "run_id": "2026-08-12T1234Z",
  "timestamp": ISODate(...),
  "total_drugs": 30,
  "total_interactions": 45,
  "in_scope_interactions": 30,
  "out_of_scope_interactions": 15,
  "errors": []
}
```

6) `users` (optional)

Minimum fields for admin operations (used by JWT auth in Phase 1):

```json
{ "username": "admin", "email": "admin@example.com", "hashed_password": "...", "roles": ["admin"] }
```

Loader responsibilities
-----------------------
- `backend/mongo_loader.py` should:
  - produce `drug_id` slugs consistently and normalize to lowercase
  - populate `translations` subdocuments when language CSV rows exist
  - convert `drug2_in_scope` values to boolean
  - create `drug_name_lower` or maintain case-insensitive helper fields if needed for exact matching

Validation and schema enforcement
---------------------------------
- Use MongoDB collection validators (JSON Schema) for strictness where possible. Example validator for `interactions`:

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["drug1_id","drug2_id","severity"],
    "properties": {
      "drug1_id": {"bsonType": "string"},
      "drug2_id": {"bsonType": "string"},
      "severity": {"enum": ["Mild","Moderate","Severe"]},
      "drug2_in_scope": {"bsonType": "bool"}
    }
  }
}
```

Operational notes
-----------------
- The initial loader run may `delete_many({})` and `insert_many()` for a clean initial load. For production, prefer upserts or incremental loading.
- Ensure the MongoDB user has proper privileges for `createIndex`, `insert`, and `createCollection` when running the loader.
- For testing without a live DB, use `mongomock` or the loader's `build_documents()` function and run unit tests against the returned dictionaries.

Next steps (optional)
---------------------
- I can add the JSON Schema validators as a short script `backend/mongo_validators.py` to create collections with validators.
- I can mark `backend/mongo_schema.md` as committed and update the todo list.
