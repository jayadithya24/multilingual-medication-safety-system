import joblib
from pathlib import Path


MODEL_PATH = Path(__file__).resolve().parent / "models" / "multilingual_intent_model_v2.joblib"

# Completely new queries for evaluation.
# These are intentionally different from the training templates.
EVAL_DATA = [
    # English
    ("en", "Metformin", "medicine_info", "Can you explain what Metformin is used for?"),
    ("en", "Metformin", "uses", "Why would a doctor prescribe Metformin?"),
    ("en", "Metformin", "side_effects", "What unwanted effects can Metformin cause?"),
    ("en", "Metformin", "contraindications", "When should someone avoid taking Metformin?"),
    ("en", "Metformin", "warnings", "What precautions should I know before using Metformin?"),
    ("en", "Metformin", "interactions", "Can Metformin react with other medicines?"),
    ("en", "Metformin", "dosage", "How much Metformin is normally taken?"),

    ("en", "Aspirin", "medicine_info", "I want some information about Aspirin."),
    ("en", "Aspirin", "uses", "What conditions can Aspirin be taken for?"),
    ("en", "Aspirin", "side_effects", "What problems might happen after taking Aspirin?"),
    ("en", "Aspirin", "contraindications", "Who should stay away from Aspirin?"),
    ("en", "Aspirin", "warnings", "Are there any important warnings for Aspirin?"),
    ("en", "Aspirin", "interactions", "Which medicines should not be combined with Aspirin?"),
    ("en", "Aspirin", "dosage", "What amount of Aspirin should be taken?"),

    # Kannada
    ("kn", "Metformin", "medicine_info", "Metformin ಬಗ್ಗೆ ಸ್ವಲ್ಪ ವಿವರಿಸಿ."),
    ("kn", "Metformin", "uses", "Metformin ಅನ್ನು ಯಾವ ಸಮಸ್ಯೆಗಳಿಗೆ ಬಳಸುತ್ತಾರೆ?"),
    ("kn", "Metformin", "side_effects", "Metformin ತೆಗೆದುಕೊಂಡಾಗ ಯಾವ ತೊಂದರೆಗಳು ಉಂಟಾಗಬಹುದು?"),
    ("kn", "Metformin", "contraindications", "ಯಾರು Metformin ತೆಗೆದುಕೊಳ್ಳಬಾರದು?"),
    ("kn", "Metformin", "warnings", "Metformin ಬಳಸುವಾಗ ಯಾವ ಮುನ್ನೆಚ್ಚರಿಕೆ ಬೇಕು?"),
    ("kn", "Metformin", "interactions", "Metformin ಜೊತೆ ಬೇರೆ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಬಹುದೇ?"),
    ("kn", "Metformin", "dosage", "Metformin ನ ಪ್ರಮಾಣ ಎಷ್ಟು ಇರಬೇಕು?"),

    ("kn", "Aspirin", "medicine_info", "Aspirin ಬಗ್ಗೆ ಮಾಹಿತಿ ಬೇಕು."),
    ("kn", "Aspirin", "uses", "Aspirin ಅನ್ನು ಯಾವುದಕ್ಕಾಗಿ ಬಳಸಲಾಗುತ್ತದೆ?"),
    ("kn", "Aspirin", "side_effects", "Aspirin ಸೇವನೆಯಿಂದ ಯಾವ ಅಡ್ಡ ಪರಿಣಾಮಗಳು ಬರಬಹುದು?"),
    ("kn", "Aspirin", "contraindications", "Aspirin ಯಾರಿಗೆ ಸೂಕ್ತವಲ್ಲ?"),
    ("kn", "Aspirin", "warnings", "Aspirin ಬಗ್ಗೆ ಗಮನಿಸಬೇಕಾದ ಎಚ್ಚರಿಕೆಗಳೇನು?"),
    ("kn", "Aspirin", "interactions", "Aspirin ಯಾವ ಔಷಧಿಗಳೊಂದಿಗೆ ಪ್ರತಿಕ್ರಿಯಿಸಬಹುದು?"),
    ("kn", "Aspirin", "dosage", "Aspirin ಅನ್ನು ಎಷ್ಟು ಪ್ರಮಾಣದಲ್ಲಿ ತೆಗೆದುಕೊಳ್ಳಬೇಕು?"),

    # Tulu
    ("tulu", "Metformin", "medicine_info", "Metformin ದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಕೊರ್ಲೆ."),
    ("tulu", "Metformin", "uses", "Metformin ಎಂಚಿನ ಬಳಕೆ ಆಪುಂಡು?"),
    ("tulu", "Metformin", "side_effects", "Metformin ತಿಂದ್ ಅಡ್ಡ ಪರಿಣಾಮೊಲು ಎಂಚಿನವು?"),
    ("tulu", "Metformin", "contraindications", "ಯೆರ್ Metformin ತಿನ್ಪುನವು ಸರಿಯಲ್ಲ?"),
    ("tulu", "Metformin", "warnings", "Metformin ಬಳಕೆದ್ ಎಂಚಿನ ಜಾಗ್ರತೆ ಬೇಕು?"),
    ("tulu", "Metformin", "interactions", "Metformin ಜೊತೆಯಾದ್ ಬೇರೆ ಔಷಧಿ ತಿನ್ಪುನದು ಸಾಧ್ಯನಾ?"),
    ("tulu", "Metformin", "dosage", "Metformin ದ ಪ್ರಮಾಣ ಎಷ್ಟ್ ಆಪುಂಡು?"),

    ("tulu", "Aspirin", "medicine_info", "Aspirin ದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಕೊರ್ಲೆ."),
    ("tulu", "Aspirin", "uses", "Aspirin ಎಂಚಿನ ಬಳಕೆಗ್ ಬರ್ಪುಂಡು?"),
    ("tulu", "Aspirin", "side_effects", "Aspirin ತಿಂದ್ ಎಂಚಿನ ತೊಂದರೆ ಆಪುಂಡು?"),
    ("tulu", "Aspirin", "contraindications", "ಯೆರ್ Aspirin ತಿನ್ಪುನವು ಸರಿಯಲ್ಲ?"),
    ("tulu", "Aspirin", "warnings", "Aspirin ಬಳಕೆದ್ ಎಂಚಿನ ಜಾಗ್ರತೆ ಬೇಕು?"),
    ("tulu", "Aspirin", "interactions", "Aspirin ಬೇರೆ ಔಷಧೊಲೊಟ್ಟಿಗೆ ಪ್ರತಿಕ್ರಿಯೆ ಆಪುಂಡಾ?"),
    ("tulu", "Aspirin", "dosage", "Aspirin ದ ಪ್ರಮಾಣ ಎಷ್ಟ್ ತಿನ್ಪುಂಡು?")
]


def main():
    print("Loading multilingual intent model...")

    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at: {MODEL_PATH}")
        return

    model = joblib.load(MODEL_PATH)

    total = len(EVAL_DATA)
    correct = 0

    language_results = {
        "en": {"correct": 0, "total": 0},
        "kn": {"correct": 0, "total": 0},
        "tulu": {"correct": 0, "total": 0},
    }

    print("\n" + "=" * 100)
    print("MULTILINGUAL INTENT MODEL - NEW QUERY EVALUATION")
    print("=" * 100)

    for language, medicine, expected, query in EVAL_DATA:
        predicted = model.predict([query])[0]

        status = "PASS" if predicted == expected else "FAIL"

        if predicted == expected:
            correct += 1
            language_results[language]["correct"] += 1

        language_results[language]["total"] += 1

        print(
            f"[{status}] "
            f"{language.upper():5} | "
            f"Expected: {expected:18} | "
            f"Predicted: {predicted:18} | "
            f"{query}"
        )

    overall_accuracy = correct / total

    print("\n" + "=" * 100)
    print("RESULTS")
    print("=" * 100)

    print(f"Overall: {correct}/{total} correct")
    print(f"Overall Accuracy: {overall_accuracy:.4f} ({overall_accuracy * 100:.2f}%)")

    print("\nAccuracy by language:")

    for language, result in language_results.items():
        accuracy = result["correct"] / result["total"]
        print(
            f"{language.upper():5}: "
            f"{result['correct']}/{result['total']} "
            f"({accuracy * 100:.2f}%)"
        )

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()