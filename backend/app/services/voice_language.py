"""Conservative language inference from recognized words, not speaker identity."""
import re
import unicodedata


def words(text):
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("\u200c", "").replace("\u200d", "")
    return set(re.findall(r"[a-z]+|[\u0c80-\u0cff]+", text))


# Include the Tulu wording supplied by the user. Shared medicine names and
# shared medical terms deliberately do not count as language evidence.
CUES = {
    "en": words("what does this do used for tell me about please medicine warning"),
    "kn": words("ಇದು ಏನು ಮಾಡುತ್ತದೆ ಔಷಧಿ ಔಷಧಿಯನ್ನು ಹೇಳಿ ತಿಳಿಸಿ ಯಾವ ಹೇಗೆ ಬಳಸುವುದು ಬದಲಾಯಿಸುವ ಮೊದಲು ವೈದ್ಯರನ್ನು ಕೇಳಿ ಮಾಹಿತಿ ಬೇಕು ಬೇಕೋ ಬಗ್ಗೆ idu enu maduttade heli tilisi yavudu hege aushadhi mahiti maahiti beku beko bekku bagge"),
    "tulu": words("ಉಂದು ದಾದ ಮಲ್ಪುಂಡ್ ಮಲ್ಪುಂಡು ಮರ್ದ್ ಬೊಕ್ಕ ದುಂಬು ಕೇನ್ಲೆ ಡಾಕ್ಟ್ರೆಡ ಮಲ್ಪುನೆಡ್ದ್ ಉಪ್ಪುನಕ್ಲೆಗ್ undu dada malpund malpundu mard mardu bokka dumbu kenle malpunedd yenk panle"),
}
CUES["tulu"].update(words("enk enka bodu ಎಂಕ್ ಎನ್ಕ್ ಬೋಡು ಬೋದು"))
SHARED_WORDS = words("bagge mahiti maahiti ಬಗ್ಗೆ ಮಾಹಿತಿ")


def infer_language(text, requested="auto"):
    requested = (requested or "auto").strip().lower()
    requested = "tulu" if requested == "tlu" else requested
    if requested in CUES:
        return requested
    if " / " in (text or ""):
        detected = {infer_language(part) for part in text.split(" / ")} - {None}
        return next(iter(detected)) if len(detected) == 1 else None
    tokens = words(text)
    scores = {language: len(tokens & (cues - SHARED_WORDS)) for language, cues in CUES.items()}
    # Shared vocabulary supports a language only when independent clues exist.
    # It cannot, by itself, make a Tulu utterance appear to be Kannada.
    for language in ("kn", "tulu"):
        if scores[language] and tokens & SHARED_WORDS:
            scores[language] += 1
    ranked = sorted(scores, key=scores.get, reverse=True)
    # Require at least two distinct cues and a clear lead. Script alone cannot
    # distinguish Kannada from Tulu, nor can a medicine name identify language.
    if scores[ranked[0]] >= 2 and scores[ranked[0]] > scores[ranked[1]]:
        return ranked[0]
    return None
