import os
from functools import lru_cache
from difflib import SequenceMatcher
import logging
import re
import subprocess
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from backend.app.services.voice_language import infer_language

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
        with wave.open(file_path, "rb") as audio:
            if (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (16000, 1, 2):
                return file_path
    except (wave.Error, EOFError):
        pass

    try:
        ffmpeg_path = _ensure_ffmpeg_on_path()
    except Exception as err:
        logger.exception("FFmpeg is unavailable for audio processing: %s", err)
        return None

    converted_path = None
    try:
        descriptor, converted_path = tempfile.mkstemp(suffix=".wav")
        os.close(descriptor)
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
                "-c:a",
                "pcm_s16le",
                converted_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        return converted_path
    except Exception as err:
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        logger.exception("Audio conversion failed for %s: %s", file_path, err)
        return None


@lru_cache(maxsize=1)
def _get_whisper_model():
    try:
        import whisper

        return whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    except Exception as err:
        logger.exception("Whisper initialization failed: %s", err)
        return None


def _transcribe_with_whisper(file_path, lang="en"):
    model = _get_whisper_model()
    if model is None:
        return None

    whisper_language = {"en": "en", "kn": "kn"}.get(lang)

    options = {
        "fp16": False,
        "temperature": 0,
    }

    if whisper_language:
        options["language"] = whisper_language

    # Give Whisper the medicine vocabulary used by our system.
    try:
        medicine_names = list_medicine_names(lang=lang)
        medicine_prompt = ", ".join(
            str(name).strip()
            for name in medicine_names
            if str(name).strip()
        )

        if medicine_prompt:
            options["initial_prompt"] = (
                "Medicine names: " + medicine_prompt
            )
    except Exception as err:
        logger.warning(
            "Could not create medicine vocabulary prompt: %s",
            err,
        )

    try:
        with wave.open(file_path, "rb") as audio_file:
            audio_bytes = audio_file.readframes(
                audio_file.getnframes()
            )

            audio = (
                np.frombuffer(
                    audio_bytes,
                    dtype=np.int16,
                )
                .astype(np.float32)
                / 32768.0
            )

            if audio_file.getnchannels() > 1:
                audio = audio.reshape(
                    -1,
                    audio_file.getnchannels(),
                ).mean(axis=1)

        transcription = model.transcribe(
            audio,
            **options,
        )

        return transcription.get(
            "text",
            "",
        ).strip()

    except Exception as err:
        logger.exception(
            "Whisper transcription failed for %s: %s",
            file_path,
            err,
        )
        return None


def _transcribe_with_speech_recognition(file_path, lang="en"):
    try:
        import speech_recognition as sr
    except Exception:
        return None

    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 5

    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)

    try:
        google_languages = {
            "en": ["en-IN"],
            "kn": ["kn-IN", "en-IN"],
            "tulu": ["tcy-IN", "kn-IN", "en-IN"],
            "auto": ["tcy-IN", "kn-IN", "en-IN"],
        }.get(lang, ["en-IN"])
        first_transcript = None
        candidates = []
        def recognize_candidate(locale):
            try:
                worker = sr.Recognizer()
                worker.operation_timeout = 5
                return worker.recognize_google(audio_data, language=locale).strip()
            except Exception as err:
                logger.warning("SpeechRecognition failed for %s: %s", locale, err)
                return ""

        # Auto mode needs all candidates to detect conflicting language evidence.
        # Run independent network requests together rather than serially.
        auto_transcripts = None
        if lang == "auto":
            with ThreadPoolExecutor(max_workers=3) as pool:
                auto_transcripts = dict(zip(google_languages, pool.map(recognize_candidate, google_languages)))
        for google_language in google_languages:
            try:
                transcript = auto_transcripts[google_language] if auto_transcripts is not None else recognizer.recognize_google(audio_data, language=google_language).strip()
                if transcript:
                    if first_transcript is None:
                        first_transcript = transcript
                    detected = infer_language(transcript, lang)
                    medicine, _ = search_medicine_from_transcript(transcript, lang=detected or "en")
                    if lang == "auto":
                        candidates.append((transcript, detected, bool(medicine)))
                        continue
                    if medicine or len(google_languages) == 1:
                        return transcript
            except Exception as err:
                logger.warning("SpeechRecognition failed for %s: %s", google_language, err)
        if candidates:
            # Retain language-bearing phrases instead of stopping at the first
            # recognizer that happens to recognize a medicine name.
            languages = {detected for _, detected, _ in candidates if detected}
            if len(languages) > 1:
                # Conflicting evidence must reach the clarification path.
                return " / ".join(text for text, _, _ in candidates)
            return max(candidates, key=lambda item: (bool(item[1]), item[2]))[0]
        return first_transcript
    except Exception as err:
        logger.warning("SpeechRecognition transcription failed: %s", err)
        return None


def transcribe_audio(file_path, lang="en"):
    """Transcribe audio with the fastest suitable backend for the selected language."""
    transcription_path = _convert_audio_for_transcription(file_path)
    if not transcription_path:
        return ""

    try:
        for transcriber in (_transcribe_with_speech_recognition, _transcribe_with_whisper):
            try:
                text = transcriber(transcription_path, lang=lang)
                if text and text.strip():
                    return text.strip()
            except Exception as err:
                logger.exception("Voice transcription failed safely: %s", err)
        return ""
    finally:
        if transcription_path != file_path:
            os.remove(transcription_path)


def detect_transcript_language(transcript_text, requested_lang=None):
    return infer_language(transcript_text, requested_lang)


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
    words = re.findall(r"[a-z]+|[\u0c80-\u0cff\u200c\u200d]+", normalized_text)
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
    """
    Match a spoken/transcribed medicine name against the
    medicines that actually exist in our dataset.

    This tolerates common Whisper speech-to-text mistakes
    such as:
        ibuprofen -> aibo profin
        paracetamol -> paracitamol
        cetirizine -> cetrizine
    """

    known_medicines = list_medicine_names(lang=lang)

    if not known_medicines:
        return None

    normalized_text = str(
        transcript_text or ""
    ).lower().strip()

    if not normalized_text:
        return None

    # Create possible spoken candidates.
    spoken_candidates = [
        word
        for word in re.findall(
            r"[a-z0-9]+",
            normalized_text,
        )
        if len(word) >= 4
        and word not in VOICE_STOP_WORDS
    ]

    # Also test the complete transcription.
    spoken_candidates.append(normalized_text)

    # Test combinations of neighboring words.
    words = re.findall(
        r"[a-z0-9]+",
        normalized_text,
    )

    for i in range(len(words)):
        for j in range(i + 1, min(i + 4, len(words) + 1)):
            phrase = " ".join(words[i:j])

            if len(phrase) >= 4:
                spoken_candidates.append(phrase)

    # Remove duplicates while preserving order.
    spoken_candidates = list(
        dict.fromkeys(spoken_candidates)
    )

    best_match = None
    best_score = 0.0

    for medicine in known_medicines:

        normalized_medicine = _normalize_spoken_name(
            medicine
        )

        if len(normalized_medicine) < 4:
            continue

        for candidate in spoken_candidates:

            normalized_candidate = _normalize_spoken_name(
                candidate
            )

            if len(normalized_candidate) < 4:
                continue

            score = SequenceMatcher(
                None,
                normalized_candidate,
                normalized_medicine,
            ).ratio()

            if score > best_score:
                best_score = score
                best_match = medicine

    logger.info(
        "Voice fuzzy matching: transcript=%r best_match=%r score=%.3f",
        transcript_text,
        best_match,
        best_score,
    )

    # More tolerant threshold for speech-recognition errors.
    if best_match and best_score >= 0.65:
        medicine = search_medicine(
            best_match,
            lang=lang,
        )

        if medicine:
            return medicine

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
