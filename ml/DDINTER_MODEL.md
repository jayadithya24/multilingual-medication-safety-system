# DDInter severity research model

This model is separate from the older synthetic-patient Random Forest. It
learns externally recorded drug-pair severity labels from the official
[DDInter downloads](https://ddinter.scbdd.com/download/).
DDInter data are licensed **CC BY-NC-SA 4.0**, for noncommercial academic use;
retain attribution and share-alike terms for redistributed derived data.
See [provider terms](https://ddinter.scbdd.com/terms/) and the
[original paper](https://doi.org/10.1093/nar/gkab880).

## Reproduce

From the repository root, using the project's Python environment:

```powershell
python ml/download_ddinter.py
python ml/train_ddinter_model.py
```

Official raw files and SHA-256 provenance are in `datasets/external/ddinter/`.
The eight therapeutic-area downloads overlap: reversed and repeated pairs
are deduplicated before splitting. Conflicting pairs, self-pairs and ungraded
labels are excluded. `deduplicated_pairs.csv` records the exact split.

The trainer compares balanced logistic regression and multinomial naive Bayes
against a majority baseline. Features are two unordered binary drug identity
indicators. Neither interaction descriptions nor severity labels are inputs.
Drug identity features capture statistical associations, not biological
mechanisms. A fixed 70/15/15 train/validation/test split keeps each unordered
pair in only one partition. Model selection uses validation macro-F1; test
results do not select the winner. The saved model is not refitted on held-out
data. Drugs may appear across splits, so this does not measure unseen-drug
generalization or prospective clinical outcomes.

## Results and use

The complete metrics, confusion matrices, catalog-only held-out evaluation,
coverage and limitations are in `ml/models/ddinter_evaluation.json`.
Initial selected model: logistic regression, test accuracy 79.04%, macro-F1
0.694. Minor-label precision is only about 35%; aggregate accuracy must not
be presented as clinical reliability. Exact-name coverage is 76/100 catalog
medicines; no unverified salt, synonym or combination-product mappings are used.
On 83 held-out pairs involving supported catalog medicines, accuracy is 77.11%
and macro-F1 is 0.616. This smaller subset is more relevant to this app and
does not support a claim of reliable clinical severity prediction.

`POST /ml/ddinter/predict` accepts `drug1` and `drug2`.
`GET /ml/ddinter/model-info` reports evaluation and coverage.
The doctor interaction page displays a separate **ML prediction trained on
DDInter** panel. Source labels remain **Minor / Moderate / Major** and are not
silently relabeled to the older project scale. The recorded source label is
shown separately from the algorithm's output, including training membership.

The model abstains for unsupported medicines, pairs without a graded source
record, or maximum scores below 0.70. The threshold is a research display rule,
not a clinically validated safety threshold. Scores are not calibrated harm
probabilities. The data contain documented interactions, not validated
non-interacting pairs, so this model cannot establish interaction existence or
safety for an unknown pair. It uses no patient factors and cannot predict
patient-specific risk. Existing evidence checks remain available.

The 100-medicine, 10-disease catalog remains accessible in all three languages;
that reference scope is distinct from the trained model's narrower coverage.
