import numpy as np
from backend.app.services import ocr_service as service


def test_unrelated_text_does_not_skip_enlarged_fallback(monkeypatch):
    monkeypatch.setattr(service.cv2, "imread", lambda *args: np.zeros((260, 440, 3), dtype=np.uint8))
    monkeypatch.setattr(service, "list_medicine_names", lambda **kwargs: ["Losartan"])
    shapes = []
    class Reader:
        def predict(self, input):
            shapes.append(input.shape)
            text = "Colo" if len(shapes) == 1 else "Losartan Potassium 50 mg"
            return [{"rec_texts": [text], "rec_scores": [0.95]}]
    result = service._read_detected_text(Reader(), "synthetic.png")
    assert len(shapes) == 2
    assert shapes[1][1] > shapes[0][1]
    assert service._find_supported_medicine(" ".join(result), ["Losartan"]) == "Losartan"


def test_clear_medicine_does_not_require_second_pass(monkeypatch):
    monkeypatch.setattr(service.cv2, "imread", lambda *args: np.zeros((260, 440, 3), dtype=np.uint8))
    monkeypatch.setattr(service, "list_medicine_names", lambda **kwargs: ["Losartan"])
    calls = []
    class Reader:
        def predict(self, input):
            calls.append(1)
            return [{"rec_texts": ["Losartan"], "rec_scores": [0.95]}]
    service._read_detected_text(Reader(), "synthetic.png")
    assert len(calls) == 1


def test_combination_preserves_both_ingredients_without_single_dose(monkeypatch, tmp_path):
    path = tmp_path / "pack.png"
    path.write_bytes(b"test")
    monkeypatch.setattr(service, "_get_reader", lambda: object())
    monkeypatch.setattr(service, "_read_detected_text", lambda *args: ["Losartan Potassium 50 mg and Hydrochlorothiazide 12.5 mg"])
    result = service.extract_prescription_details(str(path))
    assert result["all_detected_medicines"] == ["Losartan", "Hydrochlorothiazide"]
    assert result["medicine"] == "Losartan + Hydrochlorothiazide"
    assert result["dosage"] is None
