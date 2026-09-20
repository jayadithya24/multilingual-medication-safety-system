"""Live browser check using synthetic speech, real MediaRecorder, and real backend STT.

Run: python tests/voice_browser_check.py
Requires frontend/backend running and Playwright plus Microsoft Edge installed.
Verifies the speechSynthesis call, not audible output or native speaker accuracy.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

SAMPLE = Path(__file__).parent / "fixtures/voice/metformin-en.wav"


def check_playback(page, language):
    if language == "en":
        page.wait_for_function("window.spokenResponses.length > 0")
        assert "Metformin" in page.evaluate("window.spokenResponses[0].text")
    else:
        player = page.get_by_label("Spoken medicine response")
        expect(player).to_be_visible(timeout=65000)
        player.evaluate("audio => audio.play()")
        page.wait_for_function("document.querySelector('.voice-response-audio audio')?.currentTime > 0", timeout=15000)


def main():
    results = []
    frontend = os.getenv("PATIENT_TEST_FRONTEND_URL", "http://localhost:5173")
    backend = os.getenv("PATIENT_TEST_API_URL", "http://localhost:8000")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True, args=[
            "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
            f"--use-file-for-fake-audio-capture={SAMPLE.resolve()}",
        ])
        context = browser.new_context(permissions=["microphone"])
        context.add_init_script("""
            localStorage.setItem('mmss_token', 'voice-test');
            localStorage.setItem('mmss_role', 'patient');
            window.spokenResponses = [];
            const originalSpeak = speechSynthesis.speak.bind(speechSynthesis);
            speechSynthesis.speak = utterance => {
                window.spokenResponses.push({text: utterance.text, lang: utterance.lang});
                originalSpeak(utterance);
            };
        """)
        page = context.new_page()
        page.route(f"{backend}/patient/profile", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"profile": {
                "full_name": "Voice Test Patient",
                "patient_id": "VOICE-TEST",
                "age": 40,
                "gender": "Other",
                "medical_condition": "Type 2 Diabetes",
            }}),
        ))
        backend = os.getenv("VOICE_TEST_API_URL")
        if backend:
            page.route("http://127.0.0.1:8000/voice-search*", lambda route: route.continue_(url=route.request.url.replace("http://127.0.0.1:8000", backend)))
        for language in ("en", "kn", "tulu"):
            page.goto(f"{frontend}/voice-search")
            page.get_by_role("combobox").select_option(language)
            page.locator('input[type="file"][accept="audio/*"]').set_input_files(SAMPLE)
            with page.expect_response(lambda response: "/voice-search?" in response.url and response.request.method == "POST", timeout=65000) as pending:
                page.get_by_role("button", name="Search Medicine", exact=True).click()
            response = pending.value
            assert response.ok, response.text()
            result = response.json()
            assert result["status"] == "success", result
            assert result["detected_medicine"].casefold() == "metformin", result
            assert result["response_language"] == language, result
            expect(page.locator(".voice-simple-info")).to_be_visible()
            check_playback(page, language)
            results.append({"mode": "upload", "language": language, "status": "passed"})
        for language in ("en", "kn", "tulu"):
            page.goto(f"{frontend}/voice-search")
            page.get_by_role("combobox").select_option(language)
            with page.expect_response(lambda response: "/voice-search?" in response.url and response.request.method == "POST", timeout=95000) as pending:
                page.get_by_role("button", name="Record", exact=True).click()
                expect(page.get_by_role("button", name="Recording...")).to_be_visible()
                expect(page.locator(".voice-simple-info")).to_be_visible(timeout=95000)
            response = pending.value
            assert response.ok, response.text()
            assert response.json().get("detected_medicine", "").casefold() == "metformin", response.json()
            assert response.json().get("response_language") == language
            expect(page.locator(".voice-simple-info")).to_be_visible()
            check_playback(page, language)
            results.append({"mode": "record-auto-stop", "language": language, "status": "passed"})
        browser.close()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
