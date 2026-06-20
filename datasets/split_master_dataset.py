import os
import re
import sys
import pandas as pd
 
# ------------------------------------------------------------------
# CONFIG — reads and writes in the current folder (e.g. datasets/)
# ------------------------------------------------------------------
INPUT_CSV = "english_master_dataset.csv"
OUTPUT_DIR = "."
 
if not os.path.exists(INPUT_CSV):
    sys.exit(
        f"ERROR: Could not find '{INPUT_CSV}' in the current folder.\n"
        "Run build_dataset.py first to create it."
    )
 
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
df = pd.read_csv(INPUT_CSV)
 
# ------------------------------------------------------------------
# SHARED CLEANUP HELPERS
# ------------------------------------------------------------------
 
CITATION_PATTERN = re.compile(r"\(Source:.*?\)", flags=re.IGNORECASE)
 
 
def strip_citation(text: str) -> str:
    """Remove trailing '(Source: ...)' citation blocks from any text field."""
    if not isinstance(text, str):
        return ""
    text = CITATION_PATTERN.sub("", text)
    return text.strip()
 
 
def clean_fragment(text: str) -> str:
    """General whitespace / punctuation cleanup for an extracted fragment."""
    text = text.strip()
    text = re.sub(r"^[\-–—:;,\s]+", "", text)   # leading punctuation/dashes
    text = re.sub(r"[\-–—:;,\s]+$", "", text)   # trailing punctuation/dashes
    text = re.sub(r"\s+", " ", text)            # collapse whitespace
    return text.strip()
 
 
def slugify(text: str) -> str:
    """
    Convert a name into a stable lowercase, hyphenated ID for Neo4j MERGE.
    e.g. "Insulin Glargine" -> "insulin-glargine"
         "Type 2 Diabetes"  -> "type-2-diabetes"
    """
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text
 
 
# Severity / qualifier prefixes that sometimes precede a side-effect list,
# e.g. "Rare but serious: lactic acidosis", "Rare: angioedema"
SEVERITY_PREFIX_PATTERN = re.compile(
    r"^(rare(\s+but\s+serious)?|serious|common|very\s+common|"
    r"boxed\s+warning|critical)\s*:\s*",
    flags=re.IGNORECASE,
)
 
 
def split_into_sentences(text: str) -> list:
    """
    Parenthesis-aware sentence splitter.
 
    Splits on ". " only when NOT currently inside an open parenthesis.
    This avoids incorrectly breaking text like
    "angioedema (rare vs. ACE inhibitors)" at the "vs." abbreviation,
    which a naive regex-based splitter is vulnerable to.
    """
    sentences = []
    buf = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        buf.append(ch)
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "." and depth == 0:
            if i + 1 >= n or text[i + 1] in (" ", "\n"):
                sentence = "".join(buf).strip()
                if sentence:
                    sentences.append(sentence.rstrip("."))
                buf = []
        i += 1
    remainder = "".join(buf).strip().rstrip(".")
    if remainder:
        sentences.append(remainder)
    return [s for s in sentences if s]
 
 
def split_comma_list_respecting_parens(text: str) -> list:
    """
    Split a comma-separated list into parts, but do NOT split on commas
    that occur inside parentheses (e.g. "skin reactions (pruritus,
    erythema, urticaria)" should stay as ONE entry, not three).
    """
    parts = []
    buf = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts
 
 
# ------------------------------------------------------------------
# 1. drug_disease.csv
# ------------------------------------------------------------------
 
def build_drug_disease(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["drug_name", "disease"]].copy()
    out["drug_name"] = out["drug_name"].str.strip()
    out["disease"] = out["disease"].str.strip()
    out["drug_id"] = out["drug_name"].apply(slugify)
    out["disease_id"] = out["disease"].apply(slugify)
    out = out[["drug_id", "drug_name", "disease_id", "disease"]]
    out = out.drop_duplicates().reset_index(drop=True)
    return out
 
 
# ------------------------------------------------------------------
# 2. drug_sideeffects.csv
# ------------------------------------------------------------------
 
def split_side_effects(raw_text: str) -> list:
    """
    Turn a free-text side_effects field into a clean list of individual
    side effects (one term/phrase per entry), using the parenthesis-aware
    splitter so compound phrases like "skin reactions (pruritus,
    erythema, urticaria)" or "angioedema (rare vs. ACE inhibitors)"
    are NOT incorrectly broken apart.
    """
    text = strip_citation(raw_text)
    if not text:
        return []
 
    sentences = split_into_sentences(text)
 
    effects = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
 
        # Drop a leading severity/qualifier label like "Rare but serious:"
        sentence = SEVERITY_PREFIX_PATTERN.sub("", sentence)
 
        # Split remaining sentence on commas (respecting parentheses)
        parts = split_comma_list_respecting_parens(sentence)
        for part in parts:
            part = clean_fragment(part)
            if not part:
                continue
            # Drop pure boilerplate fragments that aren't real side effects
            if re.fullmatch(r"(and|or)", part, flags=re.IGNORECASE):
                continue
            # Normalize leading "and "
            part = re.sub(r"^(and|or)\s+", "", part, flags=re.IGNORECASE)
            part = clean_fragment(part)
            if part:
                effects.append(part)
 
    # De-duplicate while preserving order
    seen = set()
    unique_effects = []
    for e in effects:
        key = e.lower()
        if key not in seen:
            seen.add(key)
            unique_effects.append(e)
 
    return unique_effects
 
 
def build_drug_sideeffects(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        drug = row["drug_name"].strip()
        drug_id = slugify(drug)
        effects = split_side_effects(row["side_effects"])
        for effect in effects:
            rows.append({"drug_id": drug_id, "drug_name": drug, "side_effect": effect})
 
    out = pd.DataFrame(rows, columns=["drug_id", "drug_name", "side_effect"])
    out = out.drop_duplicates().reset_index(drop=True)
    return out
 
 
# ------------------------------------------------------------------
# 3. drug_interactions.csv
# ------------------------------------------------------------------
 
# Keyword cues used to classify severity of an interaction sentence.
SEVERE_KEYWORDS = [
    "fatal", "contraindicated", "boxed warning", "potentially fatal",
    "life-threatening", "avoid combination", "avoid concomitant",
    "do not use", "severe bradycardia", "significantly increase",
    "dramatically increase", "serious hyperkalemia",
]
MODERATE_KEYWORDS = [
    "monitor", "increase", "increases", "increased", "reduce", "reduces",
    "reduced", "risk", "caution", "may", "additive",
]
 
 
def classify_severity(effect_text: str) -> str:
    text = effect_text.lower()
    if any(kw in text for kw in SEVERE_KEYWORDS):
        return "Severe"
    if any(kw in text for kw in MODERATE_KEYWORDS):
        return "Moderate"
    return "Mild"
 
 
def split_interactions(raw_text: str) -> list:
    """
    Turn a free-text major_interactions field into a list of
    (interacting_agent, effect_text) tuples.
 
    Sentences are generally structured as:
        "<Agent(s)>: <effect description>."
    Agent(s) may include a parenthetical example list, e.g.:
        "CYP3A4 inhibitors (ketoconazole, ritonavir, clarithromycin): ..."
    In that case we use the named example drugs (inside parentheses)
    as the interacting agent(s) rather than the drug-class label,
    since those are concrete drug names suitable for a drug-drug pair.
    If no parenthetical example exists, the class/agent label itself
    is used as the interacting "drug" entry — and if THAT label is
    itself a comma- or slash-joined list (e.g. "Fluconazole, miconazole"
    or "Warfarin/anticoagulants"), it is split into individual agents too.
    """
    text = strip_citation(raw_text)
    if not text:
        return []
 
    sentences = split_into_sentences(text)
 
    pairs = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or ":" not in sentence:
            continue
 
        agent_part, effect_part = sentence.split(":", 1)
        agent_part = agent_part.strip()
        effect_part = effect_part.strip()
 
        # Extract any parenthetical example drug names: "(topiramate, acetazolamide)"
        paren_match = re.search(r"\(([^)]+)\)", agent_part)
        if paren_match:
            examples = [clean_fragment(x) for x in paren_match.group(1).split(",")]
            examples = [e for e in examples if e]
        else:
            examples = []
 
        # Remove the parenthetical from the agent label itself
        agent_label = re.sub(r"\([^)]*\)", "", agent_part)
        agent_label = clean_fragment(agent_label)
        agent_label = re.sub(r"^(and|or)\s+", "", agent_label, flags=re.IGNORECASE)
 
        # If the agent label looks like a real multi-drug name list,
        # split it into individual agents rather than keeping one combined
        # label. Two patterns occur in the source text:
        #   - slash-joined synonyms/classes: "Warfarin/anticoagulants"
        #   - comma-joined drug names:       "Fluconazole, miconazole"
        if not examples:
            if "/" in agent_label:
                examples = [clean_fragment(x) for x in agent_label.split("/")]
            elif "," in agent_label:
                examples = [clean_fragment(x) for x in agent_label.split(",")]
 
        agents_to_use = examples if examples else [agent_label]
 
        for agent in agents_to_use:
            agent = clean_fragment(agent)
            if not agent:
                continue
            pairs.append((agent, effect_part))
 
    return pairs
 
 
def build_drug_interactions(df: pd.DataFrame, known_drug_ids: set) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        drug1 = row["drug_name"].strip()
        drug1_id = slugify(drug1)
        interaction_pairs = split_interactions(row["major_interactions"])
        for agent, effect_text in interaction_pairs:
            drug2 = agent.title() if agent.islower() else agent
            drug2_id = slugify(drug2)
            severity = classify_severity(effect_text)
            rows.append({
                "drug1_id": drug1_id,
                "drug1": drug1,
                "drug2_id": drug2_id,
                "drug2": drug2,
                "drug2_in_scope": "yes" if drug2_id in known_drug_ids else "no",
                "severity": severity,
            })
 
    out = pd.DataFrame(
        rows,
        columns=["drug1_id", "drug1", "drug2_id", "drug2", "drug2_in_scope", "severity"],
    )
    out = out.drop_duplicates().reset_index(drop=True)
    return out
 
 
# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
 
def main():
    drug_disease_df = build_drug_disease(df)
    known_drug_ids = set(drug_disease_df["drug_id"])
 
    drug_sideeffects_df = build_drug_sideeffects(df)
    drug_interactions_df = build_drug_interactions(df, known_drug_ids)
 
    drug_disease_path = os.path.join(OUTPUT_DIR, "drug_disease.csv")
    drug_sideeffects_path = os.path.join(OUTPUT_DIR, "drug_sideeffects.csv")
    drug_interactions_path = os.path.join(OUTPUT_DIR, "drug_interactions.csv")
 
    drug_disease_df.to_csv(drug_disease_path, index=False, encoding="utf-8")
    drug_sideeffects_df.to_csv(drug_sideeffects_path, index=False, encoding="utf-8")
    drug_interactions_df.to_csv(drug_interactions_path, index=False, encoding="utf-8")
 
    in_scope_count = (drug_interactions_df["drug2_in_scope"] == "yes").sum()
    out_scope_count = (drug_interactions_df["drug2_in_scope"] == "no").sum()
 
    print("=== SPLIT COMPLETE ===")
    print(f"drug_disease.csv       -> {len(drug_disease_df)} records  ({os.path.abspath(drug_disease_path)})")
    print(f"drug_sideeffects.csv   -> {len(drug_sideeffects_df)} records  ({os.path.abspath(drug_sideeffects_path)})")
    print(f"drug_interactions.csv  -> {len(drug_interactions_df)} records  ({os.path.abspath(drug_interactions_path)})")
    print(f"\n  drug2_in_scope = yes (real drug in your master dataset): {in_scope_count}")
    print(f"  drug2_in_scope = no  (external substance/class, e.g. Alcohol, NSAIDs): {out_scope_count}")
 
    print("\n--- drug_disease.csv preview ---")
    print(drug_disease_df.head(5).to_string(index=False))
 
    print("\n--- drug_sideeffects.csv preview ---")
    print(drug_sideeffects_df.head(8).to_string(index=False))
 
    print("\n--- drug_interactions.csv preview ---")
    print(drug_interactions_df.head(8).to_string(index=False))
 
    print("\n--- severity distribution ---")
    print(drug_interactions_df["severity"].value_counts())
 
 
if __name__ == "__main__":
    main()