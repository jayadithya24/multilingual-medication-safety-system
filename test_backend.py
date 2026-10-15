"""Live smoke checks; optionally pass --audio sample.wav --lang en --expected Metformin."""
import argparse
from pathlib import Path
import requests


def run_tests(base_url, audio=None, lang="en", expected="Metformin"):
    requests.get(f"{base_url}/health", timeout=15).raise_for_status()
    for language in ("en", "kn", "tulu"):
        response = requests.get(f"{base_url}/medicine/Metformin", params={"lang": language}, timeout=15)
        response.raise_for_status()
        assert response.json().get("medicine"), language
    if audio:
        with Path(audio).open("rb") as recording:
            response = requests.post(f"{base_url}/voice-search", params={"lang": lang}, files={"file": (Path(audio).name, recording)}, timeout=60)
        response.raise_for_status()
        result = response.json()
        assert result.get("status") == "success", result
        assert result.get("detected_text"), result
        assert result.get("detected_medicine", "").casefold() == expected.casefold(), result
        assert result.get("response_language") == lang, result
        print("Saved audio recognition and lookup passed.")
    print("Health and medicine API checks passed for all three languages.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--audio")
    parser.add_argument("--lang", choices=("en", "kn", "tulu"), default="en")
    parser.add_argument("--expected", default="Metformin")
    args = parser.parse_args()
    run_tests(args.base_url.rstrip("/"), args.audio, args.lang, args.expected)
