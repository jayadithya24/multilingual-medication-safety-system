# Saved speech fixture

`metformin-en.wav` and its MP3 source contain the word “Metformin”, generated
with Google TTS (`lang=en`, `tld=co.in`). The WAV is mono 16-bit PCM at 16 kHz.
It contains synthetic speech, not a patient recording.

Run a real backend recognition check with:

```powershell
rtk proxy .venv-1/Scripts/python.exe test_backend.py --audio tests/fixtures/voice/metformin-en.wav --lang en
rtk proxy .venv-1/Scripts/python.exe tests/voice_browser_check.py
```

The browser check exercises language selection/localized results in English,
Kannada, and Tulu using this English medicine name. It does not establish
Kannada or Tulu speech recognition accuracy. A native speaker must validate
those languages and audible speech output with the physical microphone.
