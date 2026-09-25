# Interaction evidence and class mappings

Updated 24 September 2026. The checker describes risks from medicines taken by
the same person. Shared diseases and individual side effects never generate a
drug-pair interaction.

`datasets/interaction_evidence.json` contains seven narrowly scoped rules with
DailyMed prescribing-label references, explicit medicine membership, effects,
and monitoring summaries. The resolver retains exact CSV ratings first, then
looks up class rows only for explicitly mapped medicines. It does not expand
all class names or assume every drug in a disease category interacts.

The checker, drug reference, CSV fallback graph, and Neo4j import share the
resolver. The supported graph now contains 27 unordered interaction pairs,
including the original eight pairs; the original CSV remains unchanged.

## Severity provenance

Prescribing labels substantiate reaction descriptions, not the project's
Mild/Moderate/Severe taxonomy. Existing labels are displayed as unvalidated
dataset ratings. New evidence without a dataset rating returns `Not graded`
and requires review. No clinical severity was invented.

- Acarbose with Chlorthalidone or Hydrochlorothiazide: a cited diuretic-class
  warning about glucose control; no source severity assigned.
- NSAIDs with mapped ACE inhibitors/ARBs: recorded class ratings plus cited
  blood-pressure/kidney effects; mappings retain original CSV row provenance.
- Ibuprofen–Methotrexate: both original Moderate and Severe ratings retained;
  Review required.
- Telmisartan–Ramipril: original Mild rating retained for audit, but the
  result requires review because the label advises avoiding dual blockade.

## Scope and verification

This is a limited reference-based checker, not individualized risk prediction.
Dose, renal function, treatment duration, and other patient factors are not
inputs. Unmapped pairs still report no recorded interaction, not safety.
Translations and clinical severity adjudication are not established by these
changes. The source links and mapping basis are displayed with each result.

Run the interaction integrity tests, frontend lint/build, and browser check
`tests/interaction_evidence_browser_check.py`. After importing with
`python -m neo4j.load_data --apply`, `tools/verify_graph_api.py` verifies the live
API source and pair integrity. The import uses MERGE without deleting records.
