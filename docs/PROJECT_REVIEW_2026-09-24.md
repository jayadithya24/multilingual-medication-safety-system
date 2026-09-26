# Project review — 24 September 2026

Follow-up: [integration remediation](REMEDIATION_2026-09-24.md) resolves the Neo4j connection/import and interaction lookup findings below and records newer validation results. The remaining sections describe the original review snapshot.

Scope: patient, doctor and administrator dashboards; routing and role boundaries; account approval, consent, medication schedules and history; graph/reference/interaction integration; Google/Firebase, OCR/voice integration paths; test isolation and publication hygiene. Includes the working changes accumulated on `dev` since `8dce9d0`.

## Corrections included

- Admin doctor approval creates the user without the conflicting MongoDB `created_at` update.
- Database import requires an administrator, not merely an authenticated account.
- Removed hardcoded demo login accounts and automatic doctor login. Admin and doctor sign-in now check the returned role before persisting a session.
- Removed fabricated patient-directory and medication-history responses, including the `PAT-DEMO` consent bypass.
- Explicit test mode selects mongomock before any real database connection. Normal MongoDB failures no longer silently store writes in a temporary in-memory database.
- Doctor Reports now presents medication-taking records with accurate metrics, timestamps, patient filtering, refresh/retry, a consent-aware empty state and readable contrast. It does not claim to perform safety analysis. New medication history entries include `TAKEN` status.
- Admin queue controls prevent repeated decisions while a review is in flight; its status card describes queue loading rather than asserting overall service health.
- Unified focused SVG graphs across doctor views, dropdown-first medicine selection, pagination, keyboard selection, highlighted direct neighbors/arrows and dimming of unrelated connections.
- Graph responses and UI identify Neo4j versus CSV fallback. Side-effect IDs are namespaced and case-normalized so they cannot merge with disease IDs or create case-only duplicates. Missing Neo4j severity is reported as Unknown rather than invented as Moderate.
- Preserved the accumulated patient navigation/layout, Google button, role guard and report-route improvements.
- Local environment files, generated Firebase configuration, dependencies, uploads and screenshots are excluded from publication.

## Validation

- Full backend suite: 90 tests and 9 subtests passed. Includes approval/login, consent, Google authentication, reminders, voice/transcription, loaders and graph filtering/identity failures. Deprecation warnings remain.
- Frontend ESLint and production build passed.
- Patient browser checks: five sections at desktop/mobile widths, session expiry, navigation, OCR review, corrected-dose explicit save, speech request, Tulu request and guest restrictions. API payloads are mocked for these tests.
- Doctor browser checks: consent restrictions, Reports empty/populated states, timestamps, mobile containment and guest routing. Graph checks use real graph APIs and cover selection, highlighting, pagination, filtering, reference and pair views. The interaction summary is mocked in the graph browser check.
- Admin browser checks: approval failure/retry, approval, rejection, empty queue, mobile layout and wrong-role redirects, using synthetic requests.
- Live read-only audit: MongoDB connects; Firebase Admin initializes and matches frontend configuration. FCM dry-run accepts one token and rejects one expired token. No real notification was sent. All 30 medicines are searchable in English, Kannada and Tulu.

## Remaining limits and findings

1. **Neo4j authentication remains blocked.** The local database is reachable, but configured credentials return `AuthError`. Live Cypher execution/import correctness has not been established. The running graph uses CSV fallback; update local credentials and follow `NEO4J_VALIDATION.md`.
2. **Clinical evidence is not certified.** The source contains conflicting Ibuprofen–Methotrexate severities, limited in-scope interaction coverage and missing per-pair citations. CSV interaction lookup still has legacy partial-name matching/generic prose. These require a separate data and clinical validation pass before clinical use.
3. **Neo4j import/schema work remains.** The old loader's field names and relationship names do not consistently match the current CSV/readers. Legacy scripts include destructive database reset behavior and were not run. This review does not certify those imports.
4. **Notification/device checks remain.** One expired token needs registration renewal. End-to-end delivery on a physical device, native Tulu speech quality and physical microphone/speaker behavior were not validated by these checks.
5. **Approval concurrency is not transactional.** Concurrent administrators or a database interruption between account creation and request status update can require reconciliation. UI duplicate-click prevention does not make the two writes atomic.
6. **Historical credentials are outside this push.** Existing documentation calls for rotation of previously exposed credentials. This review excludes current secret values from new changes; it does not rewrite repository history or rotate external accounts.

The earlier audit JSON and dated audit documents are historical snapshots; their identity/count findings predate the side-effect namespace correction in this review.

## Reproduce

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest tests -q
rtk proxy .venv/Scripts/python.exe tests/patient_layout_browser_check.py
rtk proxy .venv/Scripts/python.exe tests/scan_page_browser_check.py
rtk proxy .venv/Scripts/python.exe tests/doctor_pages_browser_check.py
rtk proxy .venv/Scripts/python.exe tests/admin_dashboard_browser_check.py
rtk proxy .venv/Scripts/python.exe tests/focused_graph_browser_check.py
rtk proxy .venv/Scripts/python.exe tools/verify_patient_environment.py
```

Run `rtk proxy npm run lint` and `rtk proxy npm run build` from `frontend`. Browser checks require frontend/backend servers on ports 5173/8000 and Playwright with Edge. Test screenshots are written to ignored `artifacts/`.
