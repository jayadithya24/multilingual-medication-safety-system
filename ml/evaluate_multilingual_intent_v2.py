import joblib
from pathlib import Path


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "multilingual_intent_model_v2.joblib"
)


EVAL_DATA = [

    # =========================
    # ENGLISH
    # =========================

    ("en", "Paracetamol", "medicine_info",
     "Could you give me an overview of Paracetamol?"),

    ("en", "Ibuprofen", "medicine_info",
     "I would like to know more about Ibuprofen."),

    ("en", "Paracetamol", "uses",
     "What is Paracetamol commonly prescribed to treat?"),

    ("en", "Ibuprofen", "uses",
     "Why might someone take Ibuprofen?"),

    ("en", "Paracetamol", "side_effects",
     "What adverse reactions can occur with Paracetamol?"),

    ("en", "Ibuprofen", "side_effects",
     "Can Ibuprofen cause any unwanted reactions?"),

    ("en", "Paracetamol", "contraindications",
     "In which situations should Paracetamol be avoided?"),

    ("en", "Ibuprofen", "contraindications",
     "Are there people who should not take Ibuprofen?"),

    ("en", "Paracetamol", "warnings",
     "What should I be careful about when taking Paracetamol?"),

    ("en", "Ibuprofen", "warnings",
     "What safety warnings are associated with Ibuprofen?"),

    ("en", "Paracetamol", "interactions",
     "Can Paracetamol be taken together with other drugs?"),

    ("en", "Ibuprofen", "interactions",
     "Does Ibuprofen interact with any medicines?"),

    ("en", "Paracetamol", "dosage",
     "What is the recommended amount of Paracetamol?"),

    ("en", "Ibuprofen", "dosage",
     "How should the dose of Ibuprofen be taken?"),


    # =========================
    # KANNADA
    # =========================

    ("kn", "Paracetamol", "medicine_info",
     "Paracetamol ಔಷಧಿಯ ಬಗ್ಗೆ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."),

    ("kn", "Ibuprofen", "medicine_info",
     "Ibuprofen ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ತಿಳಿದುಕೊಳ್ಳಬೇಕು."),

    ("kn", "Paracetamol", "uses",
     "Paracetamol ಅನ್ನು ಯಾವ ಕಾಯಿಲೆಗಳಿಗೆ ಬಳಸುತ್ತಾರೆ?"),

    ("kn", "Ibuprofen", "uses",
     "Ibuprofen ತೆಗೆದುಕೊಳ್ಳುವುದರಿಂದ ಯಾವ ಸಮಸ್ಯೆಗೆ ಚಿಕಿತ್ಸೆ ಸಿಗುತ್ತದೆ?"),

    ("kn", "Paracetamol", "side_effects",
     "Paracetamol ನಿಂದ ಯಾವ ಪ್ರತಿಕೂಲ ಪರಿಣಾಮಗಳು ಉಂಟಾಗಬಹುದು?"),

    ("kn", "Ibuprofen", "side_effects",
     "Ibuprofen ಸೇವಿಸಿದರೆ ಯಾವುದೇ ಅನಗತ್ಯ ಪರಿಣಾಮಗಳಿವೆಯೇ?"),

    ("kn", "Paracetamol", "contraindications",
     "ಯಾವ ಸಂದರ್ಭಗಳಲ್ಲಿ Paracetamol ತೆಗೆದುಕೊಳ್ಳಬಾರದು?"),

    ("kn", "Ibuprofen", "contraindications",
     "ಯಾವ ವ್ಯಕ್ತಿಗಳು Ibuprofen ತೆಗೆದುಕೊಳ್ಳಬಾರದು?"),

    ("kn", "Paracetamol", "warnings",
     "Paracetamol ತೆಗೆದುಕೊಳ್ಳುವಾಗ ಯಾವ ವಿಷಯಗಳ ಬಗ್ಗೆ ಎಚ್ಚರಿಕೆ ಇರಬೇಕು?"),

    ("kn", "Ibuprofen", "warnings",
     "Ibuprofen ಬಳಸುವಾಗ ಯಾವ ಸುರಕ್ಷತಾ ಎಚ್ಚರಿಕೆಗಳಿವೆ?"),

    ("kn", "Paracetamol", "interactions",
     "Paracetamol ಅನ್ನು ಇತರ ಔಷಧಿಗಳೊಂದಿಗೆ ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?"),

    ("kn", "Ibuprofen", "interactions",
     "Ibuprofen ಬೇರೆ ಔಷಧಿಗಳೊಂದಿಗೆ ಪ್ರತಿಕ್ರಿಯಿಸುತ್ತದೆಯೇ?"),

    ("kn", "Paracetamol", "dosage",
     "Paracetamol ನ ಸರಿಯಾದ ಪ್ರಮಾಣ ಎಷ್ಟು?"),

    ("kn", "Ibuprofen", "dosage",
     "Ibuprofen ಅನ್ನು ಯಾವ ಪ್ರಮಾಣದಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಬೇಕು?"),


    # =========================
    # TULU
    # =========================

    ("tulu", "Paracetamol", "medicine_info",
     "Paracetamol ದ ಬಗ್ಗೆ ಪೂರ್ಣ ಮಾಹಿತಿ ಕೊರ್ಲೆ."),

    ("tulu", "Ibuprofen", "medicine_info",
     "Ibuprofen ದ ಬಗ್ಗೆ ಎಂಚಿನ ಮಾಹಿತಿ ಉಂಡು?"),

    ("tulu", "Paracetamol", "uses",
     "Paracetamol ಎಂಚಿನ ಸಮಸ್ಯೆಗ್ ಉಪಯೋಗ ಆಪುಂಡು?"),

    ("tulu", "Ibuprofen", "uses",
     "Ibuprofen ಯಾತಕ್ಕೆ ಬಳಕೆ ಆಪುಂಡು?"),

    ("tulu", "Paracetamol", "side_effects",
     "Paracetamol ತಿನ್ಪುನಗ ಎಂಚಿನ ಅಡ್ಡ ಪರಿಣಾಮೊಲು ಆಪುಂಡು?"),

    ("tulu", "Ibuprofen", "side_effects",
     "Ibuprofen ತಿಂದ್ ಎಂಚಿನ ತೊಂದರೆ ಆಪುಂಡು?"),

    ("tulu", "Paracetamol", "contraindications",
     "ಯಾವ ಸಂದರ್ಭಡ್ Paracetamol ತಿನ್ಪುನೆ ಸರಿಯಲ್ಲ?"),

    ("tulu", "Ibuprofen", "contraindications",
     "ಯೆರ್ Ibuprofen ತಿನ್ಪುನೆ ಸರಿಯಲ್ಲ?"),

    ("tulu", "Paracetamol", "warnings",
     "Paracetamol ಬಳಕೆದ್ ಯೆಂಚಿನ ಜಾಗ್ರತೆ ಬೇಕು?"),

    ("tulu", "Ibuprofen", "warnings",
     "Ibuprofen ತಿನ್ಪುನಗ ಎಂಚಿನ ಎಚ್ಚರಿಕೆ ಉಂಡು?"),

    ("tulu", "Paracetamol", "interactions",
     "Paracetamol ಬೇರೆ ಔಷಧಿಲೊಟ್ಟಿಗೆ ತಿನ್ಪುಂಡಾ?"),

    ("tulu", "Ibuprofen", "interactions",
     "Ibuprofen ಬೇರೆ ಔಷಧಿಲೊಟ್ಟಿಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಆಪುಂಡಾ?"),

    ("tulu", "Paracetamol", "dosage",
     "Paracetamol ದ ಪ್ರಮಾಣ ಎಷ್ಟ್ ಆಪುಂಡು?"),

    ("tulu", "Ibuprofen", "dosage",
     "Ibuprofen ಎಷ್ಟ್ ಪ್ರಮಾಣಡ್ ತಿನ್ಪುಂಡು?"),
]


def main():
    print("Loading multilingual intent model...")

    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found: {MODEL_PATH}")
        return

    model = joblib.load(MODEL_PATH)

    total = len(EVAL_DATA)
    correct = 0

    language_results = {}

    print("\n" + "=" * 100)
    print("MULTILINGUAL INTENT MODEL - SECOND UNSEEN EVALUATION")
    print("=" * 100)

    for language, medicine, expected, query in EVAL_DATA:

        predicted = model.predict([query])[0]

        passed = predicted == expected

        if language not in language_results:
            language_results[language] = {
                "correct": 0,
                "total": 0
            }

        language_results[language]["total"] += 1

        if passed:
            correct += 1
            language_results[language]["correct"] += 1

        status = "PASS" if passed else "FAIL"

        print(
            f"[{status}] "
            f"{language.upper():5} | "
            f"Expected: {expected:18} | "
            f"Predicted: {predicted:18} | "
            f"{query}"
        )

    print("\n" + "=" * 100)
    print("RESULTS")
    print("=" * 100)

    print(f"Overall: {correct}/{total}")
    print(
        f"Overall Accuracy: "
        f"{correct / total * 100:.2f}%"
    )

    print("\nAccuracy by language:")

    for language, result in language_results.items():

        accuracy = (
            result["correct"] /
            result["total"] *
            100
        )

        print(
            f"{language.upper():5}: "
            f"{result['correct']}/{result['total']} "
            f"({accuracy:.2f}%)"
        )


if __name__ == "__main__":
    main()