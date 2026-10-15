# Tulu dataset

The maintained source is `tulu_master_dataset.xlsx`, supplied by the user.
The app reads `tulu_master_dataset.csv`, exported from that workbook.

After editing the workbook, run:

```powershell
rtk proxy .venv-1/Scripts/python.exe datasets/import_tulu_workbook.py
```

The importer needs pandas and openpyxl. It normalizes column headers to
snake_case, validates required fields and unique medicine names/IDs, and
verifies that all cell text survives the UTF-8 CSV export unchanged.
Restart the backend afterward because medicine datasets are cached in memory.

The older `build_tulu_dataset.py` contains earlier generated wording; do not
use it to refresh the user-maintained dataset.

Validated: 30 exported medicines; all 30 live Tulu medicine API results matched
the workbook content; Metformin voice lookup returned the new description;
the new description produced MP3 speech; eight regression tests passed.
Speech still uses Kannada synthesis for Tulu text, so pronunciation remains
dependent on that voice. This import verifies data integration, not clinical
accuracy or translation quality. Existing database records are not reimported.
