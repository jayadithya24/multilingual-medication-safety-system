# ML Validation Report

Generated for the existing patient-risk ML scope. This report does not modify datasets and does not overwrite production model artifacts.

## Patient-Risk ML

- Model artifacts: `ml/models/risk_model.joblib`, `ml/models/risk_preprocessor.joblib`
- Training script: `ml/train_risk_model.py`
- Validation script: `ml/validate_risk_model.py`
- API service: `backend/app/services/risk_prediction_service.py`
- API route: `POST /ml/risk-predict` in `backend/app/routes/risk_prediction.py`
- Algorithm: `RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1)`
- Datasets used: `datasets/synthetic_patients.csv`, `datasets/synthetic_patient_interactions.csv`
- Target: `severity`
- Full features: `age`, `gender`, `conditions`, `kidney_function`, `liver_function`, `bmi_category`, `n_drugs`, `drug_1`, `drug_2`

### Holdout Evaluation

All results use `random_state=42`, stratified 80/20 train/test split, and weighted precision/recall/F1.

| Feature group | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Drug-pair-only | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Patient-features-only | 0.6357 | 0.7063 | 0.6357 | 0.6636 |
| Full feature model | 0.9976 | 0.9976 | 0.9976 | 0.9976 |

Full model confusion matrix, labels ordered as `Mild`, `Moderate`, `Severe`:

```text
[[ 46   0   0]
 [  0  64   0]
 [  0   1 298]]
```

### Cross-Validation

Stratified 5-fold cross-validation for the full feature model:

| Metric | Mean | Std |
| --- | ---: | ---: |
| Accuracy | 0.9946 | 0.0036 |
| Precision weighted | 0.9949 | 0.0034 |
| Recall weighted | 0.9946 | 0.0036 |
| F1 weighted | 0.9947 | 0.0036 |

### Leakage and Synthetic-Data Limitations

- The drug-pair-only model scored 100% on the holdout split.
- There are 16 directed drug pairs and all 16 map to exactly one severity.
- There are 8 canonical unordered drug pairs and all 8 map to exactly one severity.
- This means drug pairs strongly determine severity in the current synthetic dataset.
- The 99.76% full-model holdout accuracy can be presented only as internal synthetic-dataset performance.
- It should not be described as clinical validation, medical accuracy, or real-world safety performance.

## API Validation

`POST /ml/risk-predict` accepts:

- `age`
- `gender`
- `conditions`
- `kidney_function`
- `liver_function`
- `bmi_category`
- `n_drugs`
- `drug_1`
- `drug_2`

It returns:

- `risk_level`
- `confidence`
- `probabilities`

Validated with five supported profiles. All returned HTTP 200, probability sums were approximately 1.0, confidence values were between 0 and 1, and `risk_level` matched the highest probability class.

## Frontend Integration

Checked `frontend/src/pages/DrugInteraction/DrugInteraction.jsx`.

- Patient fields are collected.
- Medicine 1 and Medicine 2 are collected.
- Existing Neo4j interaction checking remains in place.
- `predictRisk(...)` is called after the Neo4j interaction check.
- ML result is rendered separately from the Neo4j interaction result.
- `InteractionGraph` remains intact.
- Display includes risk level, confidence, and Mild/Moderate/Severe probabilities.
- New checks clear stale ML results.
- ML errors are isolated so a successful Neo4j interaction result can still be shown.
- Missing/invalid age and invalid current-medicine counts are blocked before the ML request.

## Output Safety Checks

The prediction service validates model output before returning it:

- `risk_level` must be present in the probability map.
- `confidence` must be between 0 and 1.
- Every probability must be between 0 and 1.
- Probabilities must sum approximately to 1.
- `risk_level` must match the highest probability class.

## Remaining Patient-Risk ML Work

- Consider redesigning the patient-risk evaluation with pair-level grouped splits if the project needs a stronger demonstration than repeated-pair memorization.
- Do not describe current results as clinical validation or real-world medical accuracy.
