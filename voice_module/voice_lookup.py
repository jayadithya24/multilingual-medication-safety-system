import speech_recognition as sr
import pandas as pd
from rapidfuzz import process

# -----------------------------
# Load Dataset
# -----------------------------
df = pd.read_csv("../datasets/english_master_dataset.csv")

# Medicine names
drug_list = df["drug_name"].dropna().tolist()

# -----------------------------
# Speech Recognizer
# -----------------------------
r = sr.Recognizer()

try:
    with sr.Microphone() as source:
        print("Please wait... Calibrating microphone...")
        r.adjust_for_ambient_noise(source, duration=2)

        print("Now speak the medicine name...")
        audio = r.listen(
            source,
            timeout=10,
            phrase_time_limit=5
        )

    # Convert speech to text
    text = r.recognize_google(audio, language="en-IN")
    print("\nYou said:", text)

    text = text.lower().strip()

    matched_drug = None

    # -----------------------------
    # Step 1 : Partial Match
    # -----------------------------
    for drug in drug_list:
        if text in drug.lower() or drug.lower() in text:
            matched_drug = drug
            break

    # -----------------------------
    # Step 2 : Fuzzy Match
    # -----------------------------
    if matched_drug is None:
        match = process.extractOne(text, drug_list)

        if match and match[1] >= 60:
            matched_drug = match[0]

    # -----------------------------
    # Step 3 : Display Information
    # -----------------------------
    if matched_drug:

        result = df[df["drug_name"] == matched_drug]

        print("\nDid you mean:", matched_drug)
        print("----------------------------------")
        print("Drug:", result.iloc[0]["drug_name"])
        print("Disease:", result.iloc[0]["disease"])
        print("Description:", result.iloc[0]["description"])
        print("Side Effects:", result.iloc[0]["side_effects"])
        print("Warnings:", result.iloc[0]["warnings"])
        print("Interactions:", result.iloc[0]["major_interactions"])

    else:
        print("\nMedicine not found.")

except sr.WaitTimeoutError:
    print("No speech detected. Please try again.")

except sr.UnknownValueError:
    print("Sorry, I couldn't understand what you said. Please speak clearly.")

except sr.RequestError as e:
    print("Speech Recognition service error:", e)

except Exception as e:
    print("Error:", e)