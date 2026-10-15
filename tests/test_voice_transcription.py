"""Offline checks; recognizers are mocked, so these do not measure speech accuracy."""
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from backend.app.services import voice_search_service as service


class VoiceTests(unittest.TestCase):
    def test_local_recognition_retries_english_medicine_name(self):
        import speech_recognition as sr
        sample = Path(__file__).parent / "fixtures/voice/metformin-en.wav"
        with patch.object(sr.Recognizer, "recognize_google", side_effect=["unrecognized words", "Metformin"]) as recognize:
            self.assertEqual(service._transcribe_with_speech_recognition(str(sample), "kn"), "Metformin")
            self.assertEqual([call.kwargs["language"] for call in recognize.call_args_list], ["kn-IN", "en-IN"])

    def test_unmatched_transcript_is_preserved(self):
        import speech_recognition as sr
        sample = Path(__file__).parent / "fixtures/voice/metformin-en.wav"
        with patch.object(sr.Recognizer, "recognize_google", side_effect=["unrecognized words", "other words"]):
            self.assertEqual(service._transcribe_with_speech_recognition(str(sample), "kn"), "unrecognized words")

    def test_google_first_in_all_languages(self):
        for lang in ("en", "kn", "tulu", "auto"):
            with self.subTest(lang=lang), patch.object(service, "_convert_audio_for_transcription", return_value="input.wav"), patch.object(service, "_transcribe_with_speech_recognition", return_value=" Metformin ") as google, patch.object(service, "_transcribe_with_whisper") as whisper:
                self.assertEqual(service.transcribe_audio("input.wav", lang), "Metformin")
                google.assert_called_once_with("input.wav", lang=lang)
                whisper.assert_not_called()

    def test_fallback_and_cleanup(self):
        for result in ("Metformin", None, RuntimeError("unavailable")):
            with self.subTest(result=result), tempfile.TemporaryDirectory() as directory:
                converted = Path(directory) / "converted.wav"
                converted.touch()
                with patch.object(service, "_convert_audio_for_transcription", return_value=str(converted)), patch.object(service, "_transcribe_with_speech_recognition", return_value=None) as google, patch.object(service, "_transcribe_with_whisper", return_value=result, side_effect=result if isinstance(result, Exception) else None):
                    self.assertEqual(service.transcribe_audio("input.webm"), result if isinstance(result, str) else "")
                    google.assert_called_once()
                self.assertFalse(converted.exists())

    def test_wav_format_handling(self):
        for rate in (16000, 44100):
            with self.subTest(rate=rate), tempfile.TemporaryDirectory() as directory:
                source = str(Path(directory) / "sample.wav")
                with wave.open(source, "wb") as audio:
                    audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                    audio.writeframes(b"\x00\x00" * 1600)
                with patch.object(service, "_ensure_ffmpeg_on_path", return_value="ffmpeg") as ffmpeg, patch.object(service.subprocess, "run") as convert:
                    converted = service._convert_audio_for_transcription(source)
                    if rate == 16000:
                        self.assertEqual(converted, source)
                        ffmpeg.assert_not_called()
                    else:
                        try:
                            self.assertNotEqual(converted, source)
                            self.assertIn("pcm_s16le", convert.call_args.args[0])
                            convert.assert_called_once()
                        finally:
                            Path(converted).unlink()


if __name__ == "__main__":
    unittest.main()
