import pandas as pd

df = pd.read_csv("datasets/english_master_dataset.csv")

drug = "Metformin"

result = df[df["drug_name"].str.lower() == drug.lower()]

print(result[["drug_name", "disease", "description"]])