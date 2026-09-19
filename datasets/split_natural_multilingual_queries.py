import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

INPUT_FILE = Path("datasets/ml_ready/multilingual_natural_queries.csv")
OUTPUT_DIR = Path("datasets/ml_ready")

df = pd.read_csv(INPUT_FILE)

# Keep language + intent proportions balanced.
stratify_column = df["language"] + "_" + df["intent"]

# 80% training, 20% temporary set
train_df, temp_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=stratify_column
)

# Split remaining 20% equally:
# 10% validation, 10% test
temp_stratify = temp_df["language"] + "_" + temp_df["intent"]

validation_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    random_state=42,
    stratify=temp_stratify
)

train_df.to_csv(
  OUTPUT_DIR / "multilingual_natural_train.csv",
    index=False,
    encoding="utf-8-sig"
)

validation_df.to_csv(
   OUTPUT_DIR / "multilingual_natural_validation.csv",
    index=False,
    encoding="utf-8-sig"
)

test_df.to_csv(
   OUTPUT_DIR / "multilingual_natural_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Dataset split completed.")
print(f"Total:      {len(df)}")
print(f"Training:   {len(train_df)}")
print(f"Validation: {len(validation_df)}")
print(f"Test:       {len(test_df)}")

print("\nTraining distribution:")
print(train_df.groupby(["language", "intent"]).size().to_string())

print("\nValidation distribution:")
print(validation_df.groupby(["language", "intent"]).size().to_string())

print("\nTest distribution:")
print(test_df.groupby(["language", "intent"]).size().to_string())