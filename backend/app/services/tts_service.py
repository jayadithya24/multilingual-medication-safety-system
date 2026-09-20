import io
from functools import lru_cache
from gtts import gTTS


@lru_cache(maxsize=128)
def _synthesize(clean_text, language):
    # Repeated medicine responses reuse audio; unsuccessful requests are not cached.
    tts = gTTS(text=clean_text, lang=language, slow=False, timeout=(3, 8))
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()


def generate_tts_audio(text: str, lang: str = "en"):
    """Generate MP3 audio bytes using gTTS for English, Kannada, and Tulu."""
    clean_text = (text or "").strip()
    if not clean_text:
        clean_text = "No medicine information available."

    # Map application languages to gTTS language codes
    # Tulu uses Kannada script (kn) in gTTS if tulu isn't natively supported by gTTS
    gtts_lang = "en"
    if lang in ["kn", "tulu"]:
        gtts_lang = "kn"

    try:
        return _synthesize(clean_text, gtts_lang)
    except Exception as err:
        print(f"TTS generation error: {err}")
        return None
