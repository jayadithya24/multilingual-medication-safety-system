import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.services.voice_language import infer_language
from backend.app.routes import voice


@pytest.mark.parametrize("text,language", [
    ("What does Metformin do?", "en"),
    ("Metformin ಇದು ಏನು ಮಾಡುತ್ತದೆ", "kn"),
    ("Metformin ಉಂದು ದಾದ ಮಲ್ಪುಂಡ್", "tulu"),
    ("Metformin undu dada malpund", "tulu"),
    ("Metformin idu enu maduttade", "kn"),
    ("play metformin buggy mahiti beko", "kn"),
    ("Metformin bagge maahiti beku", "kn"),
    ("ಮೆಟ್ಫಾರ್ಮಿನ್ ಬಗ್ಗೆ ಮಾಹಿತಿ ಬೇಕು", "kn"),
    ("Metformin mahiti", None),
    ("enk amlodopine da bagge mahiti bodu", "tulu"),
    ("ಎಂಕ್ Amlodipine ಬಗ್ಗೆ ಮಾಹಿತಿ ಬೋಡು", "tulu"),
    ("Amlodipine bagge mahiti", None),
    ("ಎಂಗ್ ಆಮ್ ರೋಡ್ ಇಸ್ ಇನ್ ದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಬೋರ್ಡು", None),
    ("Metformin", None),
    ("ಮೆಟ್ಫಾರ್ಮಿನ್", None),
    ("ಟೈಪ್ 2 ಮಧುಮೇಹ", None),
    ("", None),
    ("what does Metformin do / Metformin ಉಂದು ದಾದ ಮಲ್ಪುಂಡ್", None),
])
def test_language_evidence(text, language):
    assert infer_language(text) == language


@pytest.mark.parametrize("language", ["en", "kn", "tulu"])
def test_manual_selection_overrides_detection(language):
    assert infer_language("Metformin", language) == language


@pytest.mark.parametrize("transcript,expected", [
    ("enk amlodopine da bagge mahiti bodu", "tulu"),
    ("play metformin buggy mahiti beko", "kn"),
    ("What does Metformin do", "en"),
    ("Metformin ಇದು ಏನು ಮಾಡುತ್ತದೆ", "kn"),
    ("Metformin ಉಂದು ದಾದ ಮಲ್ಪುಂಡ್", "tulu"),
    ("Metformin", None),
])
def test_auto_route_uses_detected_dataset(monkeypatch, tmp_path, transcript, expected):
    uploaded = tmp_path / "input.wav"
    uploaded.write_bytes(b"sample")
    monkeypatch.setattr(voice, "save_uploaded_file", lambda _: str(uploaded))
    monkeypatch.setattr(voice, "transcribe_audio", lambda *args: transcript)
    app = FastAPI()
    app.include_router(voice.router)
    with TestClient(app) as client:
        response = client.post("/voice-search", files={"file": ("sample.wav", b"sample")})
    assert response.status_code == 200
    body = response.json()
    assert body["response_language"] == expected
    if expected:
        assert body["status"] == "success"
        assert body["medicine_details"]["lang"] == expected
    else:
        assert body["status"] == "language_uncertain"
        assert not body.get("response_text")
    assert not uploaded.exists()
