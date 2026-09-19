# ML training handoff

The `ml_ready/` bundle is ready for **experimental synthetic patient-level
interaction-severity classification**, not prescription recommendation or clinical
deployment. The preparation script never changes the source CSVs or translations.

## Rebuild and verify

From the repository root, using Python with pandas installed:

```powershell
rtk proxy .venv-1/Scripts/python.exe datasets/prepare_ml_data.py
rtk proxy .venv-1/Scripts/python.exe -m pytest tests/test_ml_data.py -q
```

The output is deterministic for the same inputs and seed (`--seed 42`). The
manifest contains source and output SHA-256 hashes. Rebuild after any source
edit; keep the manifest with experiment results. Do not rerun the old synthetic
patient generator to prepare a split: it creates different dated source data.

## Files and keys

| File | Purpose |
| --- | --- |
| `train.csv`, `validation.csv`, `test.csv` | One row per patient, explicit input columns and `target_severity` |
| `manifest.json` | Exact feature allowlist, target, class weights, hashes, validation summary and limitations |
| `patient_splits.csv` | Patient-level split membership shared by every related table |
| `drug_catalog.csv` | Shared medicine IDs/names and canonical disease IDs |
| `master_localized.csv` | 90 rows: 30 medicines × 3 languages, joined using `drug_id` + `language` |
| `patient_drugs.csv` | Prescription details, canonical disease IDs and patient split |
| `patient_interactions.csv` | Positive recorded interaction labels, for audit; not classifier input |

English IDs are added to the exported catalog using the matching medicine names
and the agreed Kannada/Tulu IDs. Diabetes/Type 2 Diabetes becomes
`type_2_diabetes`; the other canonical categories are `hypertension` and
`arthritis`. Original translated text is preserved in the localized master.

## Load training inputs

```python
import json
from pathlib import Path
import pandas as pd

root = Path("datasets/ml_ready")
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
train = pd.read_csv(root / "train.csv", keep_default_na=False)
validation = pd.read_csv(root / "validation.csv", keep_default_na=False)
test = pd.read_csv(root / "test.csv", keep_default_na=False)
X_train = train[manifest["features"]]
y_train = train[manifest["target"]]
X_validation = validation[manifest["features"]]
y_validation = validation[manifest["target"]]
# Fit encoders/scalers only on X_train. Handle unseen categorical values.
# Example sklearn estimators may accept manifest["train_class_weights"].
# Tune on validation, then evaluate the test split once.
```

`keep_default_na=False` is essential: **None is a target label**. It means no
interaction was recorded in the supplied source rules; it does not mean a
medication combination is clinically safe.

## Target and leakage boundaries

The default target is each patient's highest recorded drug-interaction severity.
Inputs are age, gender, kidney/liver function, BMI category, condition indicators,
and 30 medicine-presence indicators. Patient IDs are join keys only. Language,
region, share IDs, dates, and labels are not model inputs.

Do not add `highest_severity`, interaction severities, master interaction text,
or summaries derived from the target as features. Do not duplicate each patient
three times for translations and then randomly split rows. The same patient and
all their prescriptions must remain in one partition.

These labels are deterministic outputs of the generator's drug-pair rules, not
observed outcomes. A classifier primarily learns to reproduce those rules.
Keep the rule-based system as a baseline. Patient-level separation does not
test generalization to unseen drug pairs: the same pairs/regimens may occur in
multiple splits. Such an experiment needs a separately designed pair holdout.

## Known limitations carried into the manifest

- 43,700 patients; 99,877 prescriptions; 2,041 recorded positive interactions.
- Approximate 80/10/10 stratified split: 34,959 / 4,370 / 4,371 patients.
- Patient labels contain None, Mild, and Severe; **no Moderate patient targets**.
  Moderate exists at the interaction-pair level but is masked by more severe
  pairs in each affected patient's maximum. Do not fabricate Moderate examples.
- Strong imbalance: report per-class precision/recall/F1, macro-F1 and confusion
  matrices; accuracy alone is misleading. Class weights are computed from train
  only. Never oversample validation/test.
- The source rates Ibuprofen–Methotrexate both Moderate and Severe. Validation
  reproduces the original generator's maximum-severity policy and reports the
  conflict; a qualified review must resolve it before clinical use.
- Clinical accuracy and translation equivalence remain unverified.
- The Tulu CSV contains edits/columns absent from its older Excel workbook.
  This exporter reads the current CSVs. Do not overwrite them with a workbook
  reimport without reconciling those differences.

The bundle contains all aligned master fields for separate NLP experiments,
but it is not a ready-made multilingual NLP evaluation set: 30 medicines are
too few to infer broad language coverage, and that task needs its own split.
