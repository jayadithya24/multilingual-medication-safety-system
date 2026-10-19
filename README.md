# multilingual-medication-safety-system
Multilingual Voice-Assisted Medication Information and Safety Monitoring System

The [DDInter ML model](ml/DDINTER_MODEL.md) adds independently evaluated
drug-pair severity classification from external documented labels, alongside
the existing evidence checker and older synthetic-patient demonstration.

The active English catalog covers **100 medicines across 10 diseases**. Kannada
and Tulu each cover **100 medicines across 10 diseases**. Search, voice/OCR
matching, patient disease selection, doctor references and disease protocols
use the language-specific catalog in `datasets/`.

After editing `datasets/english_master_records.json`, run
`python datasets/update_english_scope.py` to refresh the English master,
compatibility copies, relationship tables and ML preparation exports. Restart
the backend to clear cached datasets; use `python neo4j/load_data.py --apply` to refresh
an available Neo4j database. Translations and synthetic patient training data
are maintained separately. Expanding the catalog does not train or validate the
experimental risk model for the added medicines. Older dated reports describe
their original scope.

## Run locally

Use Python 3.11 and Node.js with npm. Copy `.env.example` to `.env` and
`frontend/.env.example` to `frontend/.env`, then configure your own credentials.
Do not commit environment files or Firebase service-account keys.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-test.txt
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
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
`python datasets/prepare_ml_data.py` after editing them and restart the backend.
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
