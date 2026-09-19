import pandas as pd
from pathlib import Path

INPUT_FILE = Path("datasets/ml_ready/master_localized.csv")
OUTPUT_FILE = Path("datasets/ml_ready/multilingual_queries.csv")

df = pd.read_csv(INPUT_FILE)

# Natural query templates.
# The medicine name is taken from the localized dataset.
templates = {
    "en": {
        "medicine_info": [
            "What is {medicine}?",
            "Tell me about {medicine}.",
            "What do I need to know about {medicine}?",
        ],
        "uses": [
            "What is {medicine} used for?",
            "Why is {medicine} used?",
            "What conditions is {medicine} used for?",
        ],
        "side_effects": [
            "What are the side effects of {medicine}?",
            "Can {medicine} cause any side effects?",
            "What problems can {medicine} cause?",
        ],
        "contraindications": [
            "Who should not take {medicine}?",
            "When should {medicine} not be used?",
            "Who should avoid {medicine}?",
        ],
        "warnings": [
            "What warnings should I know about {medicine}?",
            "Are there any warnings about {medicine}?",
            "What should I be careful about when taking {medicine}?",
        ],
        "interactions": [
            "Does {medicine} interact with other medicines?",
            "Can {medicine} interact with other drugs?",
            "What medicines can interact with {medicine}?",
        ],
        "dosage": [
            "How should {medicine} be taken?",
            "How do I take {medicine}?",
            "What is the dosage information for {medicine}?",
        ],
    },

    "kn": {
        "medicine_info": [
            "{medicine} ಎಂದರೇನು?",
            "{medicine} ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಿ.",
            "{medicine} ಬಗ್ಗೆ ನಾನು ಏನು ತಿಳಿದುಕೊಳ್ಳಬೇಕು?",
        ],
        "uses": [
            "{medicine} ಅನ್ನು ಯಾವುದಕ್ಕಾಗಿ ಬಳಸುತ್ತಾರೆ?",
            "{medicine} ಏಕೆ ಬಳಸಲಾಗುತ್ತದೆ?",
            "{medicine} ಯಾವ ಕಾಯಿಲೆಗೆ ಬಳಸಲಾಗುತ್ತದೆ?",
        ],
        "side_effects": [
            "{medicine} ನ ಅಡ್ಡ ಪರಿಣಾಮಗಳು ಯಾವುವು?",
            "{medicine} ಅಡ್ಡ ಪರಿಣಾಮಗಳನ್ನು ಉಂಟುಮಾಡಬಹುದೇ?",
            "{medicine} ನಿಂದ ಯಾವ ಸಮಸ್ಯೆಗಳು ಉಂಟಾಗಬಹುದು?",
        ],
        "contraindications": [
            "{medicine} ಅನ್ನು ಯಾರು ತೆಗೆದುಕೊಳ್ಳಬಾರದು?",
            "{medicine} ಅನ್ನು ಯಾವಾಗ ಬಳಸಬಾರದು?",
            "ಯಾರು {medicine} ಅನ್ನು ತಪ್ಪಿಸಬೇಕು?",
        ],
        "warnings": [
            "{medicine} ಬಗ್ಗೆ ಯಾವ ಎಚ್ಚರಿಕೆಗಳನ್ನು ತಿಳಿದುಕೊಳ್ಳಬೇಕು?",
            "{medicine} ಬಗ್ಗೆ ಯಾವುದೇ ಎಚ್ಚರಿಕೆಗಳಿವೆಯೇ?",
            "{medicine} ತೆಗೆದುಕೊಳ್ಳುವಾಗ ನಾನು ಯಾವುದರ ಬಗ್ಗೆ ಎಚ್ಚರಿಕೆಯಿಂದ ಇರಬೇಕು?",
        ],
        "interactions": [
            "{medicine} ಇತರ ಔಷಧಿಗಳೊಂದಿಗೆ ಪರಸ್ಪರ ಕ್ರಿಯೆ ಮಾಡುತ್ತದೆಯೇ?",
            "{medicine} ಇತರ ಔಷಧಿಗಳೊಂದಿಗೆ ಪ್ರತಿಕ್ರಿಯಿಸಬಹುದೇ?",
            "ಯಾವ ಔಷಧಿಗಳು {medicine} ಜೊತೆ ಪರಸ್ಪರ ಕ್ರಿಯೆ ಮಾಡಬಹುದು?",
        ],
        "dosage": [
            "{medicine} ಅನ್ನು ಹೇಗೆ ತೆಗೆದುಕೊಳ್ಳಬೇಕು?",
            "{medicine} ಅನ್ನು ಹೇಗೆ ಬಳಸಬೇಕು?",
            "{medicine} ನ ಡೋಸೇಜ್ ಮಾಹಿತಿ ಏನು?",
        ],
    },

    "tulu": {
        "medicine_info": [
            "{medicine} ದೆಂದ್?",
            "{medicine} ದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಕೊರ್ಲೆ.",
            "{medicine} ಬಗ್ಗೆ ಎಂಕ್ ಏನ್ ಗೊತ್ತ್ ಆಪುನ?",
        ],
        "uses": [
            "{medicine} ಯಾನ್ ಎತ್ಕ್ ಉಪಯೋಗ ಆಪುಂಡು?",
            "{medicine} ಯಾನ್ ಯಾಕೆ ಉಪಯೋಗ ಮಲ್ಪುಂಡು?",
            "{medicine} ಯಾನ್ ಎತ್ ಕಾಯಿಲೆಗ್ ಉಪಯೋಗ ಆಪುಂಡು?",
        ],
        "side_effects": [
            "{medicine} ದ ಅಡ್ಡ ಪರಿಣಾಮೊಲು ಎಂಚಿನವು?",
            "{medicine} ದಿಂದ ಅಡ್ಡ ಪರಿಣಾಮ ಆಪುಂಡಾ?",
            "{medicine} ದಿಂದ ಎಂಚಿನ ಸಮಸ್ಯೆ ಆಪುಂಡು?",
        ],
        "contraindications": [
            "{medicine} ಯಾನ್ ಯಾರೆ ದೆತೊನ್ಬಾರದು?",
            "{medicine} ಯಾನ್ ಯಾನ್ ಸಮಯಡ್ ದೆತೊನ್ಬಾರದು?",
            "ಯಾರೆ {medicine} ಯಾನ್ ತಪ್ಪಿಸಾಯೆರೆ?",
        ],
        "warnings": [
            "{medicine} ಬಗ್ಗೆ ಎಂಚಿನ ಎಚ್ಚರಿಕೆ ಉಂಡು?",
            "{medicine} ಬಗ್ಗೆ ಎಚ್ಚರಿಕೆ ಉಂಡಾ?",
            "{medicine} ದೆತೊನುವಾಗ ಎಂಚಿನ ಎಚ್ಚರಿಕೆ ಕೊರ್ಲೆ?",
        ],
        "interactions": [
            "{medicine} ಬೊಕ್ಕ ಬೇತೆ ಮರ್ದ್‌ಲು ಒಟ್ಟುಗು ಪರಸ್ಪರ ಕ್ರಿಯೆ ಮಲ್ಪುಂಡಾ?",
            "{medicine} ಬೇತೆ ಮರ್ದ್‌ದೊಟ್ಟುಗು ಪ್ರತಿಕ್ರಿಯೆ ಮಲ್ಪುಂಡಾ?",
            "ಎಂಚಿನ ಮರ್ದ್‌ಲು {medicine} ಬೊಕ್ಕ ಪರಸ್ಪರ ಕ್ರಿಯೆ ಮಲ್ಪುಂಡು?",
        ],
        "dosage": [
            "{medicine} ಯಾನ್ ಎಂಚ ದೆತೊನ್ಬೇಕು?",
            "{medicine} ಯಾನ್ ಎಂಚ ಉಪಯೋಗ ಮಲ್ಪುಲೆ?",
            "{medicine} ದ ಡೋಸೇಜ್ ಮಾಹಿತಿ ಎಂಚಿನದು?",
        ],
    },
}

rows = []

for _, row in df.iterrows():
    language = row["language"]

    if language not in templates:
        continue

    medicine = row["drug_name"]

    for intent, questions in templates[language].items():
        for question in questions:
            rows.append({
                "language": language,
                "query": question.format(medicine=medicine),
                "medicine": medicine,
                "intent": intent,
            })

result = pd.DataFrame(rows)

result.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print(f"Created: {OUTPUT_FILE}")
print(f"Total examples: {len(result)}")
print("\nExamples per language:")
print(result["language"].value_counts())

print("\nExamples per intent:")
print(result["intent"].value_counts())

print("\nFirst 15 examples:")
print(result.head(15).to_string(index=False))