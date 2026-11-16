# Deployment prerequisites

The current verification is a local prototype, not production certification.

## Runtime and network

Start production with `python tools/start_production.py`. This entrypoint runs
preflight automatically and refuses to start on a nonzero result. It binds the
backend to loopback port 8000 for a same-host reverse proxy and disables access
logging. Do not replace it with an unchecked Uvicorn command in deployment.
The standalone `python tools/deploy_preflight.py` remains available for checks.
It rejects forgotten production mode, invalid HTTPS
origins, mocked databases, missing Mongo configuration and research-API opt-in.
The backend also prints a development-mode startup warning when appropriate.
This configuration gate does not validate the real proxy or certify production readiness.
It also rejects empty/wildcard `FORWARDED_ALLOW_IPS`, missing Mongo URI credentials,
disabled TLS and disabled certificate/hostname verification. Deployment must still
verify that the configured proxy addresses are actually trusted.

The [local HTTPS proxy test](HTTPS_PROXY_TEST.md) passed on 24 October using
Caddy, two backend processes and real MongoDB counters. Repeat its deployment
checklist through the actual public proxy, network restrictions and certificate
chain before launch; loopback success does not verify those external controls.

- Use Python 3.13 and the single pinned root `requirements.txt`.
  `backend/requirements.txt` delegates to it; test dependencies are separate.
  Regenerate with `uv pip compile requirements.in --python-version 3.13 -o requirements.txt`.
  Keep only `opencv-contrib-python`, required by PaddleOCR; installing another
  OpenCV distribution alongside it overwrites the same `cv2` namespace.
- Set `ENVIRONMENT=production`. This refuses mongomock, forces shared MongoDB
  rate counters, disables research ML routes and requires HTTPS session cookies.
  Startup also rejects missing, non-HTTPS or non-origin `BROWSER_ORIGINS` values.
- Terminate HTTPS at a controlled reverse proxy. Configure exact
  `BROWSER_ORIGINS` and restrict the backend to the proxy's private interface.
- Local Uvicorn uses `--no-proxy-headers`. Behind a proxy, enable proxy headers
  only with `--forwarded-allow-ips` set to the exact trusted proxy addresses.
  Never use `*`. The proxy must replace incoming forwarded headers. The ASGI
  client address becomes the application rate-limit key; test independent
  clients through the actual deployed proxy before launch.
- Protect MongoDB and Neo4j from public network access, use least-privilege
  credentials, and test backup restoration. Supply secrets through deployment
  secret storage rather than source files or a container image.
- Configure monitoring, failure alerts and log access controls. Do not log
  request bodies, cookies, authorization headers, share codes or passwords.

## Authentication and retained data

Authentication is cookie-only: HttpOnly, SameSite=Strict, Secure in production,
exact Origin checks on unsafe methods, revocable hashed server sessions,
30-minute sliding idle expiry and eight-hour absolute expiry. Background polls
do not keep a session alive. Production public-route counters and account/source
password-attempt counters are shared in MongoDB. Passwords are capped at 72 UTF-8
bytes in both patient and doctor registration (not merely 72 characters).

Password attempts allow eight per normalized account and client address per
15-minute window. A separate cross-IP account counter emits one
`distributed_login_threshold` warning and marks its counter for monitoring at
32 attempts in that window. It counts attempts, not confirmed attacks, and logs
only a one-way account hash. Connect this event to operational monitoring; no
owner email, automatic MFA challenge or global lockout is implemented.
Alert configuration pending: match the exact `distributed_login_threshold` event,
group by account hash and 15-minute window, and notify a monitored destination
once per group. Include time and service identity, never usernames or request
bodies. Verify delivery with a synthetic test event before enabling real users.
No destination is currently available, so external alert delivery is unverified.
They do not globally lock a username: a stranger should not
be able to deny that user login from every network. This trades away protection
against attempts distributed across many IPs; MFA and attack monitoring remain
required deployment work. The source auth budget is 60 requests/minute.

Verified signed-in users have separate quotas, keyed by their database session's
username without extending session expiry. Invalid/expired cookies fall back to
the source IP. Anonymous analysis budgets are 300/minute per category; signed-in
budgets are 120/minute. Catalog, graph, interaction, TTS and health have separate
categories. Expensive OCR/voice uploads remain 20/minute per user or anonymous IP.
All heavy requests additionally consume a 60/minute source-IP budget before
session lookup, so changing accounts cannot reset it. Registration attempts
share a 30/hour source-IP cap across patient registration, doctor application
aliases and Google requests explicitly using `mode=register`. Failed registration
attempts count too. Google login mode and ordinary password login do not consume
the registration cap. These counters are shared in MongoDB in production.
The cap was raised from 10 to 30 to give shared networks more room for retries;
it remains an attempt cap, not a count of successfully created accounts.
Anonymous clients sharing a NAT can still share a quota; validate actual usage
and trusted-proxy addresses before launch. Every non-upload request body is
capped at 64 KiB; upload routes allow 10 MiB including multipart overhead.

Before handling real patient data, implement and verify email ownership,
password recovery/change, doctor/admin MFA, account deletion, and a reviewed
consent notice and retention policy. These are not implemented by this pass.
Access-log read/identical-denial deduplication and pagination do not constitute a retention
policy; security events are not automatically deleted.

## Content and release boundaries

DDInter's [published terms](https://ddinter.scbdd.com/terms/) specify
CC BY-NC-SA 4.0. Keep its data and research artifacts out of a commercial release
unless suitable permission is obtained. Do not assume a separate project
dataset license overrides third-party terms. The `.dockerignore` excludes
research models/data, secrets, tests and local artifacts; there is no verified
production image or deployment in this change.

Require native-speaker/pharmacist review of the language checklist, missing
Tulu classes, generic narratives and any proposed brand/combination mapping.
No guessed translations, brand mappings or cumulative clinical rules were added.
The medicine autocomplete suggests catalog names but preserves unlisted text
with a coverage warning; it does not convert brands.

Verify scheduled Firebase delivery on a physical phone and Google sign-in with
a real account. A running worker, mocked Google tests and notification-token
storage are not substitutes for those checks.
