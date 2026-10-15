# Patient dashboard — full end-to-end test case

Use this as **one continuous manual test** after pulling latest `dev`, installing dependencies, and starting backend + frontend. Label all data clearly as test data.

**Prerequisites**

1. `git pull --ff-only origin dev` (branch already up to date as of last sync).
2. Backend: `.venv\Scripts\python -m pip install -r backend/requirements.txt` (includes `edge-tts`).
3. Backend running: `.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
4. Frontend running: `cd frontend && npm run dev -- --host localhost --port 5173 --strictPort`
5. Open `http://localhost:5173` (not `file://`).
6. Optional sanity check: `http://127.0.0.1:8000/health` returns ready.

**Test account:** use a disposable email such as `patient-e2e-test+1@example.com`, or your own Google test account.

---

## TC-PAT-001 — Complete patient portal flow

| Step | Action | Expected result | Pass |
| --- | --- | --- | --- |
| 1 | Go to **Patient Portal** (`/public`) → **Register** with test email + password | Account created; redirected toward profile or dashboard | ☐ |
| 2 | If prompted, open **My Profile** and save: age `55`, gender `Female`, condition `Hypertension` | Values persist after refresh | ☐ |
| 3 | Open **Medicine Search** tab on dashboard | Heading “My Medication Dashboard”; nav shows Medicine Search active | ☐ |
| 4 | Set language **English** → search `Metformin` → **Search** | Result card appears; **female** English voice reads name + brief info (no male browser voice) | ☐ |
| 5 | Switch language **Kannada** → search `Metformin` again | Kannada result; female voice (Sapna) | ☐ |
| 6 | Switch language **Tulu** → search `Metformin` again | Tulu result; female voice | ☐ |
| 7 | Search `XYZNOTREAL999` | Clear “not found” message; no schedule created | ☐ |
| 8 | Click **Scan & Add Medicines** in nav | Scan page opens; back link to dashboard visible | ☐ |
| 9 | Set language **English** → upload a clear medicine-strip/prescription image → **Scan Image** | Form fills with detected medicine/dosage; spoken summary includes review line (“Check them against your prescription…”) | ☐ |
| 10 | Correct dosage if needed (e.g. `500 mg`) → turn **Reminders** on → **Add to Schedule** | Success message; no save happened before this button | ☐ |
| 11 | Set language **Tulu** → scan another image (or re-scan) | Spoken output = medicine + dosage + Tulu review: “ಬಳಕೆ ಮಲ್ಪುನ ದುಂಬು ಈ ವಿವರಣ್ ಈರ್ನ ಔಷಧ ಚೀಟಿ ದ ಒಟ್ಟು ಪರಿಶೀಲನೆ ಮಲ್ಪುಲೆ.” | ☐ |
| 12 | Open **Voice Search** tab | Record / upload controls visible; language selector works | ☐ |
| 13 | Upload `tests/fixtures/voice/metformin-en.wav` (or record “Metformin” and pause ~3 s) | Transcript + medicine info; female voice playback | ☐ |
| 14 | Open **My Medicines** tab | Schedule from step 10 listed with correct dosage | ☐ |
| 15 | Click **Mark as Taken** on that schedule | Dose moves to history; schedule updates | ☐ |
| 16 | Remove the test medicine from schedule | Medicine inactive; history row still visible | ☐ |
| 17 | Expand **Enable Notifications** → allow browser prompt → **Send Test Notification** | One test notification (if Firebase configured); skip if env not set up | ☐ |
| 18 | Visit **My Profile** → change age to `56` → save → return to dashboard | Profile shows updated age | ☐ |
| 19 | Resize browser to mobile width (~390 px) | No horizontal scroll; all five nav links usable | ☐ |
| 20 | **Sign out** → try opening `/patient-dashboard` directly | Redirected to login; protected pages blocked | ☐ |

**Pass criteria:** Steps 1–16 and 18–20 all pass. Step 17 passes if Firebase is configured; otherwise mark N/A.

**Fail triggers:** Male/default browser voice on search/OCR/voice; OCR Tulu speaks only name+dosage without review sentence; scan auto-saves without **Add to Schedule**; patient can access doctor-only features.

---

## Quick automated smoke (optional, after manual pass)

From repo root, with backend + frontend running:

```powershell
.venv\Scripts\python tests/patient_layout_browser_check.py
.venv\Scripts\python tests/scan_page_browser_check.py
.venv\Scripts\python tests/voice_browser_check.py
.venv\Scripts\python -m pytest tests/test_tts_cache.py -q
```

These mock most APIs except voice/TTS network calls. They do **not** replace TC-PAT-001 for login, MongoDB writes, or real notifications.

---

## Troubleshooting during test

| Issue | Fix |
| --- | --- |
| Male English voice | Restart backend after `pip install edge-tts`; hard-refresh browser |
| No Tulu OCR speech tail | Confirm language = Tulu before scan; restart frontend |
| Login/API errors | Check `VITE_API_URL` / proxy uses port **8000**, not 8001 |
| OCR slow first time | Wait for Paddle model warm-up (`WARM_UP_OCR=true`) |

For environment setup details see [PATIENT_DASHBOARD_TEAM_SETUP.md](PATIENT_DASHBOARD_TEAM_SETUP.md).
