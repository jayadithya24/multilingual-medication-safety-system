# Voice validation

Validated on 2026-09-19 using `.venv-1` and headless Microsoft Edge.

- Installed pytest, mongomock, and Playwright; reproducible dependencies are in `requirements-test.txt`.
- Eight pytest tests passed, including recognizer fallback, audio normalization,
  temporary-file cleanup, and MongoDB loader checks with an isolated mock client.
- Real Google recognition identified the saved synthetic Metformin WAV.
- Browser upload and five-second simulated microphone recording passed in
  English, Kannada, and Tulu modes: six cases with real transcription, medicine
  lookup, localized result rendering, and observed `speechSynthesis.speak` calls.
- The browser tests first used the updated voice/medicine routers on an isolated
  port 8001 server. The main backend was then restarted on port 8000, and all six
  browser cases passed again against it. The isolated server was stopped.
  These tests use an English
  medicine name in all three modes, not native-language conversation samples.
- Frontend production build and VoiceSearch ESLint passed in the preceding check.

## Kannada playback fix

After physical testing reported silent Kannada browser speech, Kannada/Tulu
responses were switched to the existing backend MP3 generator. A visible audio
player allows manual playback when autoplay is blocked. English retains browser
speech with server audio fallback on error or failure to start.

All six browser scenarios passed again. Kannada/Tulu checks now verify that the
generated audio decodes and its playback time advances, rather than merely
observing a speech API call. This still cannot verify physical speaker output.
Tulu uses Kannada synthesis pronunciation. Updated frontend lint and build passed.

## Repeat the checks

```powershell
rtk proxy .venv-1/Scripts/python.exe -m pytest tests -q
rtk proxy .venv-1/Scripts/python.exe test_backend.py --audio tests/fixtures/voice/metformin-en.wav --lang en
rtk proxy .venv-1/Scripts/python.exe tests/voice_browser_check.py
```

By default the browser check uses the running app on ports 5173 and 8000.
For an isolated API, start `uvicorn voice_test_server:app --app-dir tests --port 8001`
using the project Python and set `VOICE_TEST_API_URL=http://127.0.0.1:8001` for
the browser check process.

## Account and physical-device checks still required

- Rotate the exposed MongoDB password through the Atlas account and update the
  ignored `.env` URI. No Atlas admin credentials or account integration were
  available during this run; the password has not been rotated.
- Enter the actual Neo4j URI/user/password in `.env`. Placeholder passwords are
  now rejected before a connection attempt; actual Neo4j connectivity is unverified.
- A native speaker must record English, Kannada, and Tulu through the physical
  microphone and confirm both recognized medicine and audible output. Automated
  speech-call observation does not establish installed voice quality or audibility.
- Restart the main backend after code or `.env` changes to load them.
