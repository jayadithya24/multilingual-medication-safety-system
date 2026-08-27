import os
from functools import lru_cache
from difflib import SequenceMatcher
import logging
import re
import subprocess
import tempfile
import unicodedata
import wave

import numpy as np

from backend.app.services.medicine_service import _load_dataset, list_medicine_names, search_medicine


logger = logging.getLogger(__name__)

VOICE_STOP_WORDS = {
    "a", "am", "and", "are", "for", "from", "how", "i", "is", "it",
    "me", "medicine", "of", "please", "sugar", "tell", "the", "this",
    "to", "used", "what", "which", "with",
}


def _ensure_ffmpeg_on_path():
    import imageio_ffmpeg

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_directory = os.path.dirname(ffmpeg_path)
    if ffmpeg_directory not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = ffmpeg_directory + os.pathsep + os.environ.get("PATH", "")
    return ffmpeg_path


def _convert_audio_for_transcription(file_path):
    """Convert browser audio to a format both existing transcribers can read."""
    try:
        ffmpeg_path = _ensure_ffmpeg_on_path()
    except Exception as err:
        logger.exception("FFmpeg is unavailable for audio processing: %s", err)
        return None

    if file_path.lower().endswith(".wav"):
        return file_path

    try:
        converted_path = tempfile.mktemp(suffix=".wav")
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-i",
                file_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                converted_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return converted_path
    except Exception as err:
        logger.exception("Audio conversion failed for %s: %s", file_path, err)
        return None


@lru_cache(maxsize=1)
def _get_whisper_model():
    try:
        import whisper

        return whisper.load_model("base")
    except Exception as err:
        logger.exception("Whisper initialization failed: %s", err)
        return None


def _transcribe_with_whisper(file_path, lang="en"):
    model = _get_whisper_model()
    if model is None:
        return None

    whisper_language = {"en": "en", "kn": "kn"}.get(lang)
    options = {"fp16": False}
    if whisper_language:
        options["language"] = whisper_language

    try:
        with wave.open(file_path, "rb") as audio_file:
            audio_bytes = audio_file.readframes(audio_file.getnframes())
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            if audio_file.getnchannels() > 1:
                audio = audio.reshape(-1, audio_file.getnchannels()).mean(axis=1)

        transcription = model.transcribe(audio, **options)
        return transcription.get("text", "").strip()
    except Exception as err:
        logger.exception("Whisper transcription failed for %s: %s", file_path, err)
        return None


def _transcribe_with_speech_recognition(file_path, lang="en"):
    try:
        import speech_recognition as sr
    except Exception:
        return None

    recognizer = sr.Recognizer()

    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)

    try:
        google_languages = {
            "en": ["en-IN"],
            "kn": ["kn-IN"],
            "tulu": ["tcy-IN", "kn-IN"],
            "auto": ["tcy-IN", "kn-IN", "en-IN"],
        }.get(lang, ["en-IN"])
        for google_language in google_languages:
            try:
                transcript = recognizer.recognize_google(audio_data, language=google_language).strip()
                if transcript:
                    return transcript
            except Exception as err:
                logger.warning("SpeechRecognition failed for %s: %s", google_language, err)
        return None
    except Exception as err:
        logger.warning("SpeechRecognition transcription failed: %s", err)
        return None


def transcribe_audio(file_path, lang="en"):
    """Transcribe an audio file using Whisper first, then SpeechRecognition as fallback."""
    transcription_path = _convert_audio_for_transcription(file_path)
    if not transcription_path:
        return ""

    try:
        text = _transcribe_with_whisper(transcription_path, lang=lang)
    except Exception as err:
        logger.exception("Voice transcription failed safely: %s", err)
        text = None
    if text:
        return text

    try:
        text = _transcribe_with_speech_recognition(transcription_path, lang=lang)
    except Exception as err:
        logger.exception("Speech fallback failed safely: %s", err)
        text = None
    if text:
        if transcription_path != file_path:
            os.remove(transcription_path)
        return text

    if transcription_path != file_path:
        os.remove(transcription_path)
    return ""


def detect_transcript_language(transcript_text, requested_lang="en"):
    """Detect language from script and existing Kannada/Tulu dataset vocabulary."""
    requested_lang = requested_lang or "auto"
    if re.search(r"[\u0C80-\u0CFF]", transcript_text or ""):
        if requested_lang in {"kn", "tulu"}:
            return requested_lang

        def dataset_words(lang):
            dataframe = _load_dataset(lang)
            if dataframe is None:
                return set()
            values = dataframe.astype(str).to_string(index=False)
            return {
                unicodedata.normalize("NFKC", word).replace("\u200c", "")
                for word in re.findall(r"[\u0C80-\u0CFF]+", values)
            }

        transcript_words = {
            unicodedata.normalize("NFKC", word).replace("\u200c", "")
            for word in re.findall(r"[\u0C80-\u0CFF]+", transcript_text)
        }
        kannada_words = dataset_words("kn")
        tulu_words = dataset_words("tulu")
        if transcript_words & (tulu_words - kannada_words):
            return "tulu"
        return "kn"

    if re.search(r"[A-Za-z]", transcript_text or ""):
        tulu_cues = {"yenk", "yank", "enk", "matre", "ovu", "ovund", "panle", "matt", "malt"}
        transcript_words = set(re.findall(r"[a-z]+", transcript_text.lower()))
        if len(transcript_words & tulu_cues) >= 2:
            return "tulu"
        return "en"

    return requested_lang or "en"


def find_disease_medicines(transcript_text, lang="en"):
    """Return existing medicines when speech asks for a disease category."""
    normalized_text = str(transcript_text or "").lower()
    if not re.search(r"\bbp\b|blood pressure|ರಕ್ತ|ಒತ್ತಡ", normalized_text):
        return []

    dataframe = _load_dataset(lang)
    if dataframe is None or "disease" not in dataframe.columns:
        return []

    matches = dataframe[
        dataframe["disease"].astype(str).str.contains("ಒತ್ತಡ|pressure|hypertension", case=False, na=False, regex=True)
    ]
    return [search_medicine(name, lang=lang) for name in matches["drug_name"].tolist()]


def _transcript_candidates(transcript_text, lang="en"):
    normalized_text = str(transcript_text).strip().lower()
    words = [word for word in re.findall(r"[^\W\d_]+", normalized_text, flags=re.UNICODE) if word]
    known_medicine_matches = [
        medicine.lower()
        for medicine in list_medicine_names(lang=lang)
        if medicine.lower() in normalized_text
    ]
    candidates = known_medicine_matches + [normalized_text]
    candidates.extend(words)

    return list(dict.fromkeys(candidates))


def _normalize_spoken_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _fuzzy_medicine_match(transcript_text, lang="en"):
    """Match only against known dataset names, tolerating speech spelling errors."""
    known_medicines = list_medicine_names(lang=lang)
    normalized_text = str(transcript_text).lower()
    spoken_candidates = [
        word for word in re.findall(r"[a-z0-9]+", normalized_text)
        if len(word) >= 5 and word not in VOICE_STOP_WORDS
    ]
    spoken_candidates.extend(
        candidate for candidate in _transcript_candidates(transcript_text, lang=lang)
        if " " in candidate
    )
    best_scores = {}

    for candidate in spoken_candidates:
        normalized_candidate = _normalize_spoken_name(candidate)
        if len(normalized_candidate) < 5:
            continue

        for medicine in known_medicines:
            normalized_medicine = _normalize_spoken_name(medicine)
            score = SequenceMatcher(None, normalized_candidate, normalized_medicine).ratio()
            best_scores[medicine] = max(score, best_scores.get(medicine, 0.0))

    ranked_matches = [(score, medicine) for medicine, score in best_scores.items()]
    ranked_matches.sort(reverse=True)
    if ranked_matches:
        best_score, best_match = ranked_matches[0]
        second_score = ranked_matches[1][0] if len(ranked_matches) > 1 else 0.0
        if best_score >= 0.75 and best_score - second_score >= 0.08:
            return search_medicine(best_match, lang=lang)
    return None


def search_medicine_from_transcript(transcript_text, lang: str = "en"):
    """Search the selected existing language dataset without stripping local scripts."""

    if not transcript_text:
        return None, []

    candidates = _transcript_candidates(transcript_text, lang=lang)
    cleaned_words = candidates[1:]

    seen_candidates = set()
    for candidate in candidates:
        normalized_candidate = candidate.strip().lower()
        if (
            not normalized_candidate
            or normalized_candidate in seen_candidates
            or normalized_candidate in VOICE_STOP_WORDS
            or (" " not in normalized_candidate and len(normalized_candidate) < 5)
        ):
            continue

        seen_candidates.add(normalized_candidate)
        medicine = search_medicine(normalized_candidate, lang=lang)
        if medicine:
            return medicine, cleaned_words

    medicine = _fuzzy_medicine_match(transcript_text, lang=lang)
    if medicine:
        return medicine, cleaned_words

    return None, cleaned_words