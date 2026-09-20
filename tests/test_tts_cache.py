from backend.app.services import tts_service


def test_repeated_speech_reuses_audio(monkeypatch):
    calls = []
    async def speech(text, voice):
        calls.append((text, voice))
        return b'audio'
    monkeypatch.setattr(tts_service, '_female_audio', speech)
    tts_service._synthesize.cache_clear()
    try:
        assert tts_service.generate_tts_audio('Medicine information', 'kn') == b'audio'
        assert tts_service.generate_tts_audio('Medicine information', 'kn') == b'audio'
        assert len(calls) == 1
        assert calls[0][1] == 'kn-IN-SapnaNeural'
    finally:
        tts_service._synthesize.cache_clear()


def test_tts_failure_is_not_cached(monkeypatch):
    calls = []
    async def fail(text, voice):
        calls.append((text, voice))
        raise RuntimeError('offline')
    monkeypatch.setattr(tts_service, '_female_audio', fail)
    tts_service._synthesize.cache_clear()
    assert tts_service.generate_tts_audio('Retry information') is None
    assert tts_service.generate_tts_audio('Retry information') is None
    assert len(calls) == 2


def test_user_tulu_numbers_preserve_doses_and_identifiers():
    assert tts_service.prepare_speech_text('1 2 3 4 5 6 7 8 9 10', 'tulu') == 'ಒಂಜಿ ರಡ್ಡ್ ಮೂಜಿ ನಾಲ್ ಐನ್ ಆಜಿ ಏಳ್ ಎನ್ಮ ಒರ್ಮ ಪತ್'
    unchanged = '500 mg, 2.5 mg, 1,000 mg, B12, 12, 20, 100, 5mg'
    assert tts_service.prepare_speech_text(unchanged, 'tulu') == unchanged
    assert tts_service.prepare_speech_text('Type 2. Take 1 tablet.', 'tulu') == 'Type ರಡ್ಡ್. Take ಒಂಜಿ tablet.'
    assert tts_service.prepare_speech_text('1 2 10', 'en') == '1 2 10'


def test_voice_selection_for_every_language(monkeypatch):
    calls = []
    async def speech(text, voice):
        calls.append(voice)
        return b'audio'
    monkeypatch.setattr(tts_service, '_female_audio', speech)
    tts_service._synthesize.cache_clear()
    try:
        for language in ('en', 'kn', 'tulu'):
            assert tts_service.generate_tts_audio('voice check', language)
        assert calls == ['en-IN-NeerjaNeural', 'kn-IN-SapnaNeural', 'kn-IN-SapnaNeural']
    finally:
        tts_service._synthesize.cache_clear()
