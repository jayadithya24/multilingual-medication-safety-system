# Saved dataset alignment

- English, Kannada, and Tulu each contain 30 unique medicine names in identical order.
- No blank cells were found in the existing columns.
- All three assign the same 10 medicines to each of the diabetes, hypertension,
  and arthritis groups. Translated category names differ as expected.
- Kannada and Tulu `drug_id` values agree. English has no `drug_id` column.
- All three CSVs now contain populated `major_interactions` fields.
- The Tulu workbook has no `major_interactions` column. Its Insulin Glargine
  `drug_id` is `insulin_glargine`, whereas the CSV uses `insulin-glargine`.
  All other shared workbook/CSV cells match. Reimporting the workbook can
  therefore remove CSV interaction data and change that ID.

This is a structural and category-alignment check, not a certification that
all descriptions, warnings, contraindications, or translations are clinically
equivalent. Dataset content was not changed during this review.
