# HTTPS reverse-proxy verification

This test uses a real portable Caddy reverse proxy, two real Uvicorn processes
and an isolated database on the configured MongoDB server. It does not use
TestClient, mongomock or an in-memory production limiter.

## Recorded local result, 24 October 2026

Run `6df53f18de931ef5` passed all assertions below using Caddy v2.11.7,
two Uvicorn processes and real MongoDB. Its report is
`artifacts/proxy-test/6df53f18de931ef5/results.json`.
Both processes stopped, the temporary key was deleted and no test collections
remained. MongoDB denied dropDatabase, so cleanup used the permitted collection
drops instead. The first run had passed its security assertions but reported a
cleanup failure; its records were subsequently removed before this complete run.
No cloud deployment, physical-phone test or publicly trusted certificate was involved.

## Run locally on Windows

Use the verified Python environment and existing MongoDB credentials. The test
account must be allowed to create and remove its own disposable database.

```powershell
.venv-review/Scripts/python.exe tools/fetch_proxy_test_caddy.py
.venv-review/Scripts/python.exe tools/verify_https_proxy.py
```

The fetcher downloads Caddy v2.11.7 from the official release, verifies the
published checksum and GitHub asset digest when present, and extracts only
`caddy.exe` into ignored artifacts. The harness also accepts `--caddy PATH` for
a separately verified executable.

All listeners bind to loopback: HTTPS proxy 18443 and backends 18081/18082.
The harness refuses occupied ports rather than stopping an existing service.
Each run creates a random `mmss_proxy_probe_*` database and refuses to reuse a
nonempty database. Existing application data and the usual demo servers are
untouched. The parent process stops only the test processes it started and
removes only that run's database. Check the cleanup flags in the result.

The generated certificate expires after one day. Requests verifies it using
that specific certificate file; `verify=False` is never used. No certificate
is added to the Windows trust store. The private key is deleted at teardown.
No public tunnel, DNS record or internet-facing listener is created.

## Assertions

1. TLS verifies, and round-robin traffic reaches both backend processes.
2. Clients bound to 127.0.0.2 and 127.0.0.3 retain distinct source identities
   through the proxy. These represent separate local clients, not two physical
   networks or a mobile-carrier test.
3. Caddy replaces client-supplied X-Forwarded-For/Proto and removes Forwarded.
   Spoofing headers cannot change the backend's observed client or HTTPS scheme.
4. Uvicorn is explicitly started with `--proxy-headers` and
   `--forwarded-allow-ips 127.0.0.1`. A direct request from 127.0.0.2 cannot
   spoof its source address or scheme with forwarding headers.
5. A fictional patient can sign in over HTTPS. The cookie is Secure, HttpOnly
   and SameSite=Strict and works across both processes. Missing/untrusted
   origins receive 403; allowed logout revokes the session.
6. Twenty anonymous voice requests are counted across both processes using
   real MongoDB counters. They intentionally omit an upload, so validation
   returns 422 without running Whisper. The next request is 429 even with a
   spoofed forwarding header. The other client address retains its own quota.
7. In a separate quota case, three seeded session identities share 60 permitted
   heavy-route requests. A fourth identity from the same source receives 429,
   while the second source remains independent. This tests the aggregate source
   ceiling against real MongoDB across both workers. These are seeded identities,
   not new registrations or email-verification tests.
8. Every run records whether its processes stopped and database was removed.
   If dropDatabase is forbidden, cleanup removes only that run's collections;
   if collection drops are also forbidden, it empties and verifies the test
   records and reports any remaining empty collections explicitly.

The probe endpoint exists only in `tests/proxy_probe_app.py`, which refuses a
non-test database. Normal `backend.main:app` does not expose it. No production
routes, limits, auth rules or secrets are changed by this test.

Artifacts are under `artifacts/proxy-test/<run-id>/`: configuration, certificate,
server logs and `results.json`. Results omit passwords, cookies and the Mongo URI.
Counter checks deliberately avoid crossing the fixed minute boundary; if a
slow run crosses it, the harness fails instead of claiming a shared-quota pass.

## Repeat at the deployment boundary

A local pass proves this tested configuration, not a future cloud deployment.
Before real patient traffic:

- Use the intended hostname and publicly trusted HTTPS chain. Verify the
  certificate without disabling verification.
- Configure Uvicorn to trust only the actual proxy address(es). Do not copy
  the local loopback trust setting to a different topology or use `*`.
- Confirm the proxy overwrites forwarding headers and the backend port cannot
  be reached externally. Local loopback binding does not test cloud firewalls.
- From two real networks, repeat forged-header and independent-quota checks
  against a staging database, with at least two backend workers.
- Repeat secure-cookie, CSRF, logout/revocation and shared-counter checks.
  Check the proxy's own upload limits/timeouts as well as application limits.
- Connect rate-limit and login-monitoring events to operational alerts, then
  remove staging users and captured tokens. Do not retain real patient data in
  test logs.

Physical-phone reminders, real Google sign-in and native-speaker/pharmacist
review are separate verification tasks and are not covered by this test.

Configuration references:
[Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[Uvicorn settings](https://www.uvicorn.org/settings/),
[pinned Caddy release](https://github.com/caddyserver/caddy/releases/tag/v2.11.7).
