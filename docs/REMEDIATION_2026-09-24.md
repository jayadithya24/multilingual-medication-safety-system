# Integration remediation — 24 September 2026

This follow-up supersedes the Neo4j authentication, loader, interaction lookup and expired-token findings in PROJECT_REVIEW_2026-09-24.md. It does not certify clinical suitability or claim that all possible defects have been eliminated.

## Resolved and verified

- Corrected the local database username, authenticated successfully, and restarted the backend. No credentials are included in this commit.
- Replaced the incompatible importer with a shared dataset graph, stable node identifiers, individual schema statements, bound-endpoint MERGE relationships and multilingual properties. It does not delete existing data. Its verification fails if the database contains unexpected nodes, edges, duplicate edges or different severities.
- Imported twice and verified exactly 212 nodes (30 drugs, 3 diseases, 179 side effects) and 359 relationships (30 TREATS, 321 CAUSES, 8 unique INTERACTS_WITH pairs). The second import created no duplicates. This verifies agreement with the dataset, not medical correctness of the dataset.
- Running API explicitly reports source `neo4j`. Live checks cover endpoint integrity, reverse-pair consistency, conflict metadata, reference interactions and a Neo4j-backed interaction lookup.
- Reconciled reverse interaction rows. Ibuprofen–Methotrexate preserves both Moderate and Severe source ratings and displays Review required. No clinical rating was invented to settle the conflict. Removed partial-name interaction matching, fabricated default severity and generic management advice. Unavailable data returns HTTP 503 instead of a negative interaction result.
- Drug Reference now lists actual interaction records: Celecoxib has six recorded partners. The focused graph remains limited to medicines represented in the graph dataset.
- Closed leaked Neo4j drivers in detail/disease lookups and read interactions in both directions.
- Notification logout clears local registration state even if Firebase token revocation fails. Firebase dry-run accepted one current token and explicitly rejected one unregistered token; the rejected token alone was removed. No notification was sent during validation.
- Doctor approval atomically claims the request before creating an account, preventing a concurrent rejection. Account creation is idempotent and tagged with its request; interrupted approvals remain visible with Complete approval. Retrying completes the status update without duplicating the account. A unique registration-number index prevents two accounts sharing a registration number. Tests simulate interruption after account creation and verify recovery, rejection boundaries and existing-account protection.

## Validation

- Full backend suite: 100 tests and 9 subtests passed; dependency deprecation warnings remain.
- Frontend lint and production build passed.
- Admin, doctor, patient layout, scan workflow and focused graph browser checks passed. Dashboard workflow fixtures are synthetic; focused graphs use real APIs.
- Live voice checks passed all six upload/record scenarios with English, Kannada and Tulu response modes, using a synthetic English medicine-name audio sample and real backend transcription/audio playback.
- MongoDB connection, Firebase configuration alignment and all 30 medicine searches in each of three languages passed.

## Remaining limits

- Clinical review is still required for source conflicts, missing per-pair citations and limited interaction coverage. Ratings are marked as dataset records, not independently validated clinical conclusions.
- Physical-device notification delivery, physical microphone behavior and native Tulu pronunciation remain untested at the user's request. Tulu text currently uses Kannada speech synthesis; browser playback does not establish native pronunciation or voice identity.
- Approval recovery uses an explicit retryable state rather than a multi-document transaction. A database outage can leave an approving request in the queue until an administrator completes it.
- Historical credential rotation remains an account-owner task; this change neither publishes current credentials nor rotates external service credentials or rewrites Git history.
- Existing graph databases with legacy records require an explicit migration review; the new importer detects mismatches rather than silently deleting them.

## Reproduce

From the repository root:

```powershell
rtk proxy .venv/Scripts/python.exe -m neo4j.load_data
rtk proxy .venv/Scripts/python.exe -m neo4j.load_data --apply
rtk proxy .venv/Scripts/python.exe tools/verify_graph_api.py
rtk proxy .venv/Scripts/python.exe tools/audit_neo4j.py
rtk proxy .venv/Scripts/python.exe tools/verify_patient_environment.py
rtk proxy .venv/Scripts/python.exe tests/voice_browser_check.py
rtk proxy .venv/Scripts/python.exe -m pytest -q
```

The loader defaults to a dry run. The environment audit defaults to read-only; `--prune-unregistered` removes only tokens explicitly rejected as unregistered by Firebase dry-run.
