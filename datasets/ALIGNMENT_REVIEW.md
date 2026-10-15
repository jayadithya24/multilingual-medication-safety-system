# Saved dataset alignment

- English contains 100 unique medicine names across 10 categories. Kannada and
  Tulu retain their existing 30 medicines; their updates are deferred.
- No blank cells were found in the existing columns.
- The shared 30 medicines retain the diabetes, hypertension and arthritis
  assignments. The other 70 medicines currently have English content only.
- Kannada and Tulu `drug_id` values agree. English has no `drug_id` column.
- All three CSVs now contain populated `major_interactions` fields.
- The Tulu workbook has no `major_interactions` column. Its Insulin Glargine
  `drug_id` is `insulin_glargine`, whereas the CSV uses `insulin-glargine`.
  All other shared workbook/CSV cells match. Reimporting the workbook can
  therefore remove CSV interaction data and change that ID.

The ML export contains 100 catalog records and 160 supplied localized records.
Its manifest lists missing translations and the 70 medicines/seven categories
absent from the existing synthetic patient examples. It does not fabricate
translations, patient examples or severity ratings for the new interactions.

`update_english_scope.py` rebuilds English from `english_master_records.json`,
refreshes derived tables and existing compatibility CSV copies, then validates
and exports the ML bundle. Original structured interactions and side effects are
retained in versioned legacy records. New explicit-name interaction candidates
are ungraded, with source sentences saved in `new_interaction_candidates.json`.

This verifies structural and category alignment, not clinical accuracy or
translation equivalence. Restart an already running backend to clear CSV caches.
