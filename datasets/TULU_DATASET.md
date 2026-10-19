# Tulu dataset

The maintained source is `tulu_master_dataset.csv`, updated by the user to
100 medicines across 10 diseases on 19 October 2026. The backend reads this
CSV directly. The older workbook, importer and 30-drug generator are archived
under `artifacts/`; they must not overwrite the current CSV.

After editing, run `python datasets/prepare_ml_data.py` and restart the backend.
See the export manifest's `missing_optional_fields` for the 11 missing
drug-class values; no translated clinical content is fabricated.

Tulu speech uses Kannada synthesis, so pronunciation depends on that voice.
Data integration checks do not certify medical accuracy or translation quality.
