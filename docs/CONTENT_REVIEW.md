# Human review handoff

Run `.venv-dataset/Scripts/python.exe tools/prepare_content_review.py` to produce
`artifacts/content-review/language-review.csv` and a source-hash manifest.
The queue contains all 100 Kannada and all 100 Tulu medicines, flags missing
classes, and leaves correction/source/reviewer fields empty. Nothing is approved
automatically. No reviewer is currently available; all rows remain pending.

The native speaker should compare each record with the English source, including
medicine names, meaning, warnings and spoken pronunciation. A pharmacist must
review clinical meaning and classes separately. Record the exact proposed field
change, a source/reference, reviewer names, date and status. Source hashes must
still match before applying corrections; regenerate/reconcile if CSVs change.
Do not fill a blank by copying an unrelated medicine's class or by guessing.

The repeated English interaction narratives are master-record text, not proof
of a specific interacting pair. Pair-specific additions must identify both
ingredients and the supporting source; a general reference paragraph need not
name every possible partner. Keep project severity grades separate from a
source's original scale. Do not infer a severity merely from the wording.

Brand mappings need product name, manufacturer, market, formulation/strength,
all active ingredients, source URL/document/version, verification date and human
approval. Combination products must not be reduced to a single ingredient.
No new mapping or clinical rule is activated by this checklist.

Until review is completed, retain the Tulu synthesis disclosure, missing-content
flags and prototype limitations. Do not label the dataset clinically validated
or the Kaggle package publication-ready. This handoff is not a language or
pharmacist review, licence clearance, or consent to publish personal information.
