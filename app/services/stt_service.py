import io
import os
import speech_recognition as sr
from gtts import gTTS

def convert_speech_to_text(audio_bytes: bytes, lang: str = "kn") -> str:
    """
    Converts audio bytes (WAV/FLAC) to text using SpeechRecognition (Google Speech API).
    Supports 'kn-IN' (Kannada), 'en-IN' (English), and fallbacks for Tulu.
    """
    recognizer = sr.Recognizer()
    
    # Map language codes to Google STT locale tags
    lang_map = {
        "kn": "kn-IN",
        "tlu": "kn-IN",  # Fallback to Kannada acoustic model for Tulu phonetics
        "en": "en-IN"
    }
    target_lang = lang_map.get(lang.lower(), "en-IN")

    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=target_lang)
            return text.strip()
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"[STT ERROR]: {e}")
        return ""


def text_to_speech_stream(text: str, lang: str = "kn") -> bytes:
    """
    Converts text response to MP3 audio stream bytes using gTTS.
    Catches errors and returns empty MP3 fallback bytes to prevent HTTP header crashes.
    """
    if not text or not text.strip():
        text = "No response text provided."

    gtts_lang = "kn" if lang in ["kn", "tlu"] else "en"

    try:
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        print(f"[TTS GENERATION ERROR]: {e}")
        # Fallback to English if regional language synthesis fails
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception:
            return b""