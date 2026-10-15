import re


REMOVE_WORDS = {
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "strip",
    "mg",
    "ml",
    "batch",
    "mfg",
    "exp",
}


def clean_detected_text(text_list):
    """Convert OCR output into a list of cleaned medicine-name candidates."""

    cleaned_words = []

    for text in text_list:
        if not text:
            continue

        normalized_text = str(text).lower()
        normalized_text = re.sub(r"[^a-z\s]", " ", normalized_text)

        for word in normalized_text.split():
            if word in REMOVE_WORDS:
                continue

            cleaned_word = re.sub(r"[^a-z]", "", word)
            if cleaned_word:
                cleaned_words.append(cleaned_word)

    return cleaned_words