"""Export the user-maintained Tulu workbook to the CSV consumed by the app.

Run this after editing tulu_master_dataset.xlsx. Cell text is preserved exactly.
Do not run the older build_tulu_dataset.py to refresh this curated dataset.
"""
from pathlib import Path
import pandas as pd


def main():
    directory = Path(__file__).resolve().parent
    source = directory / "tulu_master_dataset.xlsx"
    target = directory / "tulu_master_dataset.csv"
    data = pd.read_excel(source, dtype=str, keep_default_na=False)
    data.columns = ["_".join(str(column).strip().lower().split()) for column in data.columns]
    required = {"drug_id", "drug_name", "generic_name", "disease", "drug_class",
                "active_ingredient", "description", "side_effects", "contraindications", "warnings", "source"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if data.empty or data.columns.duplicated().any():
        raise ValueError("Workbook is empty or has duplicate column names")
    for column in required:
        if data[column].str.strip().eq("").any():
            raise ValueError(f"Blank values in {column}")
    for column in ("drug_id", "drug_name"):
        if data[column].str.strip().str.casefold().duplicated().any():
            raise ValueError(f"Duplicate values in {column}")
    data.to_csv(target, index=False, encoding="utf-8")
    exported = pd.read_csv(target, dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(data, exported)
    print(f"Exported and verified {len(data)} medicines to {target.name}; cell text preserved.")


if __name__ == "__main__":
    main()
