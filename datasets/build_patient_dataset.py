"""
generate_patient_dataset.py

Generates synthetic patient data for NeoGraphMed.
Target: 1,00,000 patient-drug association records
       (10,000 unique patients x ~10 records each)

This is synthetic data generated following:
- ICMR NCD prevalence statistics
- ADA/JNC8/ACR clinical guidelines for drug assignment
- Realistic age/gender/comorbidity distributions
  based on Indian elderly outpatient demographics

Used for:
1. Loading patient nodes into Neo4j
2. Validating DDI engine against patient profiles
3. Demonstrating system with realistic data
4. Doctor dashboard -- patient drug list retrieval

USAGE:
    pip install pandas numpy
    python generate_patient_dataset.py
    (place your real drug_interactions.csv in the same folder --
     see DRUG_INTERACTIONS_CSV below)

Outputs:
    synthetic_patients.csv             -- patient master records (10,000 rows)
    synthetic_patient_drugs.csv        -- patient-drug associations (~1 lakh rows)
    synthetic_patient_interactions.csv -- computed interaction risks per patient

CHANGES FROM THE ORIGINAL DRAFT (read this before you run it):
1. KNOWN_INTERACTIONS is no longer a hand-typed dict. It is loaded directly
   from your real drug_interactions.csv (in-scope pairs only), so the
   synthetic labels always match what your actual Neo4j graph would say.
   A hardcoded fallback only kicks in if that file is missing, and it
   prints a loud warning when it does -- it should never be silently used.
2. Your real CSV has a genuine conflict: ibuprofen<->methotrexate is listed
   as Moderate in one direction and Severe in the other. This script
   resolves conflicts by taking the MORE severe rating (the safer
   assumption for a clinical tool) and prints exactly which pairs it had
   to resolve, so you can go fix the source data if the conflict wasn't
   intentional.
3. assign_conditions() previously had a docstring claiming ICMR rates of
   25/40/30% (diabetes/HTN/arthritis for 60+), but the code actually used
   60/70/45% -- roughly double. Real elderly diabetes prevalence in India
   is much closer to the 25% figure, so the CODE has been changed to match
   the CITED rates, not the other way around.
4. dosage_map / frequency_map were being rebuilt from scratch on every
   single drug, for every patient (~1 lakh redundant dict constructions).
   Moved to module level, built once.
5. Age-distribution weights were being recomputed per-patient inside the
   loop, including a dead no-op line. Precomputed once.
6. list(set(...)) for drug dedup could silently reorder between runs.
   Replaced with list(dict.fromkeys(...)) for deterministic output.
7. Removed the unused `uuid` import and dropped `faker` -- neither was used.
8. Metformin's kidney-function contraindication now also applies at
   "Moderate Impairment", not just "Severe Impairment".
9. Drugs-per-condition weights changed from [0.55, 0.35, 0.10] (1/2/3 drugs)
   to [0.30, 0.50, 0.20] -- with the corrected, lower, clinically-honest
   prevalence rates from fix #3, the original weights only produced ~1.87
   drug records per patient (18,700 total at 10,000 patients, far short of
   the 1-lakh target). Heavier weights bring that up to ~2.29/patient.
10. N_PATIENTS is set to 43,700 (not 10,000 or 55,000). This was tuned by
   actually simulating the generator with fix #9's weights and fix #3's
   prevalence rates together: 43,700 x ~2.29 drugs/patient lands almost
   exactly on 100,000 records. (A separate attempt at fixing this bumped
   N to 55,000 without re-simulating against the new weights together --
   that combination actually produces ~124,000 records, about 24% over
   target, not the ~101,750 that was estimated.)
11. Fixed a real reporting bug, not just a display issue: the per-patient
   "highest_severity" summary was showing 0% Moderate, which looked like
   Moderate-severity pairs weren't being generated at all. They were --
   verified directly against the raw synthetic_patient_interactions.csv,
   where Moderate pairs are ~16% of all interaction records. The 0% was
   because "highest_severity" always reports a patient's single WORST
   interaction, and most patients who have a Moderate pair (almost always
   involving methotrexate) also have a Severe pair (methotrexate is
   involved in nearly every in-scope pair), which masks the Moderate one
   in the per-patient rollup. This is correct behavior for a "worst-case
   risk" column, not a bug -- but it was invisible and looked broken, so
   the summary output below now also prints the raw per-INTERACTION
   severity breakdown (not just the per-PATIENT worst-case breakdown),
   so both views are visible and neither looks silently wrong.
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = "."
DRUG_INTERACTIONS_CSV = "drug_interactions.csv"  # your real exported data

# ─────────────────────────────────────────────────────────────────────────────
# DRUG LISTS -- must match your 30-drug dataset exactly
# ─────────────────────────────────────────────────────────────────────────────

DIABETES_DRUGS = [
    "metformin", "glipizide", "glimepiride", "sitagliptin",
    "empagliflozin", "pioglitazone", "insulin-glargine",
    "dapagliflozin", "vildagliptin", "acarbose"
]

HTN_DRUGS = [
    "amlodipine", "losartan", "enalapril", "telmisartan",
    "hydrochlorothiazide", "atenolol", "ramipril",
    "chlorthalidone", "carvedilol", "clonidine"
]

ARTHRITIS_DRUGS = [
    "ibuprofen", "diclofenac", "naproxen", "methotrexate",
    "hydroxychloroquine", "celecoxib", "sulfasalazine",
    "prednisolone", "leflunomide", "colchicine"
]

ALL_DRUGS = {
    "Diabetes":     DIABETES_DRUGS,
    "Hypertension": HTN_DRUGS,
    "Arthritis":    ARTHRITIS_DRUGS,
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN INTERACTIONS -- loaded from your real drug_interactions.csv
# (in-scope pairs only: both drugs are within your 30-drug set)
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_RANK = {"Severe": 3, "Moderate": 2, "Mild": 1, "None": 0}

# Used ONLY if drug_interactions.csv can't be found. This is deliberately
# small and clearly separate from the real data so it's never mistaken for it.
FALLBACK_INTERACTIONS = {
    ("metformin", "ibuprofen"): "Severe",
    ("metformin", "amlodipine"): "Mild",
    ("amlodipine", "ibuprofen"): "Moderate",
}


def load_known_interactions(csv_path):
    """
    Load in-scope drug-drug interactions from the real exported CSV.
    Returns a dict keyed by frozenset({drug1, drug2}) -> severity string.
    Conflicting directional entries are resolved to the MORE severe rating,
    with a printed warning for each conflict found.
    """
    if not os.path.exists(csv_path):
        print(f"\n*** WARNING: '{csv_path}' not found. ***")
        print("*** Falling back to a tiny 3-pair hardcoded interaction set. ***")
        print("*** Your synthetic labels will NOT reflect your real Neo4j data. ***\n")
        return {frozenset(k): v for k, v in FALLBACK_INTERACTIONS.items()}

    df = pd.read_csv(csv_path)
    in_scope = df[df["drug2_in_scope"].astype(str).str.lower() == "yes"]

    resolved = {}
    conflicts = []
    for _, row in in_scope.iterrows():
        pair = frozenset({row["drug1_id"], row["drug2_id"]})
        sev = row["severity"]
        if pair in resolved and resolved[pair] != sev:
            conflicts.append((pair, resolved[pair], sev))
            if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(resolved[pair], 0):
                resolved[pair] = sev
        else:
            resolved[pair] = sev

    print(f"Loaded {len(resolved)} in-scope interaction pairs from '{csv_path}'.")
    if conflicts:
        print(f"\n*** WARNING: {len(conflicts)} pair(s) had conflicting severities "
              f"in the source CSV (resolved to the more severe rating): ***")
        for pair, sev_a, sev_b in conflicts:
            d1, d2 = tuple(pair)
            print(f"    {d1} <-> {d2}: saw both '{sev_a}' and '{sev_b}' "
                  f"-> kept '{resolved[pair]}'. Check your source data.")
        print()

    return resolved


KNOWN_INTERACTIONS = load_known_interactions(
    os.path.join(OUTPUT_DIR, DRUG_INTERACTIONS_CSV)
)


def get_interaction_severity(drug_list):
    """Return the highest severity among all drug pairs in the list."""
    highest = "None"
    for i in range(len(drug_list)):
        for j in range(i + 1, len(drug_list)):
            pair = frozenset({drug_list[i], drug_list[j]})
            sev = KNOWN_INTERACTIONS.get(pair)
            if sev and SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(highest, 0):
                highest = sev
    return highest


def get_all_interactions(drug_list):
    """Return a list of (drug1, drug2, severity) for every pair in drug_list."""
    results = []
    for i in range(len(drug_list)):
        for j in range(i + 1, len(drug_list)):
            d1, d2 = drug_list[i], drug_list[j]
            sev = KNOWN_INTERACTIONS.get(frozenset({d1, d2}), "None")
            results.append((d1, d2, sev))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# STATIC LOOKUP TABLES (built once, not per-patient / per-drug)
# ─────────────────────────────────────────────────────────────────────────────

REGIONS = [
    "Mangaluru", "Udupi", "Puttur", "Sullia", "Bantwal",
    "Kundapura", "Karkala", "Beltangady", "Moodbidri", "Manipal",
]

LANGUAGES = ["Tulu", "Kannada", "English"]
LANGUAGE_WEIGHTS = [0.55, 0.35, 0.10]  # coastal Karnataka realistic distribution

GENDERS = ["Male", "Female"]

DOSAGE_MAP = {
    "metformin": "500mg", "glipizide": "5mg", "glimepiride": "2mg",
    "sitagliptin": "100mg", "empagliflozin": "10mg", "pioglitazone": "15mg",
    "insulin-glargine": "10 units", "dapagliflozin": "10mg",
    "vildagliptin": "50mg", "acarbose": "25mg",
    "amlodipine": "5mg", "losartan": "50mg", "enalapril": "5mg",
    "telmisartan": "40mg", "hydrochlorothiazide": "12.5mg",
    "atenolol": "50mg", "ramipril": "5mg", "chlorthalidone": "12.5mg",
    "carvedilol": "6.25mg", "clonidine": "0.1mg",
    "ibuprofen": "400mg", "diclofenac": "50mg", "naproxen": "250mg",
    "methotrexate": "7.5mg", "hydroxychloroquine": "200mg",
    "celecoxib": "100mg", "sulfasalazine": "500mg", "prednisolone": "5mg",
    "leflunomide": "10mg", "colchicine": "0.5mg",
}

FREQUENCY_MAP = {
    "metformin": "Twice daily", "glipizide": "Once daily",
    "glimepiride": "Once daily", "sitagliptin": "Once daily",
    "empagliflozin": "Once daily", "pioglitazone": "Once daily",
    "insulin-glargine": "Once daily (bedtime)", "dapagliflozin": "Once daily",
    "vildagliptin": "Twice daily", "acarbose": "Thrice daily with meals",
    "amlodipine": "Once daily", "losartan": "Once daily",
    "enalapril": "Once daily", "telmisartan": "Once daily",
    "hydrochlorothiazide": "Once daily", "atenolol": "Once daily",
    "ramipril": "Once daily", "chlorthalidone": "Once daily",
    "carvedilol": "Twice daily", "clonidine": "Twice daily",
    "ibuprofen": "Thrice daily with food", "diclofenac": "Twice daily",
    "naproxen": "Twice daily", "methotrexate": "Once weekly",
    "hydroxychloroquine": "Once daily", "celecoxib": "Once daily",
    "sulfasalazine": "Twice daily", "prednisolone": "Once daily (morning)",
    "leflunomide": "Once daily", "colchicine": "Once or twice daily",
}

DRUG_TO_CONDITION = {
    drug: condition for condition, drugs in ALL_DRUGS.items() for drug in drugs
}

# ICMR NCD prevalence used for condition assignment. Matches the numbers
# actually cited in this file's own docstring (previously the code used
# 60/70/45% for 60+, roughly double these -- see change note #3 above).
PREVALENCE = {
    "60+":    {"Diabetes": 0.25, "Hypertension": 0.40, "Arthritis": 0.30},
    "45-59":  {"Diabetes": 0.15, "Hypertension": 0.20, "Arthritis": 0.10},
    "under45": {"Diabetes": 0.10, "Hypertension": 0.12, "Arthritis": 0.08},
}

# Age distribution weights, computed once (not per patient).
_AGE_RANGE = list(range(30, 85))  # 55 ages: 30-84
_RAW_WEIGHTS = np.array([0.004] * 15 + [0.013] * 15 + [0.025] * 25)  # 15+15+25=55
AGE_WEIGHTS = _RAW_WEIGHTS / _RAW_WEIGHTS.sum()


def assign_conditions(age):
    """
    Assign disease conditions based on age, following ICMR NCD prevalence
    (see PREVALENCE above). Co-occurrence is common in elderly patients,
    so each condition is rolled independently.
    """
    tier = "60+" if age >= 60 else ("45-59" if age >= 45 else "under45")
    rates = PREVALENCE[tier]

    conditions = [
        cond for cond in ("Diabetes", "Hypertension", "Arthritis")
        if random.random() < rates[cond]
    ]

    # This is an outpatient dataset -- every patient has at least one condition.
    if not conditions:
        conditions.append(random.choice(["Diabetes", "Hypertension", "Arthritis"]))

    return conditions


def assign_drugs(conditions, kidney_function, liver_function):
    """
    Assign 1-3 drugs per condition following clinical guidelines.
    Respects contraindications:
      - Metformin avoided at Moderate or Severe kidney impairment
        (tightened from the original Severe-only rule -- real prescribing
        guidance is cautious well before severe impairment).
      - Methotrexate/Leflunomide avoided if liver function is impaired.
    """
    assigned = []
    for condition in conditions:
        drug_pool = ALL_DRUGS[condition].copy()

        if condition == "Diabetes" and kidney_function in (
            "Moderate Impairment", "Severe Impairment"
        ):
            drug_pool = [
                d for d in drug_pool
                if d not in ("metformin", "empagliflozin", "dapagliflozin")
            ]

        if condition == "Arthritis" and liver_function == "Impaired":
            drug_pool = [d for d in drug_pool if d not in ("methotrexate", "leflunomide")]

        if not drug_pool:
            drug_pool = ALL_DRUGS[condition][:3]

        n_drugs = random.choices([1, 2, 3], weights=[0.30, 0.50, 0.20])[0]
        first = random.choice(drug_pool[:2])
        chosen = [first]
        remaining = [d for d in drug_pool if d != first]
        if n_drugs > 1 and remaining:
            chosen.extend(random.sample(remaining, min(n_drugs - 1, len(remaining))))

        assigned.extend(chosen)

    return list(dict.fromkeys(assigned))  # dedupe, order-preserving & deterministic


def generate_patient_share_id(n):
    """Generate n unique 6-character alphanumeric patient share IDs."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    ids = set()
    while len(ids) < n:
        ids.add("".join(random.choices(chars, k=6)))
    return list(ids)


# ─────────────────────────────────────────────────────────────────────────────
# GENERATE PATIENTS
# ─────────────────────────────────────────────────────────────────────────────

N_PATIENTS = 43700
print(f"Generating {N_PATIENTS} synthetic patients...")

share_ids = generate_patient_share_id(N_PATIENTS)

patient_records = []
patient_drug_records = []
patient_interaction_records = []

for i in range(N_PATIENTS):
    pid = f"P{i + 1:05d}"
    share_id = share_ids[i]

    age = int(np.random.choice(_AGE_RANGE, p=AGE_WEIGHTS))
    gender = random.choice(GENDERS)
    region = random.choice(REGIONS)
    language = random.choices(LANGUAGES, LANGUAGE_WEIGHTS)[0]

    kidney_function = random.choices(
        ["Normal", "Mild Impairment", "Moderate Impairment", "Severe Impairment"],
        weights=[0.65, 0.20, 0.10, 0.05],
    )[0]

    liver_function = random.choices(["Normal", "Impaired"], weights=[0.88, 0.12])[0]

    bmi_category = random.choices(
        ["Underweight", "Normal", "Overweight", "Obese"],
        weights=[0.08, 0.35, 0.38, 0.19],
    )[0]

    conditions = assign_conditions(age)
    drugs = assign_drugs(conditions, kidney_function, liver_function)

    highest_severity = get_interaction_severity(drugs)
    all_pairs = get_all_interactions(drugs)

    days_ago = random.randint(0, 730)
    registered = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    patient_records.append({
        "patient_id": pid,
        "patient_share_id": share_id,
        "age": age,
        "gender": gender,
        "region": region,
        "preferred_language": language,
        "conditions": "|".join(conditions),
        "n_conditions": len(conditions),
        "kidney_function": kidney_function,
        "liver_function": liver_function,
        "bmi_category": bmi_category,
        "n_drugs": len(drugs),
        "highest_severity": highest_severity,
        "registered_date": registered,
    })

    for drug in drugs:
        patient_drug_records.append({
            "patient_id": pid,
            "patient_share_id": share_id,
            "drug_id": drug,
            "condition_treated": DRUG_TO_CONDITION.get(drug, "Unknown"),
            "dosage": DOSAGE_MAP.get(drug, "Standard dose"),
            "frequency": FREQUENCY_MAP.get(drug, "As prescribed"),
            "is_active": True,
            "added_date": registered,
        })

    for d1, d2, severity in all_pairs:
        if severity != "None":
            patient_interaction_records.append({
                "patient_id": pid,
                "patient_share_id": share_id,
                "drug_1": d1,
                "drug_2": d2,
                "severity": severity,
                "disclaimer": "Consult your doctor before acting on this information.",
            })

# ─────────────────────────────────────────────────────────────────────────────
# SAVE OUTPUTS
# ─────────────────────────────────────────────────────────────────────────────

df_patients = pd.DataFrame(patient_records)
df_drugs = pd.DataFrame(patient_drug_records)
df_interact = pd.DataFrame(patient_interaction_records)

df_patients.to_csv(os.path.join(OUTPUT_DIR, "synthetic_patients.csv"),
                    index=False, encoding="utf-8-sig")
df_drugs.to_csv(os.path.join(OUTPUT_DIR, "synthetic_patient_drugs.csv"),
                index=False, encoding="utf-8-sig")
df_interact.to_csv(os.path.join(OUTPUT_DIR, "synthetic_patient_interactions.csv"),
                    index=False, encoding="utf-8-sig")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print("\n=== SYNTHETIC PATIENT DATASET SUMMARY ===")
print(f"\nPatients generated        : {len(df_patients):,}")
print(f"Patient-drug records      : {len(df_drugs):,}  <- this is your '1 lakh fields'")
print(f"Interaction risk records  : {len(df_interact):,}")

print("\nCondition distribution:")
for cond in ["Diabetes", "Hypertension", "Arthritis"]:
    n = df_patients["conditions"].str.contains(cond).sum()
    print(f"  {cond:<15}: {n:,} ({n / len(df_patients) * 100:.1f}%)")

all3 = df_patients["n_conditions"].eq(3).sum()
print(f"\nCo-occurrence (all 3 diseases): {all3:,} ({all3 / len(df_patients) * 100:.1f}%)")

print("\nInteraction severity breakdown (per-patient WORST-CASE severity --")
print("a patient with both a Moderate and a Severe pair counts as Severe here):")
for sev in ["Severe", "Moderate", "Mild", "None"]:
    n = df_patients["highest_severity"].eq(sev).sum()
    print(f"  {sev:<10}: {n:,} ({n / len(df_patients) * 100:.1f}%)")

print("\nInteraction severity breakdown (RAW, per individual interaction record --")
print("this is the one to check if the summary above looks like Moderate is missing;")
print("it isn't missing, it's just usually outranked by a Severe pair on the same patient):")
if len(df_interact) > 0:
    for sev in ["Severe", "Moderate", "Mild"]:
        n = df_interact["severity"].eq(sev).sum()
        print(f"  {sev:<10}: {n:,} ({n / len(df_interact) * 100:.1f}%)")
else:
    print("  (no interaction records generated)")

print("\nLanguage distribution:")
for lang in ["Tulu", "Kannada", "English"]:
    n = df_patients["preferred_language"].eq(lang).sum()
    print(f"  {lang:<10}: {n:,} ({n / len(df_patients) * 100:.1f}%)")

print("\nAge distribution:")
print(f"  Mean age   : {df_patients['age'].mean():.1f} years")
print(f"  60+ years  : {df_patients['age'].ge(60).sum():,}")
print(f"  45-59 years: {df_patients['age'].between(45, 59).sum():,}")

print("\nFiles saved:")
print("  synthetic_patients.csv")
print("  synthetic_patient_drugs.csv")
print("  synthetic_patient_interactions.csv")
print("\nData source note for documentation:")
print("  Synthetic data generated following ICMR NCD prevalence statistics,")
print("  ADA/JNC8/ACR clinical guidelines, and coastal Karnataka demographic")
print("  distribution. Interaction severities are loaded directly from the")
print("  real drug_interactions.csv used by NeoGraphMed's Neo4j graph.")
print("  Not real patient data.")