import speech_recognition as sr
import pandas as pd

df = pd.read_csv("datasets/english_master_dataset.csv")

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Speak...")
    audio = r.listen(source)

text = r.recognize_google(audio)

print("You said:", text)

# Extract last word
drug = text.split()[-1].capitalize()

result = df[df["drug_name"].str.contains(drug, case=False, na=False)]

if result.empty:
    print("Drug not found")
else:
    print("\nDrug:", result.iloc[0]["drug_name"])
print("Disease:", result.iloc[0]["disease"])
print("Description:", result.iloc[0]["description"])
print("Side Effects:", result.iloc[0]["side_effects"])
print("Warnings:", result.iloc[0]["warnings"])
print("Interactions:", result.iloc[0]["major_interactions"])
