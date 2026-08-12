from functools import lru_cache

from app.services.medicine_service import search_medicine
from app.utils.text_cleaner import clean_detected_text


@lru_cache(maxsize=1)
def _get_whisper_model():
    try:
        import whisper

        return whisper.load_model("base")
    except Exception:
        return None


def _transcribe_with_whisper(file_path):
    model = _get_whisper_model()
    if model is None:
        return None

    transcription = model.transcribe(file_path, fp16=False)
    return transcription.get("text", "").strip()


def _transcribe_with_speech_recognition(file_path):
    try:
        import speech_recognition as sr
    except Exception:
        return None

    recognizer = sr.Recognizer()

    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio_data).strip()
    except Exception:
        return None


def transcribe_audio(file_path):
    """Transcribe an audio file using Whisper first, then SpeechRecognition as fallback."""

    text = _transcribe_with_whisper(file_path)
    if text:
        return text

    text = _transcribe_with_speech_recognition(file_path)
    if text:
        return text

    return ""


def search_medicine_from_transcript(transcript_text):
    """Clean transcript text and search the medicine dataset using the shared medicine service."""

    if not transcript_text:
        return None, []

    cleaned_words = clean_detected_text([transcript_text])
    candidates = []

    joined_phrase = " ".join(cleaned_words).strip()
    if joined_phrase:
        candidates.append(joined_phrase)

    candidates.extend(cleaned_words)

    seen_candidates = set()
    for candidate in candidates:
        normalized_candidate = candidate.strip().lower()
        if not normalized_candidate or normalized_candidate in seen_candidates:
            continue

        seen_candidates.add(normalized_candidate)
        medicine = search_medicine(normalized_candidate)
        if medicine:
            return medicine, cleaned_words

    return None, cleaned_words