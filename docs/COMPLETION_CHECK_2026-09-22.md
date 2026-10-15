# Completion check — 22 September 2026

Reviewed current `dev` at `8dce9d0`, rather than the older ZIP snapshot.

## Older action items

- Neo4j loader: all five medicine-ID references already use `resolve_drug_id`;
  the regression suite passes. No database import was performed.
- Reports: component already fetches `/doctor/medication-history`, but was not
  reachable through routing/navigation. Added `/reports` inside the doctor role
  guard and a doctor-sidebar link.
- Upload cleanup: neither upload directory has tracked files, and both match
  ignore rules. This does not remove blobs from old Git commits. No history
  rewrite or force-push was performed.

## Fixes made locally

- Removed unused state/imports and corrected effect initialization to pass lint.
- Patient-list requests are cancelled on unmount.
- Removed the hardcoded `doctor` / `secret` automatic login fallback.
- Removed local demo consent and simulated request-success behavior; the patient
  list now reflects actual backend access-request results.
- Updated scan browser checks to the current search label and guest read-only
  behavior; added doctor consent/navigation/guest-route checks.

## Verification

- 78 backend tests and 9 subtests passed (dependency deprecation warnings remain).
- Full frontend lint and production build passed.
- Patient desktop/mobile layout check passed.
- Scan review, corrected-dose save, speech request, navigation and guest save
  restriction browser checks passed.
- Doctor pending-access and Reports navigation/guest redirect checks passed.
- Browser checks use mocked API data; they do not prove live cross-account consent
  or clinical accuracy. No real patient record was created by these checks.

## Current service readiness

Read-only environment audit, without printing secret values:

- MongoDB connected.
- Firebase Admin initialized using the existing configuration.
- Generated frontend Firebase project matches the Admin project.
- FCM dry run accepted two stored tokens; one returned `UnregisteredError`.
  No actual notification was sent. An expired token is not evidence of missing
  service-account JSON; refresh notification registration on that browser.
- Reminder timezone: Asia/Kolkata; configured poll interval: 2 seconds.
- Neo4j connectivity returned `ServiceUnavailable`. Graph-backed functionality
  needs its service/connection restored; cached CSV medicine lookup remains usable.
- All 30 medicines were found for each of English, Kannada, and Tulu.

Firebase configuration is present and passes dry-run verification. The remaining
notification acceptance check is a real foreground/background scheduled reminder
on an authorized test device, with browser/OS permission enabled. This was not
sent to stored users during the audit. Follow `PATIENT_DASHBOARD_TEAM_SETUP.md`.

No code was committed or pushed during this completion check. Native Tulu speech
accuracy, clinical dataset validation and historical secret rotation are not
certified by these checks.
