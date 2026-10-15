# Patient sign-in setup

Email/password sign-in works independently of Google and Firebase notifications.

## Google

1. Open Google Cloud Console and select your project. In Google Auth Platform,
   configure Branding and Audience. If your app is in Testing, add your test accounts.
2. Create an OAuth client with application type **Web application**.
3. Add authorized JavaScript origins `http://localhost:5173` and
   `http://127.0.0.1:5173` (add your exact HTTPS origin when deploying).
4. Set `GOOGLE_CLIENT_ID=<web client ID>` in the root `.env`. This popup-based
   integration needs the client ID, not a client secret. Restart the backend.
5. Reload the patient page, which opens on Register. Choose **Sign up with Google**
   to create an account. On the Login tab, Google sign-in accepts registered accounts only.
   A new patient is stored in MongoDB `meds.users`, identified by `google_sub`.
   Complete age, gender, and medical condition in My Profile.

Existing email/password accounts can link Google by choosing their matching Google
account and confirming their existing app password once. The patient ID, profile,
and schedules are preserved. Later Google logins do not require the app password.
The app never silently links an identity based only on a matching email.
Google sign-in only grants the patient role. Disabled accounts are rejected.

The backend validates Google token signature, audience, issuer, expiry, and verified
email before issuing the app's own session token. Live Google verification requires
a configured client and interactive consent; automated tests mock this boundary.

`JWT_SECRET_KEY` in the root `.env` must contain a random secret of at least
32 characters. Keep it private and stable; changing it invalidates existing sessions.

Official instructions:
- https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid
- https://developers.google.com/identity/gsi/web/guides/verify-google-id-token

## Verification

- Register, sign in by pressing Enter, toggle Show password, and sign out.
- On every patient page verify heading, navigation, active section, and mobile width.
- Google without configuration must show an unavailable message, not fake success.
- Once configured, test new Google account, repeat login, canceled popup, and an
  email already registered with a password. Existing records must not be overwritten.
- Inspect `meds.users` for the Google patient; no Google credential is stored.

## Firebase notifications (next stage)

Google sign-in does not configure FCM. For notifications, supply the backend
`FIREBASE_SERVICE_ACCOUNT_JSON` and frontend Firebase web configuration plus
`VITE_FIREBASE_VAPID_KEY`. Use the same Firebase project, localhost or HTTPS,
and grant browser notification permission. No service-account key belongs in
frontend environment variables. Real delivery remains unverified until configured.
