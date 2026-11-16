# multilingual-medication-safety-system
Multilingual Voice-Assisted Medication Information and Safety Monitoring System

See the [current implementation and verification record](IMPLEMENTATION_REVIEW.md)
for the patient/doctor/admin workflow, share-code consent and measured test results.
For presentation setup, see the [three-role demo walkthrough](docs/DEMO_WALKTHROUGH.md)
and [human content-review handoff](docs/CONTENT_REVIEW.md). Demo credentials are
generated locally by `tools/seed_demo.py` and must never be committed or shared.
See [deployment prerequisites](docs/DEPLOYMENT.md) for trusted-proxy settings,
account-security gaps and release/licensing boundaries.
The [DDInter ML model](ml/DDINTER_MODEL.md) and older synthetic-patient model
remain research artifacts; their panels are hidden from the doctor dashboard.
The normal interaction checker shows recorded evidence and explicit coverage.

The active English catalog covers **100 medicines across 10 diseases**. Kannada
and Tulu each cover **100 medicines across 10 diseases**. Search, voice/OCR
matching, patient disease selection, doctor references and disease protocols
use the language-specific catalog in `datasets/`.

After editing the three maintained CSVs in `datasets/`, run
`python tools/datasets/sync_datasets.py` to validate them and refresh
compatibility copies, relationship tables and ML preparation exports. Restart
the backend to clear cached datasets; use `python -m neo4j.load_data --apply --sync` to reconcile
an available Neo4j database. Translations and synthetic patient training data
are maintained separately. Expanding the catalog does not train or validate the
experimental risk model for the added medicines. Older dated reports describe
their original scope.

Default dataset validation rejects the 11 currently missing Tulu drug classes.
For an explicitly incomplete demo synchronization, add `--allow-incomplete`;
this preserves and reports missing content instead of inventing translations.
The clean-install tested Windows interpreter is `.venv-review/Scripts/python.exe`;
the older `.venv` points to a removed Python installation.

## Run locally

Use Python 3.13 and Node.js with npm. Copy `.env.example` to `.env` and
`frontend/.env.example` to `frontend/.env`, then configure your own credentials.
Do not commit environment files or Firebase service-account keys.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-test.txt
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

Open http://localhost:5173. MongoDB connectivity is required for account and
patient workflows. Set `FIREBASE_SERVICE_ACCOUNT_FILE` to a local service-account
JSON path for reminders. Google login needs a configured OAuth client with the
frontend origin authorized. A real account/device is needed to validate Google
sign-in and notification delivery end to end.

Neo4j can be populated with `python neo4j/load_data.py --apply` after starting
the configured database. Graph views use the local dataset fallback when Neo4j
is unavailable; that fallback is not proof that the live database is healthy.

## Data and model scope

The Kannada and Tulu CSVs are user-maintained sources. Run
`python tools/datasets/sync_datasets.py` after editing them and restart the backend.
Tulu currently has 11 blank optional drug-class fields, recorded in the export
manifest. Do not invent translations to fill those cells. The old 30-drug
generators and workbook were removed from the active tree.

The [ML preparation guide](datasets/ML_README.md) explains the synthetic patient
data. The [DDInter model guide](ml/DDINTER_MODEL.md) documents the separate
external-label model, evaluation, 76/100 medicine coverage and abstention rules.
DDInter data and derived exports retain their CC BY-NC-SA 4.0 noncommercial
academic-use terms; see `datasets/external/ddinter/provenance.json`.

## Verify

```powershell
.venv/Scripts/python.exe -m pytest tests -q
.venv/Scripts/python.exe tools/diagnose_backend.py
.venv/Scripts/python.exe tools/verify_patient_environment.py
```

Run `npm run lint` and `npm run build` in `frontend/`. Browser checks in `tests/`
require both servers, Playwright and Microsoft Edge. The patient end-to-end
check creates disposable records and cleans them up. Credentials, local
recovery archives, caches and installed dependencies are excluded from Git.
