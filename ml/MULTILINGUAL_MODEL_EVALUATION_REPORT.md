# Multilingual Intent Classification Model - Evaluation Report

## 1. Overview

The Multilingual Intent Classification Model is designed to identify the intent of medication-related user queries in English, Kannada, and Tulu.

The model uses:

- Character-level TF-IDF with character word-boundary n-grams
- N-gram range: 2-5
- Logistic Regression
- Balanced class weights
- Random state: 42

The model predicts seven medication-related intents:

1. medicine_info
2. uses
3. side_effects
4. contraindications
5. warnings
6. interactions
7. dosage

The V2 model was trained using the natural multilingual query dataset.

---

## 2. Dataset

The V2 training dataset contains:

- 336 total queries
- 4 medicines
- 3 languages
- 7 intents
- 4 natural-language templates per intent

Languages:

- English
- Kannada
- Tulu

The dataset was split into:

- Training: 268 samples
- Validation: 34 samples
- Test: 34 samples

The split was stratified using language and intent.

---

## 3. V2 Standard Evaluation

The V2 model achieved:

- Validation Accuracy: 100%
- Test Accuracy: 100%

The standard test set contained 34 samples.

The model achieved 100% accuracy for English, Kannada, and Tulu on this test set.

---

## 4. Unseen Evaluation - Test 1

A separate manually constructed unseen evaluation set containing 42 queries was used.

Results:

| Language | Correct | Total | Accuracy |
|----------|---------|-------|----------|
| English | 13 | 14 | 92.86% |
| Kannada | 14 | 14 | 100.00% |
| Tulu | 14 | 14 | 100.00% |
| Overall | 41 | 42 | 97.62% |

One prediction was incorrect.

Expected intent:

`medicine_info`

Predicted intent:

`uses`

Query:

"Can you explain what Metformin is used for?"

This query has an ambiguous intent boundary because the phrase "used for" strongly indicates the `uses` intent.

---

## 5. Unseen Evaluation - Test 2

A second independent unseen evaluation set containing 42 queries was evaluated.

Results:

| Language | Correct | Total | Accuracy |
|----------|---------|-------|----------|
| English | 13 | 14 | 92.86% |
| Kannada | 14 | 14 | 100.00% |
| Tulu | 14 | 14 | 100.00% |
| Overall | 41 | 42 | 97.62% |

One prediction was incorrect.

Expected intent:

`uses`

Predicted intent:

`contraindications`

Query:

"Why might someone take Ibuprofen?"

This query is relatively ambiguous because it asks for a reason for taking the medicine without explicitly stating whether the user is asking about its medical uses.

---

## 6. V1 vs V2

The V2 model was developed to improve generalization beyond the original template-based dataset.

### Unseen Test 1

| Model | Accuracy |
|-------|----------|
| V1 | 76.19% |
| V2 | 97.62% |

### Language-level performance

The V2 model achieved:

- English: 92.86%
- Kannada: 100%
- Tulu: 100%

The unseen evaluation indicates a substantial improvement over the original V1 model.

---

## 7. Model Architecture

The current pipeline is:

User Query
    |
    v
Text / Speech-to-Text
    |
    v
TF-IDF Character N-gram Vectorization
    |
    v
Logistic Regression Classifier
    |
    v
Intent
    |
    v
Medicine Information Retrieval
    |
    v
Localized Response

The classifier identifies the user's intent. It does not generate medical information.

Medication information should be retrieved from the project's existing medication database or knowledge graph.

---

## 8. Limitations

The evaluation results should not be interpreted as clinical or real-world accuracy.

Important limitations include:

- The V2 dataset is relatively small.
- The unseen evaluation sets contain only 42 queries each.
- The evaluation queries were manually constructed.
- Tulu examples require further linguistic validation.
- The dataset does not represent all possible ways users may ask medication-related questions.
- The model has not been evaluated on a large independently collected real-world dataset.
- The model predicts intent only; it does not provide clinical recommendations.
- High accuracy on these datasets does not establish clinical safety.

---

## 9. Conclusion

The V2 multilingual intent classifier demonstrated strong performance on the available validation, test, and unseen evaluation datasets.

It achieved 97.62% accuracy on both unseen evaluation sets, with 100% accuracy for Kannada and Tulu in both evaluations.

The results support using the V2 model as an experimental intent-classification component of the multilingual medication safety system.

Further evaluation using larger, independently collected multilingual user queries would be required before making claims about real-world or clinical performance.