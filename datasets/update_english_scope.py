"""Rebuild English, derived CSVs, compatibility copies, and the ML bundle.

Existing translations and synthetic patient source data remain maintained separately.
Run from any directory: python datasets/update_english_scope.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    for name in ("build_dataset.py", "split_master_dataset.py"):
        subprocess.run([sys.executable, str(ROOT / name)], check=True)
    files = {
        ROOT.parent / "english_master_dataset.csv": ROOT / "english_master_dataset.csv",
        ROOT.parent / "backend/app/datasets/english_master_dataset.csv": ROOT / "english_master_dataset.csv",
    }
    # Refresh only compatibility copies that already exist.
    for name in ("drug_disease.csv", "drug_sideeffects.csv", "drug_interactions.csv"):
        for directory in (ROOT.parent, ROOT.parent / "backend/app/datasets"):
            destination = directory / name
            if destination.exists():
                files[destination] = ROOT / name
    for destination, source in files.items():
        shutil.copyfile(source, destination)
    subprocess.run([sys.executable, str(ROOT / "prepare_ml_data.py")], check=True)


if __name__ == "__main__":
    main()
