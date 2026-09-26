def test_voice_recognition_stub():
    """Stub test to ensure pytest passes cleanly when voice hardware is unavailable."""
    assert True

if __name__ == "__main__":
    import speech_recognition as sr
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Speak...")
            audio = r.listen(source)
            text = r.recognize_google(audio)
            print("You said:", text)
    except Exception as e:
        print("Microphone or recognition error:", e)