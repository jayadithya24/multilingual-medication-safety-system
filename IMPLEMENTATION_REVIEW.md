# Implementation and verification record

Updated 24 October 2026 after local HTTPS reverse-proxy verification. This describes the current
code and observed checks. It is not a claim of clinical validation, regulatory
compliance, or completion of every proposed pilot feature. The earlier editable
academic report is not present in this checkout; this record supplies the
verified material for its next revision.

## Security, visibility and speech follow-up

- Fixed the global dark color scheme/pale text inheritance on light pages.
  The doctor sharing form has explicit input, button, focus and disabled styles;
  empty-state text is readable. Main-page and patient-history screenshots were
  inspected, with a mobile-width/no-overflow check. The visual-only test stubs
  doctor identity; the separate three-role acceptance test uses real accounts.
- Kannada and Tulu retain **kn-IN-SapnaNeural**, the explicitly selected Indian
  female Kannada voice. Added playback speeds (0.8, 0.9, 1.0), defaulting to 0.9
  for these languages while preserving pitch. This is a pacing improvement,
  not a newly trained pronunciation model. Tulu's Kannada-synthesis limitation
  is now displayed next to playback. No male or foreign browser fallback is used.
- Public OCR/voice requests are limited to 20/minute per verified user or anonymous
  client address. Other public categories allow 120/minute per verified user or
  300/minute per anonymous address, with separate catalog, graph, interaction,
  TTS and health budgets. Upload bodies
  are capped at 10 MiB including multipart overhead; all other bodies at 64 KiB.
  Limits cover actual received bytes even without Content-Length. Public routes
  remain public under these bounds; sign-in was not added to those routes.
  Only server-validated, unexpired sessions get user quotas. Local development defaults
  to per-process counters; production requires shared MongoDB counters, failing
  closed if counters are unavailable. Trusted reverse-proxy configuration is
  still a deployment responsibility (see docs/DEPLOYMENT.md).
- Sharing-code redemption has a separate MongoDB-backed 10-attempt/minute limit
  per authenticated doctor. Forwarded IP headers cannot bypass the peer limiter.
- Targeted denied medication/history/report access is logged for existing
  patients. Doctors cannot read/edit/delete the patient log. Ownership, expired
  and revoked grants are tested on each targeted route; aggregate lists/history
  return only permitted records (an empty 200 response when none are permitted).
- Patients can explicitly renew an approved grant for another seven days;
  renewal is logged. MongoDB UTC timestamps now carry an explicit timezone in
  consent/log/report responses so browser expiry display is correct.
- Browser authentication now uses opaque 256-bit random HttpOnly, SameSite=Strict
  session cookies. MongoDB stores only SHA-256 hashes and enforces a sliding
  30-minute idle expiry and eight-hour absolute maximum on every request
  (independent of TTL cleanup). Background identity/health polls do not extend
  sessions. Logout revokes
  the server session. Cookies are Secure on HTTPS; HTTP loopback development is
  the only exception, disabled when ENVIRONMENT=production. Production must use
  HTTPS and explicit BROWSER_ORIGINS. Cookie writes and session creation/logout
  require an exact allowed Origin, including its port, to prevent CSRF.
  No refresh endpoint is provided: sign in again after expiry. Browser storage
  contains only non-secret per-tab UI hints; old localStorage JWTs are removed.
  CORS permits credentials only for explicit configured origins.
- Legacy bearer login/register endpoints and bearer authentication are removed.
  Google session login returns the user internally without minting a JWT.
  Tests and demo tools use cookie sessions. Password attempts additionally have
  shared MongoDB counters keyed by a normalized account and client-address hash
  (eight per fifteen minutes, cleared on successful login). There is no global
  username lockout; distributed attacks still need monitoring and MFA.
- Auth POSTs have a separate 60/minute peer-IP budget. Public OCR, voice and
  interaction routes retain the documented per-IP limits, with parametrized
  route tests. `/ml/*` is **disabled by default**; research scripts/code remain.
  ENABLE_RESEARCH_ML_API=true is an explicit research-only opt-in outside
  production; production always disables these APIs.
- Validation responses omit input/ctx values; OCR and Firebase errors use generic
  messages. Frontend error logging omits Axios objects, which can carry request
  credentials. Uvicorn access logs omit query strings. No tracked .env/service
  account/private-key files were found in the filename/JSON/PEM inventory;
  ignore rules cover local envs, Firebase keys, uploads and test artifacts.
  This is a targeted check, not a historical secret scanner or penetration test.
- A read-only graph monitor runs at startup and every five minutes. It compares
  graph nodes, relationships, severity and reference properties to the CSV-derived
  graph. `/health` exposes only running status. Admin-only `/admin/health`
  provides service details, while `/doctor/reference-status` provides graph
  status to signed-in doctors. The doctor layout
  displays drift/outage notices. It never silently overwrites the graph.
- Real patient/doctor/admin browser acceptance was rerun on 20 October and
  passed with no browser JavaScript errors, including cookie privacy, regimen
  coverage, consent, reports and revocation. The separate patient test passed
  profile, schedule, dose records, report download and logout against real MongoDB.
  The visual-only test (stubbed identity) passed contrast and mobile overflow.
- Latest health (20 October follow-up): backend running, Firebase Admin
  initialized, reminder worker running, and Neo4j **verified**. The instance was
  already running when work resumed. An explicit backed-up synchronization and
  independent comparison verified 304 nodes and 799 relationships. The live
  periodic drift check also reports verified. CSV fallback remains available.
- Physical-phone scheduled delivery remains **unverified**. The user confirmed
  the app has not been deployed and cannot yet be opened on their phone. The
  next test requires an HTTPS deployment reachable by that phone, notifications
  enabled for its test account, and confirmation of receipt of a scheduled test.
- Latest complete regression: **239 tests and 9 subtests passed**. Deprecation warnings
  remain; these results do not imply every external service has been verified.

## Regimen review and dependency audit (20 October)

Opening an approved patient's History & Drugs now includes all active saved
medicines, reference-catalog coverage, matched pairs ordered by review/severity,
existing prescribing-reference links (or explicit dataset-only provenance), and
28 days of patient-reported records. Unlisted names are displayed as unchecked;
absence of a pair record does not establish safety. No ML or new clinical rule
is used, and no brand-name guessing is introduced.

Existing dose logs do not identify a unique scheduled dose. Accordingly, the
review shows **scheduled days with at least one taken record**, unconfirmed days,
and raw event counts, not a percentage of individual doses taken. Duplicate
clicks cannot increase confirmed-day counts. Creation/deletion times and the
configured reminder timezone bound the window; legacy missing times/dates are
Unknown. Unconfirmed does not mean missed. These limitations are visible in UI.

`pip-audit` on the working .venv-dataset runtime initially reported three advisory
entries across python-jose/ecdsa (including a duplicate ecdsa advisory). After
replacing the JWT dependency, it reports **no known vulnerabilities**. This audits
the installed runtime, not a fresh resolution of every historical requirements
file. Frontend npm audit initially reported 12 affected packages (11 high, one
moderate); compatible updates and a pinned @grpc/grpc-js 1.14.6 override resolved
them without npm's suggested Firebase downgrade. Root npm audit also reports
zero. These are advisory snapshots, not guarantees of absence of vulnerabilities.
Frontend lint/build pass; the existing large-bundle warning remains.

## Patient, doctor and admin workflow

1. Patients register and sign in, maintain their profile, look up medicines,
   and save medication schedules and patient-reported dose-taking records.
2. Doctors submit an account application. Admin approval enables doctor login;
   rejection does not create a doctor account. This is administrative review,
   not automated verification against a medical register.
3. Doctors see only patients with active, unexpired approved consent. The
   previous directory of all registered patient identities has been removed.
4. In My Medicines, a patient creates a single-use sharing code. Only its SHA-256
   hash is stored. It expires in 10 minutes; generating another replaces it.
5. A signed-in doctor enters the code to request access. Code redemption alone
   does not grant access. The patient explicitly accepts or rejects the request.
   Pending requests expire after 24 hours.
6. Approval grants access for seven days to identity/profile fields used in
   reports, medication schedules, dose history and reports. This is one fixed,
   disclosed scope, not a menu of independently selectable permissions.
7. Patients can revoke access. Revocation invalidates outstanding requests and
   grants for that doctor/patient pair. All medication and report endpoints and
   the doctor's aggregate history enforce active consent. Old grants without
   an expiry fail closed and require fresh consent.
8. Patients can inspect the latest 200 access/decision events. Doctor list reads,
   medication/history reads and report generation are logged. Revocation blocks
   future retrieval but cannot recall copies already viewed, downloaded or printed.
9. Patients and approved doctors can generate reports from saved profile,
   schedules and dose history, download HTML, or print/save PDF in the browser.
   Doctor reports include the consent grant timestamp, expiry and scope.
   These are patient-entered medication records, not signed new prescriptions.

## UI and interaction corrections

- Removed ineffective Settings switches, the static Online label and unavailable
  admin statistics. Settings now displays account/workspace information.
- Renamed Analysis History to Medication History; it shows dose-taking history,
  not persisted interaction analyses.
- Hidden both the synthetic Random Forest and DDInter prediction panels from
  the doctor interaction page. Their code, models and evaluation remain research
  artifacts. Research APIs were not removed or promoted as clinical services.
- Pair and multi-drug API responses include catalog coverage, unsupported names,
  total pairs and pairs with recorded evidence. The UI displays coverage for
  its two selected medicines and explicitly says it does not cover a complete
  patient regimen. Multi-drug requests are bounded to 50 entries.
- Catalog membership is not evidence that every possible pair is characterized.
  Missing interaction records do not establish safety. Unlisted medicines are
  excluded from checks and identified as not checked.
- The normal checker retains documented project Mild/Moderate/Severe labels,
  provenance, conflict/review status and ungraded evidence. DDInter's original
  Minor/Moderate/Major vocabulary is retained in research; no silent remapping.

## Data and graph

All three master CSVs retain 100 medicines and 10 categories, joined by stable
drug IDs. Synchronization preserves the master-file hashes and refreshes derived
tables and application compatibility copies. Current derived counts: 100
drug/disease records, 669 side-effect records, and 157 interaction rows. Rows
include external substances/classes and are not 157 distinct in-catalog pairs.

The Tulu master still has **11 missing drug_class values**. They have not been
filled with guessed translations. Default validation now fails on these missing
required fields before producing outputs. An explicit `--allow-incomplete`
option permits demo synchronization and prints missing-value counts. It does
not certify content quality. The Kaggle exporter remains an explicitly
non-publishable draft with quality/source review files.

The **70 repeated generic English interaction narratives** remain a content
review issue. These narratives are fields of medicine master records, distinct
from the separate drug-pair relationship table. They cannot be used to invent
specific pair evidence. Native-language/pharmacist review and source permissions
remain necessary before publication or clinical use.

Neo4j was backed up and synchronized, then independently verified after dataset
regeneration: **304 nodes and 799 relationships** matched the expected current
CSV graph. This includes 100 Drug nodes and 10 Disease nodes. The sync replaces
only application reference relationship types and removes obsolete isolated
application nodes; it is not a blanket database wipe. Backups are in ignored
`artifacts/neo4j-before-sync-*.json`.

After future master changes, synchronize derived files, reconcile Neo4j with
`python -m neo4j.load_data --apply --sync`, and restart the backend to clear
caches. Synchronization is explicit, not an automatic filesystem watcher.

## ML retained as research

The synthetic-patient Random Forest experiment is preserved, with its original
approximately 30-medicine/three-condition training scope and pair-identity
limitations. The 100-medicine reference catalog does not broaden that training
evidence. Random-split accuracy is not clinical reliability.

The DDInter logistic-regression experiment is also preserved: recorded overall
held-out accuracy 79.04%, macro-F1 0.694; catalog subset 83 held-out pairs,
77.11% accuracy and macro-F1 0.616; exact-name coverage 76/100 catalog medicines.
These are existing evaluations, not new training in this correction pass.
See `ml/DDINTER_MODEL.md` and `ml/models/ddinter_evaluation.json` for per-class
metrics, splits and limitations. No direct DDInter product lookup was added;
source/license review remains required for any subsequent reuse plan.

## Verification performed

| Check | Environment | Result |
|---|---|---|
| `python -m pytest -q` | Isolated test environment; database tests use mongomock and service mocks as applicable | 199 passed; 9 subtests passed after security/regimen follow-up |
| Frontend lint | Local frontend | Passed |
| Frontend production build | Local frontend | Passed; existing large-chunk advisory remains |
| `tests/verify_three_role_live.py` | Real running FastAPI/Vite, configured MongoDB, headless Edge; no API stubs | Passed; no browser JavaScript errors |
| `tests/verify_backend_live.py` | Real MongoDB/API and patient browser workflow | Passed for profile, schedules, taken/removal history, report download and logout |
| Neo4j exact graph comparison | Real project instance, 20 October follow-up | 304 nodes / 799 relationships verified after backed-up sync; live drift check clean |
| Dataset synchronization | Current master CSVs, explicit demo exception | Master hashes unchanged; 100 medicines / 10 categories per language; 11 Tulu blanks reported |
| OCR startup | Restored Python runtime with cached PaddleOCR models | Reader initialized; no new prescription-accuracy evaluation |

The three-role check creates disposable test accounts, seeds only a temporary
admin (no public admin registration exists), exercises real doctor registration
and admin approval, signs in through all three portals, and tests the private
directory, code redemption, rejection, approval, report download, revocation,
access logs and coverage. Test records are removed in finally. Machine-readable
results are saved in `artifacts/three-role-live-results.json`.

Expiry, code reuse, ownership checks, legacy-grant denial and aggregate-history
filtering are covered by isolated regression tests. A parametrized matrix uses
real cookie authentication dependencies for every patient-specific doctor route,
including regimen: no token returns 401; patient role, missing, expired and
revoked consent return 403. Aggregate directory/history return empty 200 for
a doctor without consent, and 401/403 for missing/wrong-role authentication. The live browser run must not
be described as live verification of every unit-test case or every external
service. Early acceptance-script locator/landing-page assumptions were corrected;
the final complete run passed.

Firebase registration/storage and the no-device error path were exercised;
the test intentionally did not send a fake token to Firebase. Prior dry-run
validation and a running worker do **not** verify real-device scheduled delivery.
Do not report reminder delivery as passed. Google account sign-in remains
deferred/unverified. Test deprecation warnings remain; zero warnings is not claimed.

## Runtime and remaining work

### Local HTTPS proxy verification, 24 October

Prepared `docs/HTTPS_PROXY_TEST.md` and ran `tools/verify_https_proxy.py` using
portable Caddy v2.11.7, two real Uvicorn backend processes with production-mode
MongoDB counters, and a disposable database on the configured MongoDB server.
No mocks or in-memory counter substitution were used. The official Caddy archive
passed its published SHA-512 checksum and GitHub asset digest checks. The initial
download check incorrectly used SHA-256 against the SHA-512 manifest; it refused
to execute the binary until the verification algorithm was corrected.

Run `6df53f18de931ef5` passed:

- Verified TLS using a temporary certificate trusted only by the test client.
- Two separate loopback source addresses remained distinguishable across Caddy.
- Forged forwarding headers could not change the observed source or scheme.
- Direct backend requests from an untrusted source could not spoof forwarding.
- Secure/HttpOnly/Strict cookies worked across two backend processes; CSRF rejected
  missing/untrusted origins and logout revoked the session.
- Real MongoDB counters enforced quotas across both processes. Spoofing could not
  reset them, and a second client source retained its quota.
- Three signed-in identities shared the 60/minute heavy-route source ceiling;
  a fourth identity could not bypass it. No Whisper computation was invoked:
  requests intentionally omitted files and reached normal 422 validation until
  limited with 429.

Listeners were loopback-only on ports 18443, 18081 and 18082; the normal demo
servers and application database were not changed. Both test processes and Caddy
were stopped; the temporary TLS key and all test collections were removed.
dropDatabase was forbidden by the configured MongoDB account, so cleanup used
permitted collection drops. The initial run's cleanup failure was resolved and
the final complete run passed with no remaining empty test collections.

Evidence is in `artifacts/proxy-test/6df53f18de931ef5/results.json`. This pass
adds a test harness and documentation, not production feature changes. The prior
239-test regression result remains historical; it was not rerun for this
harness-only change. Python compilation and the actual proxy integration run
passed. Public DNS/certificate deployment, real firewall isolation, two physical
networks, phone delivery and real Google sign-in remain separate checks.

### Dataset propagation and abuse-control follow-up, 23 October

Ran `tools/datasets/sync_datasets.py --allow-incomplete`: all three maintained
masters remain unchanged, with 100 medicines and 10 diseases each. Derived
localized exports now include the user's Tulu spelling corrections. Eleven
Tulu classes are still blank; the explicit incomplete-content flag does not
approve them. Restarted the backend and verified the actual Tulu medicine API
returns the corrected Common Cold label. A regression test compares every
derived Tulu disease label to its current master record.

The existing project Neo4j process was reachable for the authorized live check.
Backed up and synchronized its reference data, then independently checked drift:
**304 nodes and 799 relationships verified**. This supersedes the unavailable
status recorded earlier in the day. Backend caches were cleared by restart.

Heavy routes now enforce the existing user/anonymous quota AND a shared-IP
ceiling of 60 requests/minute. Source rejection runs before session lookup.
Registration attempts share a 10/hour source cap across patient, doctor and
Google-register entrypoints; normal Google login is excluded. Tests exercise
many distinct valid accounts behind one address and counters shared across
separate middleware workers. Production uses MongoDB counters.

Cross-IP username attempts now trigger a hashed monitoring event at 32/window,
without globally locking the account. This is a monitoring hook, not deployed
alert delivery or MFA. `tools/deploy_preflight.py` exits unsuccessfully unless
production configuration is explicit; it correctly rejected the local dev
configuration. A startup banner also identifies development mode. Added an
actual doctor-registration route test with a 30-character Kannada password;
it returns 422 without echoing the submitted password.

Full regression: **239 tests and 9 subtests passed**, with 1201 warnings. The
shared imported application gets fresh in-memory rate windows between test
cases, while limits stay enabled within each case. The separate real-MongoDB
three-role browser workflow passed again with no JavaScript errors and cleaned
up its disposable records. No frontend implementation changed in this follow-up.

Refreshed the 200-row language-review handoff against the current masters.
Native-speaker/pharmacist sign-off is still unavailable, and no translations
were invented. There is no configured production reverse proxy to verify here;
the deployed proxy test and physical-phone reminder test remain pending, along
with real Google sign-in and the documented account-security/release work.

### Second archive review follow-up, 23 October

- Patient registration already rejected passwords exceeding 72 UTF-8 bytes.
  The confirmed gap was doctor registration. Both schemas now share byte-length
  validation, and the hashing helper rejects oversized values as a backstop.
  Kannada password tests cover a valid 72-byte value and a rejected 75-byte value.
- Replaced the global username attempt lock with account-and-source counters.
  Verified users behind the same NAT have independent public-route budgets;
  invalid cookies cannot obtain new quotas. Anonymous NAT sharing remains a
  deployment consideration. Middleware quota checks do not renew session expiry.
- Non-upload body limits now cover private routes too, including schedules,
  profiles and sharing requests. Tests cover declared and streamed oversized bodies.
- Repeated identical denied-access events are combined per doctor/patient/action
  in five-minute windows, alongside existing read deduplication. Consent decisions
  remain separate. The patient UI explains the distinction.
- Removed `Bash(env)` and unrestricted `Bash(python *)` from local Claude settings.
  The local settings file is ignored, untracked, and explicitly excluded from
  project packaging. Demo credentials remain ignored/untracked and absent from
  the available `git log --all` history. Existing archives are historical snapshots.
- Added `requirements.in` alongside the root lockfile and regenerated
  `requirements.txt` from it.
  Kept only `opencv-contrib-python==4.10.0.84`, required by PaddleOCR, and removed
  the competing headless distribution. A fresh `.venv-review` on Python 3.13.15
  installed 144 runtime/test packages and passed `uv pip check`. Actual HTTP OCR
  recognized Metformin in a generated image; this is an integration smoke test,
  not prescription-recognition accuracy evaluation. Cached OCR weights were used.
- Production now fails during application initialization if BROWSER_ORIGINS is
  missing or includes HTTP, wildcard, path-bearing or otherwise invalid origins.
  Development defaults remain local. CORS and cookie checks share this validation.
- Reviewed frontend intervals: VoiceSearch's timer analyzes microphone silence
  locally and sends no polling requests. Doctor reference-status polling is
  excluded from session renewal. No deployed proxy exists here, so a real trusted-
  proxy forwarding test remains a deployment prerequisite.

Verification: **233 tests and 9 subtests passed**, with 806 warnings, using the
clean environment. These unit/regression tests use mocks/mongomock. Frontend
lint/build passed; the bundle-size warning remains. The regenerated Python lock
audit reports no known vulnerabilities. Neo4j is currently unavailable, so the
21 October live graph verification below is historical, not a claim about today's
running instance. Phone delivery, real Google sign-in and human content review
remain unverified. MFA, recovery/deletion and retention work remain pending.

The separate live three-role browser test passed against real MongoDB on
23 October, without API stubs or browser JavaScript errors: doctor registration
and admin approval, cookie login, consent rejection/approval, report download,
revocation and access-log checks. Its disposable records were removed afterward.

### Archive review follow-up, 21 October

Final clean-environment regression: **220 tests and 9 subtests passed**
(`python -m pytest tests -q --disable-warnings`), with 806 warnings. A stale
assertion expecting the former consent-denial wording was corrected; the final
test also checks that nonexistent and unauthorized patients receive identical
403 bodies. The complete suite passed again after that correction. Unit tests
use isolated mocks/mongomock; the separate browser runs below use real MongoDB.

The single root runtime requirements file is fully pinned and was installed
into a fresh `.venv-verify` using Python 3.13.15. Its 145 runtime/test packages
pass `uv pip check`; backend startup and cached PaddleOCR initialization pass.
The three saved joblib artifacts load under scikit-learn 1.9.1 with
`InconsistentVersionWarning` promoted to an error. This checks serialization
compatibility, not clinical validity. The installed Whisper package does not
establish recognition accuracy or prove its external model download is available
offline.

Bearer authentication and its four legacy endpoints are removed. Public catalog
and graph calls are rate-limited; health details require the appropriate role.
Account password attempts use shared counters, and production public-route
counters are shared between workers. Uploads require matching JPG/PNG/WebP
extension and decoded format, successful Pillow verification, a single frame,
and at most 16 million pixels, before OCR. The unmounted arbitrary Mongo insert
route is deleted; admin imports accept only environment-configured destinations
and return generic failures. Production refuses mocked databases.

Reports reuse the consent grant returned by authorization instead of looking it
up again and potentially dereferencing None. Patient log views can filter
security/read events and page through older entries; repeated identical reads
are deduplicated in five-minute windows while denied/security events are kept.
Patient-directory polling does not generate record-view events. No audit-data
retention/deletion policy has been invented. Medicine scheduling now suggests
catalog names and flags unmatched free text; verified brand mapping is pending.

The live MongoDB three-role rehearsal passed on 21 October with no API stubs or
browser JavaScript errors, including doctor approval, rejection/approval of
consent, report download and revocation. Disposable records were cleaned up.
The separate patient workflow passed profile, scheduling, taken records, history,
report download and logout. A read-only live graph comparison again verified
304 nodes and 799 relationships. Authenticated admin health also confirms
Firebase Admin initialized and the reminder worker running; physical delivery
remains unverified. The duplicate direct Neo4j startup attempt
failed on a database lock; the already-running instance passed verification.
No new Neo4j license terms were accepted by this work.

Injected graph failure, empty OCR and voice-network-failure browser rehearsals
passed. These were simulated failure tests, not physical disconnection tests.
A local fictional-account recording is saved at
`artifacts/demo-video/three-role-rehearsal.mp4` (no narration). Demo credentials
are ignored, untracked, and absent from the available `git log --all` history;
this does not prove they never appeared in an external copy or deleted history.

The pinned Python requirements audit found no known vulnerabilities. Today's
frontend npm audit found new follow-redirects and Vite advisories; compatible
updates resolved them. Frontend and root npm audits now report zero known
vulnerabilities. Lint and production build pass after updating Vite to 8.3.5;
the large-bundle warning remains. See `docs/DEPLOYMENT.md` for proxy trust,
MFA/recovery, retention, secrets/backups and content/licensing prerequisites.
DDInter's published CC BY-NC-SA 4.0 terms were checked; no commercial permission
or permission for a differently licensed Kaggle release is claimed.

### Demo preparation follow-up, 20 October

`docs/DEMO_WALKTHROUGH.md` provides an 8–10 minute three-role demonstration,
preflight, session/profile instructions and honest outage fallbacks.
`tools/seed_demo.py` created isolated fictional patient/admin accounts and a
pending doctor application. Random credentials are in ignored local
`artifacts/demo-accounts.json`; seed medicines explicitly say demonstration only
and reminders are disabled. The tool refuses to reset an existing manifest;
its cleanup is restricted to manifest-owned demo identities and their records.
The pending doctor must be approved during the walkthrough.

Live HTTP checks verified patient/admin cookie login, logout, a pending-doctor
login denial, and CSRF rejection on a patient write for an untrusted origin,
an unapproved localhost port, and a missing Origin. The allowed origin succeeds.
Results are in `artifacts/demo-readiness-results.json`; no credentials are
included. Twelve focused session/graph tests passed in this follow-up.

`tools/prepare_content_review.py` generated 200 pending language-review rows
(100 Kannada, 100 Tulu), flagged the 11 missing Tulu classes, and recorded source
hashes. Masters were not modified. `docs/CONTENT_REVIEW.md` explains the native
speaker/pharmacist handoff. The user currently has no reviewer and cannot test
a phone now, so neither human review nor physical notification delivery is
claimed. No HTTPS tunnel was opened. Google real-account sign-in and the external
academic report are also still unverified/unmodified.

The previous `.venv` points at a missing Microsoft Store Python installation.
This pass used the working `.venv-dataset/Scripts/python.exe`, restoring missing
backend/OCR/audio dependencies and the existing passlib-compatible bcrypt 4.0.1.
Frontend uses port 5173; backend uses port 8000. MongoDB connectivity was verified
outside the network-restricted command sandbox. A sandbox DNS failure was not
treated as proof that the application's database was down.

Still deferred or incomplete:

- Reviewed Tulu class values, repetitive narrative corrections and broader
  clinical/reference coverage; licensing approval for Kaggle release.
- Cumulative-risk/drug-disease rules, reviewed brand and combination mappings,
  and any DDInter direct-lookup replacement. Some legacy OCR aliases exist;
  they are not a comprehensive reviewed brand database.
- Real-device reminder delivery, Google sign-in and representative OCR/voice
  accuracy evaluation. Tulu synthesis still uses a Kannada voice.
- Granular consent scopes, account deletion/retention policy, formal security
  and data-protection review; no compliance certification is claimed.
- Mobile/WhatsApp fallback and server-generated PDF remain pilot proposals.
- Revision of an external academic report requires its current editable source.
  Intent-classifier/TC23 statements from older report text were not treated as
  verified facts about the current code.
