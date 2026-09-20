# Patient dashboard verification — 20 September 2026

## Speech correction follow-up

The subsequent patient speech update replaces browser-selected/gTTS voices with explicitly selected female voices throughout OCR, medicine search and voice search: English `en-IN-NeerjaNeural`; Kannada/Tulu `kn-IN-SapnaNeural`. The provider's voice catalogue identifies both as Female. Actual synthesis returned audio in approximately 1.24 seconds (English sample) and 1.13 seconds (short Tulu sample). Network time varies; these are not latency guarantees. A failed service call leaves readable text instead of silently selecting a male/default voice.

Tulu OCR now appends the user's supplied review sentence: “ಬಳಕೆ ಮಲ್ಪುನ ದುಂಬು ಈ ವಿವರನ್ ಈರ್ನ ಔಷಧ ಚೀಟಿದ ಒಟ್ಟು ಪರಿಶೀಲನೆ ಮಲ್ಪುಲೆ.” Speech-only replacements cover the supplied 1–10 pronunciations, while decimals, larger numbers, identifiers and stored dosages remain unchanged. The user's first workbook row (Metformin description and side effects) is synchronized to the CSV consumed by the app; other rows were preserved. Native-speaker pronunciation still needs user acceptance.

## Repository and integration

Work was performed on `dev`, starting from `70d3bd6`. Existing patient work was preserved in `741478b`; `6fc9cae` merged the four newer remote commits through `ef43716`. A further remote Neo4j update, `c187173`, appeared during final verification and is included in the final integration. Use `git log -5 --oneline` for the published tip.

The [team setup guide](PATIENT_DASHBOARD_TEAM_SETUP.md) covers local credentials, provider Console steps and patient test cases. Private `.env` files and generated Firebase configuration are not published. Local runtime corrections: frontend API port aligned from 8001 to 8000, reminder polling changed from 30 to 2 seconds.

## Results

| Check | Result |
| --- | --- |
| MongoDB | Connected. At the read-only audit: 2 users, 3 FCM token records, 5 schedules, 2 medication-history records. Disposable test records were cleaned up. |
| Firebase Admin | Initialized successfully; backend `/health` reports ready and reminder worker running. |
| Frontend Firebase | Public config generated; its project matches Admin configuration. |
| FCM validation | Two stored tokens accepted by Firebase **dry-run** validation; one returned `UnregisteredError`. No visible notification is sent by this audit. |
| Notification delivery | Foreground/background handling corrected; actual visible notification and wall-clock delivery still require the manual device test in the guide. Firebase acceptance is not delivery confirmation. |
| Reminder scheduler | Tests cover timezone, one send per occurrence, next-day recurrence, missed-minute/midnight recovery, inactive/disabled/taken/new schedules, retries of only failed devices, concurrent workers, expired claims and stale-token cleanup. |
| Neo4j | Current configured instance returned `ServiceUnavailable`. No loading was performed; live Drug, Disease and relationship counts could not be obtained. CSV fallback is available. |
| Dataset audit | English, Kannada and Tulu each contain 30 named medicines, no duplicate/empty drug names, matching drug-name sets; all 90 language-specific searches returned results. This is not a clinical-content review. |
| Live patient flow | Browser login, profile save, schedule creation, dose history, removal retaining history and logout passed against the running backend/MongoDB. Token registration/unregistration passed using a synthetic storage-only token. |
| Layout | All five patient sections passed at 1440 px and 390 px: heading/nav order, active links, back links and no horizontal overflow. |
| Scan flow | Mocked scan review, corrected dosage, explicit save, manual entry, legacy redirects and guest guard passed. Real synthetic-image OCR also returned HTTP 200. |
| Voice | Real upload and automatic recording search passed in English, Kannada and Tulu using the English Metformin audio fixture. Playback was invoked; pronunciation was not assessed by a native speaker. |
| Frontend validation | Production build and lint passed. Initial JavaScript reduced from 636.39 KB to 426.45 KB before compression; graph/doctor features load separately. |

The backend suite contains 73 tests plus 9 subtests, including female voice selection, speech-only Tulu numbers, Mongo loader and Mongo integration tests. Existing dependency deprecation warnings remain (FastAPI lifecycle hooks, Starlette/httpx, Python audio modules and Firebase token naming); they are not hidden.

## Local timing samples

Measured after OCR model warm-up, using `tools/benchmark_patient_api.py` on this machine:

| Request | Samples | Observed time |
| --- | --- | --- |
| Medicine search | 3 per language | 0.018–0.037 seconds |
| OCR | 3 synthetic printed-name images, 900×240 | 0.696–0.943 seconds |
| Voice | 2 English Metformin WAV requests | 0.564–0.615 seconds |
| Health while OCR runs | 3 | 0.304–0.445 seconds |

These samples do not establish a universal three-second guarantee. First model downloads, long/noisy recordings, complex prescriptions, CPU contention and remote services can take longer. Recording time and speech playback duration are separate from processing time. Repeated TTS text now reuses a bounded in-memory audio cache; failed synthesis is retried rather than cached.

## Changes to review

- Kept Google registration/login/linking, complete-profile routing, combined scan page and patient navigation while merging the newer doctor/admin work.
- Changed synchronous database, authentication, graph and TTS routes to FastAPI worker threads so they do not directly block reminder polling.
- Made medicine search consult the existing cached multilingual dataset first; bounded graph connection waits and closed the search driver.
- Added `reminder_deliveries` with a unique occurrence index, expiring audit records, atomic worker claims and per-device retry tracking. No existing patient collection was cleared.
- Added visible foreground notifications, avoided a second background display, and made notification clicks return to My Medicines. Sign-out revokes the browser subscription where possible.
- Simplified My Medicines with expandable doctor access/testing sections; retained schedule, dose history and removal. Fixed lint and missing route imports exposed by the merge.
- Matched generated Firebase config to Vite environment/mode loading and corrected the dev proxy's handling of patient page URLs.
- Added scheduler/TTS regression tests, a read-only environment audit, reproducible timing script and updated browser tests.

For the full file list: `git diff --name-only 70d3bd6..HEAD`. Unrelated local `docs/paper/` files were left out of the push.

Remaining manual work: teammates need their own authorized environment configuration and browser permission/token; the project owner must permit Google test users/origins and provide authorized Firebase credentials. Restore the intended Neo4j connection if graph features are needed. Run the foreground/background future-reminder test on the actual target device before treating notifications as verified.
