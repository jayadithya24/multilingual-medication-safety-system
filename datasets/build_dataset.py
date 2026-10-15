"""Build English from english_master_records.json. Run: python datasets/build_dataset.py."""
import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ["drug_name", "generic_name", "disease", "drug_class", "active_ingredient",
          "description", "side_effects", "contraindications", "warnings", "major_interactions", "source"]


def main(src=ROOT / "english_master_records.json", dst=ROOT / "english_master_dataset.csv"):
    rows = json.loads(Path(src).read_text(encoding="utf-8"))
    if not rows:
        raise ValueError("Canonical records are empty")
    names = set()
    for row in rows:
        if set(row) != set(FIELDS) or any(not isinstance(row[f], str) or not row[f].strip() for f in FIELDS):
            raise ValueError("Every record must contain exactly 11 populated English fields")
        name = row["drug_name"].strip().casefold()
        if name in names:
            raise ValueError(f"Duplicate medicine: {row['drug_name']}")
        names.add(name)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", newline="",
                                         dir=dst.parent, delete=False) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, dst)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    print(f"Wrote {len(rows)} medicines -> {dst}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "english_master_records.json")
    parser.add_argument("--output", type=Path, default=ROOT / "english_master_dataset.csv")
    args = parser.parse_args()
    main(args.source, args.output)
