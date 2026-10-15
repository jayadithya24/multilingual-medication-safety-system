"""Browser regression: synthetic speech then silence submits without a Search click."""
import tempfile
import wave
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    sample = Path(__file__).parent / "fixtures/voice/metformin-en.wav"
    with tempfile.TemporaryDirectory() as directory:
        padded = Path(directory) / "speech-then-silence.wav"
        with wave.open(str(sample), "rb") as source, wave.open(str(padded), "wb") as target:
            target.setparams(source.getparams())
            target.writeframes(source.readframes(source.getnframes()))
            target.writeframes(bytes(source.getframerate() * source.getsampwidth() * source.getnchannels() * 8))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True, args=[
                "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                f"--use-file-for-fake-audio-capture={padded}",
            ])
            page = browser.new_page(permissions=["microphone"])
            requests = []
            def reply(route):
                requests.append(route.request)
                route.fulfill(json={"status": "language_uncertain", "detected_text": "Metformin", "message": "Please confirm your language."})
            page.route("**/voice-search?*", reply)
            page.goto("http://127.0.0.1:5173/voice-search")
            page.get_by_role("button", name="Record", exact=True).click()
            expect(page.get_by_role("heading", name="Metformin", exact=True)).to_be_visible(timeout=15000)
            assert len(requests) == 1
            assert len(requests[0].post_data_buffer) > 1000
            expect(page.get_by_text("Try uploading a clearer image", exact=False)).to_have_count(0)
            expect(page.get_by_role("button", name="Record", exact=True)).to_be_enabled()
            browser.close()
    print("PASS: speech followed by silence automatically uploaded once; no Search click or image advice.")


if __name__ == "__main__":
    main()
