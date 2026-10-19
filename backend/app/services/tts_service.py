import asyncio
import logging
import re
from functools import lru_cache
import edge_tts

FEMALE_VOICES = {"en": "en-IN-NeerjaNeural", "kn": "kn-IN-SapnaNeural", "tulu": "kn-IN-SapnaNeural"}
# User-provided pronunciations, applied to speech only. Never alter stored doses.
TULU_NUMBERS = dict(zip(range(1, 11), ["ಒಂಜಿ", "ರಡ್ಡ್", "ಮೂಜಿ", "ನಾಲ್", "ಐನ್", "ಆಜಿ", "ಎಲ್", "ಎನ್ಮ", "ಒರ್ಮ", "ಪಾತ್"]))


def prepare_speech_text(text, language):
    if language != "tulu":
        return text
    # Whole numbers only: preserve decimals, compound numbers, B12 and identifiers.
    return re.sub(r"(?<![\w.,])(?:10|[1-9])(?!\w|[.,]\d)",
                  lambda match: TULU_NUMBERS[int(match.group())], text)


async def _female_audio(clean_text, voice):
    stream = edge_tts.Communicate(clean_text, voice, rate="+0%", connect_timeout=5, receive_timeout=15)
    chunks = [chunk["data"] async for chunk in stream.stream() if chunk["type"] == "audio"]
    if not chunks:
        raise RuntimeError("No speech audio returned")
    return b"".join(chunks)


@lru_cache(maxsize=128)
def _synthesize(clean_text, language):
    # Repeated medicine responses reuse audio; unsuccessful requests are not cached.
    return asyncio.run(asyncio.wait_for(_female_audio(clean_text, FEMALE_VOICES[language]), timeout=25))


def generate_tts_audio(text: str, lang: str = "en"):
    """Use explicitly selected female voices consistently across patient pages."""
    clean_text = (text or "").strip()
    if not clean_text:
        clean_text = "No medicine information available."

    lang = "tulu" if lang in ("tlu", "te") else lang
    if lang not in FEMALE_VOICES:
        lang = "en"

    try:
        return _synthesize(prepare_speech_text(clean_text, lang), lang)
    except Exception as err:
        logging.getLogger(__name__).warning("Female speech unavailable (%s)", type(err).__name__)
        return None
