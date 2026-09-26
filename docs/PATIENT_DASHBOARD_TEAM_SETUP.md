# Patient dashboard: teammate setup and test guide

This guide covers the patient work merged with the newer `origin/dev` doctor changes. Google login uses Google Identity Services plus the backend's JWT and MongoDB users. Firebase is used for browser notifications; Firebase Authentication is not required for the existing Google login flow.

## 1. Pull and install

Commit or stash your own unfinished changes first. From a clean checkout:

```powershell
git switch dev
git pull --ff-only origin dev
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt -r requirements-test.txt
cd frontend
npm ci
cd ..
```

Use Python 3.11 and Node 22.12 or newer compatible with the installed Vite version. The backend requirements pin the bcrypt/passlib combination used by this app. First OCR use needs downloaded Paddle models; internet access is also needed for Google's speech recognizer and the Microsoft online female-voice service used by `edge-tts`. Reinstall backend requirements after pulling the speech update. The local Whisper fallback may download a model and is slower on CPU. `imageio-ffmpeg` provides the audio conversion executable.

For a new checkout only, copy `.env.example` to `.env`, and `frontend/.env.example` to `frontend/.env`. **Do not overwrite an existing configured `.env`.** Obtain private credentials from the project owner through a secure channel. Pulling Git does not supply them.

## 2. Backend environment

| Variable | What to configure |
| --- | --- |
| `MONGO_URI` | Your authorized MongoDB connection string; allow your IP in Atlas Network Access and use an authorized database user. |
| `MONGO_DB` | `meds`, or your separate development database. Shared database means shared patient data. |
| `JWT_SECRET_KEY` | Private random value of at least 32 characters. All processes serving one deployment need the same value. Changing it invalidates existing sessions. |
| `GOOGLE_CLIENT_ID` | The project's Google OAuth **Web application** client ID. This is a public identifier, not the client secret. |
| `FIREBASE_SERVICE_ACCOUNT_FILE` | Absolute path to a private Firebase Admin JSON key outside the public frontend. Preferred to pasting JSON. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Alternative to the file: service-account JSON. Leave this empty if using the file; the file takes precedence. |
| `REMINDER_TIMEZONE` | `Asia/Kolkata` for the current project. Schedule times are interpreted in this server timezone. |
| `REMINDER_POLL_SECONDS` | `2`. Update old local values of `30` too. |
| `REMINDER_CATCHUP_MINUTES` | `5`: recover recent missed polls, not hours-old doses. |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | The actual running Neo4j instance's connection details. Local Desktop normally uses its displayed Bolt URI. |
| `WARM_UP_OCR` | `true` loads OCR models before the app becomes ready. |

Generate a signing key locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and put it only in `.env`. Never put Admin keys, database passwords, JWT secrets, or Google client secrets in `VITE_*` variables or Git.

## 3. Google Console setup

1. Open the Google Auth Platform project containing the existing web OAuth client.
2. In the client's **Authorized JavaScript origins**, include the exact frontend origin, normally `http://localhost:5173`. Add `http://localhost` for local testing and `http://127.0.0.1:5173` if using that address. Changing the port creates a different origin.
3. If the consent configuration is in Testing, add teammates' Google accounts as test users. The owner manages this once per shared project.
4. Put that client ID in backend `GOOGLE_CLIENT_ID`, then restart the backend. `/auth/providers` supplies the public ID to both Register and Login.

The app uses a JavaScript credential callback, so it does not need a Google client secret or a new redirect endpoint. Register first with Google, then use Google on the Login tab. If the email already belongs to a password account, confirm the existing app password once to link Google while preserving the same patient profile and medication history. See [Google's setup documentation](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid).

## 4. Firebase Console and web configuration

1. In Firebase Project settings, register a **Web app** with a nickname such as `MMSS Notification Web`. Firebase generates its app ID; do not invent the `VITE_FIREBASE_APP_ID` value.
2. Copy the web SDK config into `frontend/.env` using the mapping below.
3. In Project settings → Cloud Messaging → Web Push certificates, generate or reuse the project's key pair. Put its **public** key in `VITE_FIREBASE_VAPID_KEY`.
4. Use the same Firebase project for the web config, VAPID key and Admin service account. Enable the FCM Registration API if registration reports it disabled, and the Firebase Cloud Messaging API if sending reports it disabled. The Admin identity needs permission to send messages.
5. Obtain an Admin service-account key through the project's authorized owner (Project settings → Service accounts), store it privately, and configure its absolute path on each backend machine. Organization policies may require the owner to provision an approved identity instead of downloading a key.

| Firebase SDK field | Frontend variable |
| --- | --- |
| `apiKey` | `VITE_FIREBASE_API_KEY` |
| `authDomain` | `VITE_FIREBASE_AUTH_DOMAIN` |
| `projectId` | `VITE_FIREBASE_PROJECT_ID` |
| `storageBucket` | `VITE_FIREBASE_STORAGE_BUCKET` |
| `messagingSenderId` | `VITE_FIREBASE_MESSAGING_SENDER_ID` |
| `appId` | `VITE_FIREBASE_APP_ID` |
| Web Push public key | `VITE_FIREBASE_VAPID_KEY` |

`npm run dev` and `npm run build` generate `frontend/public/firebase-public-config.js`. Vite's environment loading includes `.env.local`, mode files and process environment values. Do not hand-edit the generated file. Restart Vite after changing configuration; rebuild before deployment. See [Firebase web setup](https://firebase.google.com/docs/cloud-messaging/web/get-started).

## 5. Start and verify

Backend terminal, from repository root:

```powershell
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Frontend terminal:

```powershell
cd frontend
npm run dev -- --host localhost --port 5173 --strictPort
```

Open `http://localhost:5173`. Do not open HTML using `file://`. Use localhost or HTTPS for service workers, microphone and notification permission. `VITE_API_URL` must agree with the backend port; stale `8001` configuration will break login against an `8000` backend. With the value unset in development, Vite proxies API requests to port 8000. Direct patient page navigation is excluded from proxying.

Check `http://127.0.0.1:8000/health` and `/docs`. Health shows Firebase Admin initialization, worker state, timezone and polling interval; initialization alone does not prove device delivery. The existing notification routes are `POST /patient/fcm-token`, `DELETE /patient/fcm-token`, and `POST /patient/fcm-test`. No duplicate test endpoint is needed.

Run the read-only audit:

```powershell
.venv\Scripts\python tools/verify_patient_environment.py
```

It prints collection counts, dataset consistency, Neo4j counts when connected, Firebase project matching, and **dry-run** token validation. It does not send visible notifications or reload databases. Neo4j is not necessary for the cached medicine lookup dataset. Graph-backed features still require a working instance. Confirm graph contents using:

```cypher
MATCH (d:Drug) RETURN count(d);
MATCH (d:Disease) RETURN count(d);
MATCH ()-[r]->() RETURN count(r);
```

The legacy Neo4j loaders contain graph-clearing operations and fixed connection settings; do not run them on shared data as a generic setup step. Ask the graph owner for the populated database/approved import procedure if these counts are zero. No graph reload was performed during this review.

## 6. Where actions appear in MongoDB

In Compass or Atlas Data Explorer select the database named by `MONGO_DB`. Refresh after each action. Use your own lower-case registered email in the filter.

| Frontend action | Collection / filter | Expected change |
| --- | --- | --- |
| Register or save profile | `users`, `{ "username": "your-email@example.com" }` | One account; age, gender and medical condition update. Google linking adds `google_sub` to the same account. |
| Enable Notifications | `fcm_tokens`, `{ "patient_username": "your-email@example.com" }` | Browser token saved. Each teammate/device must grant permission and register its own token. |
| Add to Schedule | `patient_schedules`, same patient filter | Active schedule with `scheduled_times`, dosage, instructions and reminder preference. |
| Mark as Taken | `medication_history`, same patient filter | New dose record; schedule `last_taken_at` updated. |
| Remove from schedule | `patient_schedules`, same filter | `status: "inactive"`, reminders disabled; history retained. |
| Scheduled reminder | `reminder_deliveries`, same filter | Due occurrence, `attempts`, `attempted_at`, `status`, accepted count and safe error category. Records expire after 30 days. |
| Doctor access decision | `access_requests` | Request status changes after Accept/Reject. |

Opening a page, searching, scanning or speaking does not create patient medication records. Scan results must be reviewed and explicitly saved. Login does not create a second account. Never share password hashes, tokens or private records in screenshots/reports.

## 7. Notification timing and troubleshooting

In **My Medicines**, click **Enable Notifications** and allow the browser prompt. Expand **Check notification delivery** and use **Send Test Notification**. Then create a clearly labeled test schedule at least two minutes in the future, using the timezone displayed by `/health`, with reminders enabled. Keep the backend and computer awake. First test with the page visible, then with another tab focused. Click the notification to return to My Medicines; remove the test schedule afterward.

The worker checks every two seconds, catches up within five minutes, claims each schedule occurrence atomically and retries failed devices without intentionally re-sending to accepted devices. Firebase gets high web-push urgency and a five-minute TTL. Invalid/unregistered devices are removed when a send detects them. Foreground messages display via the service worker; background notification payloads use Firebase's automatic display so the app does not display a second copy. See [Firebase message handling](https://firebase.google.com/docs/cloud-messaging/web/receive-messages).

`status: "sent"` means Firebase accepted the delivery request, **not that a person saw the notification**. OS notification settings, Focus Assist/Do Not Disturb, browser background restrictions, network outages and sleeping machines can delay or suppress it. A crash after Firebase accepts a message but before MongoDB records it can still cause a retry; stable notification tags reduce duplicate visible entries. This is not an exact-time alarm guarantee.

| Symptom | Check |
| --- | --- |
| No reminder attempt document | Worker running, correct timezone/time format, active schedule, reminders enabled, created before due time; a dose already recorded after its due time is skipped. |
| Retry with no device | Enable Notifications on this browser while signed in. |
| `UnregisteredError` in audit | Old browser subscription expired. Re-enable notifications; if necessary reset this site's notification/service-worker data and grant permission again. |
| Firebase initialization fails | Admin file exists and is readable; valid JSON; restart backend after changes. |
| Firebase accepts but nothing visible | Browser/OS notifications enabled, page not in an unsupported browser, Focus Assist off; test visible and background tabs separately. |
| Wrong sender/project error | Align all web config, VAPID and Admin credentials to the same project, then register a fresh token. |
| Google unavailable/origin error | Correct OAuth ID, exact allowed origin/port, permitted test account, internet access to Google's script; restart backend. |
| Mongo timeout | Correct URI, Atlas network access and database user, or local Mongo service running. |
| Neo4j unavailable | Start the intended Desktop instance or hosted service; match URI/protocol/user/password. CSV fallback does not prove Neo4j connected. |

Sign-out attempts to unregister this device and revoke its browser subscription. On a shared browser, do not leave another patient's session open. Backend service uptime is required for scheduling; closing the terminal stops reminders. A production deployment needs a continuously running backend and HTTPS, with allowed origins and API URL configured for that deployment.

## 8. Patient test cases

For a **single step-by-step walkthrough** of the whole dashboard (register → search → OCR → voice → medicines → profile → logout), use [PATIENT_DASHBOARD_E2E_TEST.md](PATIENT_DASHBOARD_E2E_TEST.md) (**TC-PAT-001**).

Use a test account and labels that are clearly test data; do not change prescribed doses based on these samples.

| Page | Test | Expected result |
| --- | --- | --- |
| Register/Login | Register email, log in; try unregistered email; then test Google Register/Login | Registered login works; unknown login fails; existing email links only after password confirmation. |
| My Profile | Save age, gender and condition; navigate away and back | Same values persist in `users`; incomplete new profiles prompt completion. |
| Medicine Search | Search `Metformin` in English, Kannada and Tulu; search a made-up name | Relevant local dataset result; brief speech where supported; clear not-found state. No schedule written. |
| Scan & Add Medicines | Upload a clear medicine image, review/correct fields, then Add to Schedule | OCR fills review form and reads its summary; no write before Save; active Mongo schedule after Save. |
| Voice Search | Upload `tests/fixtures/voice/metformin-en.wav`; then record a short name and pause | Upload search works; recording searches automatically after a pause; selected-language response. |
| My Medicines | Mark a test dose taken; remove its schedule | History row added; removed medicine no longer active; history remains. |
| Notifications | Test notification, then schedule a future reminder; test visible/background tabs | One visible notification per event; a scheduled attempt is traceable in `reminder_deliveries`. |
| Navigation | Visit all five pages at desktop/mobile width; sign out | Heading above nav, correct active link, back link on inner pages, no horizontal overflow; protected pages require login. |

All patient readouts use the same selected female voices: `en-IN-NeerjaNeural` for English and `kn-IN-SapnaNeural` for Kannada/Tulu. No default browser or male voice is used as a fallback. If the service is unavailable, the app keeps the written result and reports the audio problem. Tulu uses a Kannada-script speech engine, not a native Tulu voice; pronunciation needs the user's review. Supplied pronunciations for standalone numbers 1–10 affect speech only, preserving stored doses and compound/decimal numbers. The updated first Excel row was copied to the runtime CSV; future workbook corrections also need exporting before the app can use them. The dataset audit checks structural consistency and lookup coverage, not medical correctness.

## 9. Automated checks

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m pytest tests/test_mongo_loader.py -q
.venv\Scripts\python -m pytest tests/test_integration_mongo.py -q
cd frontend
npm run build
npm run lint
cd ..
.venv\Scripts\python tests/patient_layout_browser_check.py
.venv\Scripts\python tests/scan_page_browser_check.py
.venv\Scripts\python tests/verify_backend_live.py
.venv\Scripts\python tests/voice_browser_check.py
.venv\Scripts\python tools/benchmark_patient_api.py
```

Browser checks require Microsoft Edge and Playwright. Layout/scan tests mock API responses; `verify_backend_live.py` creates disposable records and deletes only its own records afterward. Voice checks use a synthetic fixture and real speech APIs; they verify playback invocation, not native-speaker pronunciation. Configure `PATIENT_TEST_API_URL` if using a different browser-visible backend address. Never interpret a mocked test as proof that MongoDB or Firebase is connected. For the current measured results and remaining environment blockers, see [verification results](PATIENT_DASHBOARD_VERIFICATION.md).
