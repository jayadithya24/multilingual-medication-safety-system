# Local demonstration: three roles

Use fictional data only. This is an information/research prototype, not a
validated prescribing system. Allow 8–10 minutes. Use separate browser profiles
for each role: cookies are shared between tabs in the same profile.

## Before opening the doors

1. Connect the laptop to the network that will be used for the demo. MongoDB,
   Google sign-in and cloud speech/notifications need network access even though
   the website runs on localhost. Disable sleep during the session.
2. Start the project database in Neo4j Desktop. Start the backend with
   `.venv-review/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers`.
   In `frontend`, run `npm run dev -- --host localhost --port 5173 --strictPort`.
3. Check `http://127.0.0.1:8000/health` for the minimal running status.
   Using an admin session, `/admin/health` provides detailed service status;
   graph_check must say verified for a live graph demonstration. Firebase Admin
   ready/worker running do not prove notification receipt.
4. Run `.venv-dataset/Scripts/python.exe -m neo4j.load_data --apply --sync` if needed.
   It backs up application graph data before reconciliation.
5. Run `.venv-dataset/Scripts/python.exe tools/seed_demo.py`. Open the ignored
   `artifacts/demo-accounts.json` privately to get credentials. The doctor starts
   pending. No existing account is changed. Reminders on seeded medicines are off.
6. Rehearse once. To start with fresh accounts afterward, run the seed tool with
   `--cleanup`, then without it. Cleanup removes only that manifest's demo data.
   Do not manually delete the manifest before cleanup. Sessions expire after
   30 minutes of inactivity, with an eight-hour absolute maximum; sign in shortly
   before presenting. Background polling does not renew idle sessions.

## Script

| Time | Role | Action and expected result |
|---|---|---|
| 0–1 min | Admin | Open `/admin`, sign in, and approve the pending Demo Doctor. Explain that this is manual administrative approval, not medical-register verification. |
| 1–3 min | Patient | Open `/public`, sign in, and show medicine lookup in English, Kannada and Tulu. Show the selected Indian female voice and the visible Tulu/Kannada-synthesis disclosure. Show OCR's review/edit step if a prepared sample is available; do not imply unmeasured accuracy. |
| 3–4 min | Patient | Open My Medicines. Show fictional schedules with reminders disabled. Mark one record taken; explain this is patient-reported. Create a sharing code and copy it privately. |
| 4–5 min | Doctor | Open `/research`, sign in, go to Patient History & Drug Lists. The directory is initially empty. Enter the patient's code and submit the request. |
| 5–6 min | Patient | Reject the first request to show control. Create a new code, have the doctor request again, then grant seven-day access. Show expiry and renewal. |
| 6–8 min | Doctor | Refresh patients, open the patient. Show 3 of 4 catalog medicines covered, the unlisted medicine, reference links, and any “Review required” label. Explain these are recorded reference relationships, not an ML diagnosis. Show day-level taken/unconfirmed history without calling unconfirmed doses “missed”. |
| 8–9 min | Doctor | Generate the patient report and download HTML or use browser Print to PDF. Explain that exported copies cannot be recalled by later revocation. |
| 9–10 min | Patient/Doctor | Revoke consent; refresh doctor records and show denial. Patient opens the access log. Sign out all profiles. |

## Honest fallback plan

- Neo4j unavailable: use the visibly identified CSV fallback and say the live
  graph is unavailable. Do not present it as a successful Neo4j connection.
- MongoDB/network unavailable: login/consent workflows cannot run. Use a clearly
  labelled prerecorded rehearsal or previously saved screenshots/results, not
  a fabricated success screen. Restore the network and retry live.
- Voice/cloud speech unavailable: use typed search and source text. Do not claim
  native Tulu speech synthesis; its pronunciation still requires review.
- OCR inaccurate: demonstrate manual correction before saving. Keep a typed
  sample available, and identify it as typed rather than OCR output.
- Google login unavailable: use the prepared password accounts. Google sign-in
  remains unverified until tested with a real account.
- Reminder delivery: say “worker runs; physical-device delivery unverified”.
  Do not enable medicine reminders for the fictional seeded regimen.

## Evidence and limitations

`tests/verify_three_role_live.py` is an automated real-MongoDB rehearsal with its
own temporary accounts; it does not replace this manual walkthrough or consume
the seeded demo accounts. `IMPLEMENTATION_REVIEW.md` records measured checks.
No tunnel is opened by these tools. A phone test needs an HTTPS origin, exact
CORS/cookie configuration, device permission and observed receipt; iOS browser
support must be checked before promising delivery. Never expose a database port
or the credential manifest. No physical-phone result is recorded yet.
