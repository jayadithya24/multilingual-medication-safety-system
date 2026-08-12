import io
from gtts import gTTS


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
        tts = gTTS(text=clean_text, lang=gtts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as err:
        print(f"TTS generation error: {err}")
        return None
