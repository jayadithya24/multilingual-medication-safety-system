from pathlib import Path
import pandas as pd


OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "ml_ready"
    / "multilingual_natural_queries.csv"
)

MEDICINES = [
    "Metformin",
    "Aspirin",
    "Paracetamol",
    "Ibuprofen",
]

TEMPLATES = {
    "en": {
        "medicine_info": [
            "Can you tell me about {medicine}?",
            "I want to know more about {medicine}.",
            "What should I know about {medicine}?",
            "Give me some information about {medicine}.",
        ],
        "uses": [
            "What is {medicine} used to treat?",
            "Why is {medicine} prescribed?",
            "What conditions is {medicine} used for?",
            "What is the purpose of taking {medicine}?",
        ],
        "side_effects": [
            "What side effects can {medicine} cause?",
            "Can {medicine} cause any unwanted effects?",
            "What problems might occur after taking {medicine}?",
            "Are there any adverse effects of {medicine}?",
        ],
        "contraindications": [
            "Who should not take {medicine}?",
            "When should {medicine} be avoided?",
            "Are there people who cannot use {medicine}?",
            "When is {medicine} not suitable?",
        ],
        "warnings": [
            "What precautions should I take with {medicine}?",
            "Are there any warnings about {medicine}?",
            "What should I be careful about when using {medicine}?",
            "What safety information should I know about {medicine}?",
        ],
        "interactions": [
            "Can {medicine} interact with other medicines?",
            "Which medicines should not be taken with {medicine}?",
            "Is it safe to combine {medicine} with other drugs?",
            "Does {medicine} have any drug interactions?",
        ],
        "dosage": [
            "How much {medicine} should be taken?",
            "What is the usual dose of {medicine}?",
            "How should the dose of {medicine} be taken?",
            "What amount of {medicine} is recommended?",
        ],
    },

    "kn": {
        "medicine_info": [
            "{medicine} ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಿ.",
            "{medicine} ಔಷಧಿಯ ಬಗ್ಗೆ ತಿಳಿಸಿ.",
            "{medicine} ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ತಿಳಿದುಕೊಳ್ಳಬೇಕು.",
            "{medicine} ಬಗ್ಗೆ ನನಗೆ ವಿವರ ಬೇಕು.",
        ],
        "uses": [
            "{medicine} ಅನ್ನು ಯಾವುದಕ್ಕಾಗಿ ಬಳಸುತ್ತಾರೆ?",
            "{medicine} ಯಾವ ಕಾಯಿಲೆಗೆ ಉಪಯೋಗವಾಗುತ್ತದೆ?",
            "{medicine} ಅನ್ನು ಏಕೆ ನೀಡುತ್ತಾರೆ?",
            "{medicine} ನ ಮುಖ್ಯ ಬಳಕೆ ಏನು?",
        ],
        "side_effects": [
            "{medicine} ನಿಂದ ಯಾವ ಅಡ್ಡ ಪರಿಣಾಮಗಳು ಉಂಟಾಗಬಹುದು?",
            "{medicine} ತೆಗೆದುಕೊಂಡರೆ ಯಾವ ತೊಂದರೆಗಳು ಬರಬಹುದು?",
            "{medicine} ಸೇವನೆಯಿಂದ ಅನಗತ್ಯ ಪರಿಣಾಮಗಳಿವೆಯೇ?",
            "{medicine} ನಿಂದ ಯಾವುದೇ ಪ್ರತಿಕೂಲ ಪರಿಣಾಮಗಳಿವೆಯೇ?",
        ],
        "contraindications": [
            "ಯಾರು {medicine} ತೆಗೆದುಕೊಳ್ಳಬಾರದು?",
            "ಯಾವಾಗ {medicine} ಅನ್ನು ತಪ್ಪಿಸಬೇಕು?",
            "ಯಾರಿಗೆ {medicine} ಸೂಕ್ತವಲ್ಲ?",
            "{medicine} ಯಾವ ಸಂದರ್ಭಗಳಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಬಾರದು?",
        ],
        "warnings": [
            "{medicine} ಬಳಸುವಾಗ ಯಾವ ಮುನ್ನೆಚ್ಚರಿಕೆ ಬೇಕು?",
            "{medicine} ಬಗ್ಗೆ ಯಾವ ಎಚ್ಚರಿಕೆಗಳಿವೆ?",
            "{medicine} ತೆಗೆದುಕೊಳ್ಳುವಾಗ ಯಾವುದರ ಬಗ್ಗೆ ಜಾಗರೂಕರಾಗಬೇಕು?",
            "{medicine} ಬಳಸುವ ಮೊದಲು ಯಾವ ಸುರಕ್ಷತಾ ಮಾಹಿತಿ ತಿಳಿದಿರಬೇಕು?",
        ],
        "interactions": [
            "{medicine} ಬೇರೆ ಔಷಧಿಗಳೊಂದಿಗೆ ಪ್ರತಿಕ್ರಿಯಿಸುತ್ತದೆಯೇ?",
            "{medicine} ಜೊತೆ ಯಾವ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಬಾರದು?",
            "{medicine} ಅನ್ನು ಇತರ ಔಷಧಿಗಳೊಂದಿಗೆ ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?",
            "{medicine} ನ ಔಷಧಿ ಪರಸ್ಪರ ಕ್ರಿಯೆಗಳು ಯಾವುವು?",
        ],
        "dosage": [
            "{medicine} ಅನ್ನು ಎಷ್ಟು ಪ್ರಮಾಣದಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಬೇಕು?",
            "{medicine} ನ ಸಾಮಾನ್ಯ ಪ್ರಮಾಣ ಎಷ್ಟು?",
            "{medicine} ನ ಸರಿಯಾದ ಡೋಸ್ ಎಷ್ಟು?",
            "{medicine} ಅನ್ನು ಹೇಗೆ ಮತ್ತು ಎಷ್ಟು ತೆಗೆದುಕೊಳ್ಳಬೇಕು?",
        ],
    },

    "tulu": {
        "medicine_info": [
            "{medicine} ದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಕೊರ್ಲೆ.",
            "{medicine} ದ ಬಗ್ಗೆ ಎಂಚಿನ ಮಾಹಿತಿ ಉಂಡು?",
            "{medicine} ದ ಬಗ್ಗೆ ತಿಳ್ಕೊಂಬೊಡು.",
            "{medicine} ದ ಬಗ್ಗೆ ವಿವರ ಕೊರ್ಲೆ.",
        ],
        "uses": [
            "{medicine} ಎಂಚಿನ ಬಳಕೆಗ್ ಬರ್ಪುಂಡು?",
            "{medicine} ಯಾತಕ್ಕೆ ಬಳಕೆ ಆಪುಂಡು?",
            "{medicine} ದ ಮುಖ್ಯ ಬಳಕೆ ಎಂಚಿನದು?",
            "{medicine} ಯಾತಕ್ಕೆ ತಿನ್ಪುಂಡು?",
        ],
        "side_effects": [
            "{medicine} ತಿಂದ್ ಎಂಚಿನ ಅಡ್ಡ ಪರಿಣಾಮೊಲು ಆಪುಂಡು?",
            "{medicine} ತಿನ್ಪುನಗ ಎಂಚಿನ ತೊಂದರೆ ಆಪುಂಡು?",
            "{medicine} ದಿಂದ್ ಎಂಚಿನ ಅನಗತ್ಯ ಪರಿಣಾಮ ಆಪುಂಡು?",
            "{medicine} ತಿಂದ್ ಯಾವುದೇ ತೊಂದರೆ ಉಂಡಾ?",
        ],
        "contraindications": [
            "ಯೆರ್ {medicine} ತಿನ್ಪುನೆ ಸರಿಯಲ್ಲ?",
            "{medicine} ಯೆಂಚಿನ ಸಂದರ್ಭಡ್ ತಿನ್ಪುನೆ ಸರಿಯಲ್ಲ?",
            "ಯಾರಿಗೆ {medicine} ಸೂಕ್ತ ಅಲ್ಲ?",
            "{medicine} ಯೆರ್ ತಿನ್ಪುನೆ ಬೇಡ?",
        ],
        "warnings": [
            "{medicine} ಬಳಕೆದ್ ಎಂಚಿನ ಜಾಗ್ರತೆ ಬೇಕು?",
            "{medicine} ಬಗ್ಗೆ ಎಂಚಿನ ಎಚ್ಚರಿಕೆ ಉಂಡು?",
            "{medicine} ತಿನ್ಪುನಗ ಯೆಂಚಿನ ಜಾಗ್ರತೆ ಬೇಕು?",
            "{medicine} ಬಳಕೆ ಮುಂಚೆ ಎಂಚಿನ ಮಾಹಿತಿ ಗೊತ್ತುಪ್ಪು?",
        ],
        "interactions": [
            "{medicine} ಬೇರೆ ಔಷಧಿಲೊಟ್ಟಿಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಆಪುಂಡಾ?",
            "{medicine} ಜೊತೆಯಾದ್ ಬೇರೆ ಔಷಧಿ ತಿನ್ಪುಂಡಾ?",
            "{medicine} ಬೇರೆ ಔಷಧಿಲೊಟ್ಟಿಗೆ ತಿನ್ಪುನೆ ಸಾಧ್ಯನಾ?",
            "{medicine} ದ ಔಷಧಿ ಪರಸ್ಪರ ಕ್ರಿಯೆ ಉಂಡಾ?",
        ],
        "dosage": [
            "{medicine} ದ ಪ್ರಮಾಣ ಎಷ್ಟ್ ಆಪುಂಡು?",
            "{medicine} ಎಷ್ಟ್ ಪ್ರಮಾಣಡ್ ತಿನ್ಪುಂಡು?",
            "{medicine} ದ ಸಾಮಾನ್ಯ ಡೋಸ್ ಎಷ್ಟ್?",
            "{medicine} ಎಂಚಿನ ಪ್ರಮಾಣಡ್ ತಿನ್ಪುಂಡು?",
        ],
    },
}


def build_dataset():
    rows = []

    for language, intents in TEMPLATES.items():
        for intent, templates in intents.items():
            for medicine in MEDICINES:
                for template in templates:
                    rows.append(
                        {
                            "language": language,
                            "query": template.format(medicine=medicine),
                            "medicine": medicine,
                            "intent": intent,
                        }
                    )

    return pd.DataFrame(rows)


def main():
    dataset = build_dataset()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Natural multilingual dataset created.")
    print(f"Total examples: {len(dataset)}")
    print("\nLanguage distribution:")
    print(dataset["language"].value_counts())

    print("\nIntent distribution:")
    print(dataset["intent"].value_counts())

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()