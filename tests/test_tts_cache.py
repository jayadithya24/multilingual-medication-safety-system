from backend.app.services import tts_service


def test_repeated_speech_reuses_audio(monkeypatch):
    calls = []
    class Speech:
        def __init__(self, **kwargs):
            calls.append(kwargs)
        def write_to_fp(self, stream):
            stream.write(b'audio')
    monkeypatch.setattr(tts_service, 'gTTS', Speech)
    tts_service._synthesize.cache_clear()
    try:
        assert tts_service.generate_tts_audio('Medicine information', 'kn') == b'audio'
        assert tts_service.generate_tts_audio('Medicine information', 'kn') == b'audio'
        assert len(calls) == 1
        assert calls[0]['timeout'] == (3, 8)
    finally:
        tts_service._synthesize.cache_clear()


def test_tts_failure_is_not_cached(monkeypatch):
    calls = []
    def fail(**kwargs):
        calls.append(kwargs)
        raise RuntimeError('offline')
    monkeypatch.setattr(tts_service, 'gTTS', fail)
    tts_service._synthesize.cache_clear()
    assert tts_service.generate_tts_audio('Retry information') is None
    assert tts_service.generate_tts_audio('Retry information') is None
    assert len(calls) == 2
