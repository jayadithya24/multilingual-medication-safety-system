# Maintained datasets

Edit only `english_master_dataset.csv`, `kannada_master_dataset.csv` and
`tulu_master_dataset.csv` for the application reference content. Each contains
100 medicines across 10 localized disease categories, with matching `drug_id`
values. Save standard UTF-8 CSV, not tab-separated text with a `.csv` extension.

After editing, from the project root:

```powershell
python tools/datasets/sync_datasets.py
```

This validates alignment, refreshes compatibility copies and relationship
tables, and exports the ML preparation bundle without rewriting your masters.
Restart the backend to clear its cached data. The English JSON generator was
removed so it cannot overwrite manually maintained CSVs. Maintenance scripts
now live in `tools/datasets/`; synthetic-patient generation lives in `ml/`.

Validation now rejects missing required drug classes. The current Tulu file
contains 11 blanks that require reviewed translations; no values are invented.
For the explicitly incomplete demonstration catalog only, use
`python tools/datasets/sync_datasets.py --allow-incomplete`. Its output lists
the missing counts. This exception is not a publication-quality validation.
After synchronization and with the project's Neo4j instance running, use
`python -m neo4j.load_data --apply --sync` to back up and reconcile the graph.
This updates only the application's reference relationship types and verifies
the exact node/relationship sets. Restart the backend to clear cached data.

The other files still have consumers:

- `drug_*.csv`: graph relationships and existing interaction checks.
- `legacy_interaction_records.json`, `interaction_evidence.json`: separately
  maintained legacy severity records and source/class mappings. Editing master
  prose does not train or clinically validate severity labels.
- `new_interaction_candidates.json`: current explicit-name, ungraded text
  matches; generic wording does not invent named-pair edges.
- `synthetic_*.csv`, `ml_ready/`: existing synthetic patient experiments and
  aligned catalog exports; not actual patients or new clinical outcomes.
- `external/`: separately licensed DDInter model data, not part of the master
  CSV publication package.

For a Kaggle draft, run `python tools/datasets/export_kaggle.py`. It creates
`artifacts/kaggle-multilingual-medication-draft.zip` with the three CSVs, schema,
quality report, checksums and an unresolved source/licensing review. It does not
publish or grant a license. Confirm source rights and authorship before release.
