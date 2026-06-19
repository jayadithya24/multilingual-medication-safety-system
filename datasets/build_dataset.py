import pandas as pd
import textwrap

# ============================================================
# english_master_dataset.csv
# Sources: FDA Drug Labels (DailyMed/OpenFDA), DrugBank CC BY-NC 4.0,
#          RxNorm, SIDER, ICMR Guidelines, WHO ATC Classification
# All content reflects published official label / database text.
# ============================================================

records = [

    # ─────────────────────────────────────────────────────────
    # TYPE 2 DIABETES  (10 drugs)
    # ─────────────────────────────────────────────────────────
    {
        "drug_name": "Metformin",
        "generic_name": "metformin hydrochloride",
        "disease": "Type 2 Diabetes",
        "drug_class": "Biguanide",
        "active_ingredient": "Metformin Hydrochloride",
        "description": (
            "Metformin is an oral antihyperglycemic agent used as first-line pharmacotherapy "
            "for type 2 diabetes mellitus. It decreases hepatic glucose production, decreases "
            "intestinal absorption of glucose, and improves insulin sensitivity by increasing "
            "peripheral glucose uptake and utilization. It does not cause hypoglycemia when used "
            "as monotherapy. (Source: FDA label; ICMR Diabetes Guidelines 2018)"
        ),
        "side_effects": (
            "Diarrhea, nausea, vomiting, flatulence, abdominal discomfort, indigestion, "
            "headache, decreased vitamin B12 absorption (long-term use), metallic taste. "
            "Rare but serious: lactic acidosis. (Source: FDA DailyMed label; SIDER)"
        ),
        "contraindications": (
            "Renal impairment (eGFR < 30 mL/min/1.73 m²); acute or chronic metabolic acidosis "
            "including diabetic ketoacidosis; hypersensitivity to metformin; temporary withhold "
            "for iodinated contrast media procedures. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Lactic acidosis — rare but potentially fatal; risk increases with "
            "renal impairment, hepatic impairment, congestive heart failure, alcohol use, "
            "and in patients ≥65 years. Hold before surgery and contrast procedures. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Carbonic anhydrase inhibitors (topiramate, acetazolamide): increased lactic acidosis risk. "
            "Alcohol: potentiates lactic acidosis risk. Iodinated contrast agents: hold 48 h before/after. "
            "Cimetidine: increases metformin plasma levels. (Source: RxNav/DrugBank DDI)"
        ),
        "source": "FDA DailyMed; DrugBank DB00331; RxNorm CUI 41493; ICMR 2018"
    },

    {
        "drug_name": "Glipizide",
        "generic_name": "glipizide",
        "disease": "Type 2 Diabetes",
        "drug_class": "Sulfonylurea (2nd generation)",
        "active_ingredient": "Glipizide",
        "description": (
            "Glipizide is a second-generation sulfonylurea oral hypoglycemic agent. It stimulates "
            "the release of insulin from functioning pancreatic beta cells by binding to the "
            "sulfonylurea receptor (SUR1), closing ATP-sensitive potassium channels. Used as "
            "adjunct to diet and exercise in type 2 diabetes. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Hypoglycemia (most common), nausea, diarrhea, constipation, dizziness, headache, "
            "skin rash, photosensitivity, weight gain. Rare: blood dyscrasias, hepatotoxicity, "
            "hyponatremia (SIADH). (Source: FDA DailyMed label; SIDER)"
        ),
        "contraindications": (
            "Type 1 diabetes mellitus; diabetic ketoacidosis; hypersensitivity to glipizide or "
            "other sulfonamides; severe renal or hepatic impairment. Not recommended during "
            "pregnancy. (Source: FDA label)"
        ),
        "warnings": (
            "Hypoglycemia: risk increased in elderly, debilitated patients, renal/hepatic impairment, "
            "irregular meals, strenuous exercise, alcohol use. Cardiovascular mortality risk associated "
            "with sulfonylureas (UGDP study). Hemolytic anemia in G6PD-deficient patients. "
            "(Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Fluconazole, miconazole: increased hypoglycemia risk (CYP2C9 inhibition). "
            "NSAIDs, warfarin, salicylates: potentiate hypoglycemic effect. "
            "Beta-blockers: mask hypoglycemia symptoms. Rifampin: reduces glipizide efficacy. "
            "(Source: RxNav/DrugBank DDI)"
        ),
        "source": "FDA DailyMed; DrugBank DB01067; RxNorm CUI 4815"
    },

    {
        "drug_name": "Glimepiride",
        "generic_name": "glimepiride",
        "disease": "Type 2 Diabetes",
        "drug_class": "Sulfonylurea (3rd generation)",
        "active_ingredient": "Glimepiride",
        "description": (
            "Glimepiride is a third-generation sulfonylurea that stimulates insulin secretion "
            "from pancreatic beta cells. It has a lower hypoglycemia risk than older sulfonylureas "
            "and may have extrapancreatic glucose-lowering effects. Used as monotherapy or combined "
            "with metformin or insulin. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Hypoglycemia, dizziness, headache, nausea, asthenia, weight gain, skin reactions "
            "(pruritus, erythema, urticaria). Rare: leukopenia, agranulocytosis, "
            "thrombocytopenia, hemolytic anemia. (Source: FDA label; SIDER)"
        ),
        "contraindications": (
            "Type 1 diabetes; diabetic ketoacidosis; hypersensitivity to glimepiride or "
            "sulfonamides; severe renal impairment (CrCl < 22 mL/min); hepatic impairment. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Hypoglycemia is the primary risk — especially with irregular meals, renal/hepatic "
            "impairment, or elderly patients. Hemolytic anemia possible in G6PD deficiency. "
            "Cardiovascular mortality warning (UGDP data). (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "CYP2C9 inhibitors (fluconazole, gemfibrozil): significantly increase glimepiride exposure. "
            "ACE inhibitors, salicylates: enhance hypoglycemic effect. "
            "Corticosteroids, thiazides: antagonize effect. (Source: DrugBank; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00222; RxNorm CUI 25789"
    },

    {
        "drug_name": "Sitagliptin",
        "generic_name": "sitagliptin phosphate",
        "disease": "Type 2 Diabetes",
        "drug_class": "DPP-4 Inhibitor (Gliptin)",
        "active_ingredient": "Sitagliptin Phosphate Monohydrate",
        "description": (
            "Sitagliptin (Januvia) is a dipeptidyl peptidase-4 (DPP-4) inhibitor that increases "
            "active incretin levels (GLP-1 and GIP), which stimulate insulin release and suppress "
            "glucagon in a glucose-dependent manner. Low intrinsic hypoglycemia risk. "
            "Used as monotherapy or add-on therapy. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Nasopharyngitis, upper respiratory tract infection, headache, urinary tract infection. "
            "Rare but serious: acute pancreatitis, severe joint pain (arthralgia), "
            "bullous pemphigoid, hypersensitivity reactions (anaphylaxis, angioedema). "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "History of serious hypersensitivity to sitagliptin; prior history of pancreatitis "
            "(use with caution). Not for type 1 diabetes or diabetic ketoacidosis. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Acute pancreatitis: discontinue if suspected. Severe and disabling arthralgia reported. "
            "Heart failure: use cautiously in patients with existing heart failure "
            "(saxagliptin class warning may apply). Renal dose adjustment required. "
            "(Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Digoxin: sitagliptin may slightly increase digoxin levels (monitor). "
            "Insulin/sulfonylureas: increased hypoglycemia risk when combined. "
            "No significant CYP interactions. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB01261; RxNorm CUI 593411"
    },

    {
        "drug_name": "Empagliflozin",
        "generic_name": "empagliflozin",
        "disease": "Type 2 Diabetes",
        "drug_class": "SGLT-2 Inhibitor",
        "active_ingredient": "Empagliflozin",
        "description": (
            "Empagliflozin (Jardiance) is a sodium-glucose co-transporter 2 (SGLT-2) inhibitor "
            "that reduces renal glucose reabsorption and lowers the renal threshold for glucose, "
            "resulting in increased urinary glucose excretion. Has proven cardiovascular and "
            "renal protective benefits in T2DM. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Urinary tract infections, genital mycotic infections (candidiasis), "
            "increased urination, nasopharyngitis, dyslipidemia, nausea. Rare: "
            "diabetic ketoacidosis (even with near-normal glucose), Fournier's gangrene, "
            "lower limb amputation risk. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "eGFR < 30 mL/min/1.73 m² (for glycemic use); history of serious hypersensitivity "
            "to empagliflozin; dialysis-dependent patients. Not for type 1 diabetes. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Diabetic ketoacidosis: can occur with near-normal blood glucose — hold before surgery. "
            "Fournier's gangrene (necrotizing fasciitis of the perineum): rare but life-threatening. "
            "Hypotension: volume depletion risk especially with diuretics or in elderly. "
            "Lower limb amputations: monitor. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Insulin/insulin secretagogues: increased hypoglycemia risk — dose reduction may be needed. "
            "Diuretics: additive diuretic effect, increased dehydration/hypotension risk. "
            "UGT inducers (rifampin): may reduce empagliflozin efficacy. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB09038; RxNorm CUI 1373463"
    },

    {
        "drug_name": "Pioglitazone",
        "generic_name": "pioglitazone hydrochloride",
        "disease": "Type 2 Diabetes",
        "drug_class": "Thiazolidinedione (TZD / Glitazone)",
        "active_ingredient": "Pioglitazone Hydrochloride",
        "description": (
            "Pioglitazone (Actos) is a thiazolidinedione that acts as a peroxisome proliferator-"
            "activated receptor gamma (PPARγ) agonist. It decreases insulin resistance in "
            "peripheral tissues and liver. Improves insulin sensitivity without increasing "
            "insulin secretion. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Weight gain, edema, upper respiratory infection, headache, sinusitis. "
            "Serious: fluid retention/heart failure exacerbation, bone fractures (especially in women), "
            "macular edema, bladder cancer risk with prolonged use. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "NYHA Class III or IV heart failure; active bladder cancer or history of bladder cancer; "
            "hypersensitivity to pioglitazone. Not for type 1 diabetes. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Congestive heart failure — fluid retention can worsen or initiate "
            "heart failure. Bladder cancer: do not use if active bladder cancer. "
            "Bone fractures increased in women. Macular edema: ophthalmic examination recommended. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "CYP2C8 inhibitors (gemfibrozil): significantly increase pioglitazone exposure — "
            "limit dose to 15 mg/day. CYP2C8 inducers (rifampin): reduce efficacy. "
            "Insulin: additive fluid retention, heart failure risk. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB01132; RxNorm CUI 33738"
    },

    {
        "drug_name": "Insulin Glargine",
        "generic_name": "insulin glargine",
        "disease": "Type 2 Diabetes",
        "drug_class": "Long-acting Basal Insulin Analog",
        "active_ingredient": "Insulin Glargine (rDNA origin)",
        "description": (
            "Insulin glargine (Lantus, Basaglar) is a recombinant long-acting insulin analog "
            "with a duration of action of approximately 24 hours and no pronounced peak. "
            "It is used for once-daily subcutaneous injection to provide basal glycemic control "
            "in type 1 and type 2 diabetes mellitus. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Hypoglycemia (most common and serious), injection site reactions (pain, redness, "
            "swelling, lipodystrophy), weight gain, edema, peripheral edema, hypokalemia, "
            "allergic reactions. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Hypersensitivity to insulin glargine or any of its excipients. "
            "Do not use during episodes of hypoglycemia. Not for IV administration. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Hypoglycemia: most common adverse effect — can be life-threatening. "
            "Never mix or dilute with other insulins or solutions. "
            "Monitor potassium in patients at risk for hypokalemia. "
            "Changes in insulin regimen should be made cautiously. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Beta-blockers: mask hypoglycemia symptoms and may delay recovery. "
            "ACE inhibitors, salicylates, MAO inhibitors: increase insulin sensitivity — "
            "increased hypoglycemia risk. Corticosteroids, thiazides, atypical antipsychotics: "
            "antagonize glucose-lowering effect. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00047; RxNorm CUI 274783"
    },

    {
        "drug_name": "Dapagliflozin",
        "generic_name": "dapagliflozin",
        "disease": "Type 2 Diabetes",
        "drug_class": "SGLT-2 Inhibitor",
        "active_ingredient": "Dapagliflozin Propanediol",
        "description": (
            "Dapagliflozin (Farxiga/Forxiga) is an SGLT-2 inhibitor that blocks reabsorption "
            "of glucose in the proximal renal tubule, promoting urinary glucose excretion. "
            "Also approved for heart failure with reduced ejection fraction and chronic kidney "
            "disease, regardless of diabetes status. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Female genital mycotic infections, urinary tract infections, nasopharyngitis, "
            "back pain, increased urination, nausea, dyslipidemia. Rare: "
            "diabetic ketoacidosis (DKA), Fournier's gangrene, urosepsis. "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Severe renal impairment (eGFR < 25 mL/min for glycemic use); "
            "end-stage renal disease; dialysis; type 1 diabetes (for glycemic indication); "
            "hypersensitivity to dapagliflozin. (Source: FDA label)"
        ),
        "warnings": (
            "Diabetic ketoacidosis: possible even at near-normal glucose levels. "
            "Volume depletion/hypotension: especially in elderly or diuretic users. "
            "Fournier's gangrene: rare, serious — assess perineal area immediately if pain/swelling. "
            "Urosepsis and pyelonephritis reported. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Insulin/sulfonylureas: increased hypoglycemia risk. "
            "Diuretics: additive diuretic effect, volume depletion risk. "
            "UGT1A9 inhibitors (mefenamic acid): may increase dapagliflozin exposure. "
            "(Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB06292; RxNorm CUI 1488564"
    },

    {
        "drug_name": "Vildagliptin",
        "generic_name": "vildagliptin",
        "disease": "Type 2 Diabetes",
        "drug_class": "DPP-4 Inhibitor (Gliptin)",
        "active_ingredient": "Vildagliptin",
        "description": (
            "Vildagliptin (Galvus) is a DPP-4 inhibitor widely used in India and Europe for "
            "type 2 diabetes. It enhances incretin-mediated insulin secretion and suppresses "
            "inappropriate glucagon secretion in a glucose-dependent manner. Commonly used as "
            "add-on to metformin. Approved by CDSCO for India. (Source: DrugBank; CDSCO)"
        ),
        "side_effects": (
            "Nasopharyngitis, headache, dizziness, peripheral edema, nausea. "
            "Hepatic enzyme elevations (liver function monitoring required). "
            "Rare: acute pancreatitis, severe cutaneous adverse reactions, "
            "upper respiratory infections. (Source: DrugBank; EMA label)"
        ),
        "contraindications": (
            "Hepatic impairment (ALT or AST > 3× ULN); severe renal impairment if not dose-adjusted; "
            "hypersensitivity to vildagliptin; type 1 diabetes; diabetic ketoacidosis. "
            "(Source: EMA label; DrugBank)"
        ),
        "warnings": (
            "Liver function tests recommended before initiation and periodically during treatment. "
            "Discontinue if hepatic impairment develops. Acute pancreatitis: monitor and discontinue "
            "if suspected. (Source: EMA SmPC; DrugBank DB04876)"
        ),
        "major_interactions": (
            "Insulin/sulfonylureas: dose reduction of secretagogue may be needed to reduce "
            "hypoglycemia risk. ACE inhibitors: increased risk of angioedema reported. "
            "No significant CYP-based interactions. (Source: DrugBank; EMA label)"
        ),
        "source": "DrugBank DB04876; EMA SmPC; CDSCO approved list; RxNorm CUI 414864"
    },

    {
        "drug_name": "Acarbose",
        "generic_name": "acarbose",
        "disease": "Type 2 Diabetes",
        "drug_class": "Alpha-Glucosidase Inhibitor",
        "active_ingredient": "Acarbose",
        "description": (
            "Acarbose (Glucobay, Precose) is an alpha-glucosidase inhibitor that competitively "
            "inhibits intestinal enzymes (maltase, sucrase, dextranase) that digest complex "
            "carbohydrates. It slows carbohydrate absorption and reduces postprandial glucose "
            "excursions. Particularly useful in India given high-carbohydrate diets. "
            "(Source: FDA label; ICMR Diabetes Guidelines)"
        ),
        "side_effects": (
            "Flatulence (very common), abdominal pain, diarrhea, bloating — these are "
            "dose-related and often decrease over time. Rare: elevated liver enzymes, "
            "hepatotoxicity with high doses, ileus. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Inflammatory bowel disease, colonic ulceration, partial intestinal obstruction, "
            "chronic intestinal diseases with absorption disorders; "
            "cirrhosis; serum creatinine > 2 mg/dL; type 1 diabetes. (Source: FDA label)"
        ),
        "warnings": (
            "GI adverse effects: titrate dose slowly starting at 25 mg to minimize. "
            "Hypoglycemia: when combined with insulin/sulfonylurea, must treat with glucose "
            "(not sucrose — sucrase is inhibited). Liver enzyme elevation: monitor at "
            "6, 12 months then annually. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Digestive enzyme preparations (amylase, pancreatin): reduce acarbose efficacy — "
            "avoid concomitant use. Activated charcoal: reduces acarbose effect — avoid. "
            "Digoxin: acarbose may reduce digoxin bioavailability. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00284; RxNorm CUI 16681; ICMR 2018"
    },

    # ─────────────────────────────────────────────────────────
    # HYPERTENSION  (10 drugs)
    # ─────────────────────────────────────────────────────────
    {
        "drug_name": "Amlodipine",
        "generic_name": "amlodipine besylate",
        "disease": "Hypertension",
        "drug_class": "Calcium Channel Blocker (Dihydropyridine)",
        "active_ingredient": "Amlodipine Besylate",
        "description": (
            "Amlodipine (Norvasc) is a dihydropyridine calcium channel blocker that inhibits "
            "the transmembrane influx of calcium ions into vascular smooth muscle and cardiac "
            "muscle. It reduces peripheral vascular resistance and blood pressure. "
            "Also approved for angina. Widely used first-line antihypertensive in India. "
            "(Source: FDA label; ICMR Hypertension Guidelines)"
        ),
        "side_effects": (
            "Peripheral edema (most common), flushing, headache, dizziness, palpitations, "
            "fatigue, somnolence, nausea. Rare: gingival hyperplasia, hepatotoxicity, "
            "severe hypotension. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Known hypersensitivity to amlodipine or dihydropyridines. "
            "Use with caution in severe aortic stenosis. (Source: FDA label)"
        ),
        "warnings": (
            "Hypotension: excessive hypotension can occur, especially in severe aortic stenosis. "
            "Worsening angina or myocardial infarction: acute onset may occur when starting "
            "calcium channel blockers (particularly in patients with obstructive CAD). "
            "Peripheral edema may require dose reduction. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "CYP3A4 inhibitors (ketoconazole, ritonavir, clarithromycin): increase amlodipine "
            "levels significantly — monitor BP. CYP3A4 inducers (rifampin): reduce efficacy. "
            "Simvastatin: limit simvastatin to 20 mg/day (FDA 2011 safety update). "
            "Cyclosporine, tacrolimus: amlodipine may increase levels. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00381; RxNorm CUI 17767; ICMR HTN Guidelines"
    },

    {
        "drug_name": "Losartan",
        "generic_name": "losartan potassium",
        "disease": "Hypertension",
        "drug_class": "Angiotensin II Receptor Blocker (ARB)",
        "active_ingredient": "Losartan Potassium",
        "description": (
            "Losartan (Cozaar) is an angiotensin II receptor antagonist (AT1 subtype) that "
            "blocks vasoconstriction and aldosterone-secreting effects of angiotensin II. "
            "It reduces blood pressure and has proven renoprotective effects in diabetic "
            "nephropathy. Preferred in patients with ACE inhibitor cough. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Dizziness, upper respiratory infection, nasal congestion, back pain, fatigue, "
            "hyperkalemia, elevated serum creatinine. Rare: angioedema (rare vs. ACE inhibitors), "
            "hypotension, renal impairment. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy (all trimesters — causes fetal harm/death); "
            "concomitant use with aliskiren in patients with diabetes or renal impairment (eGFR < 60); "
            "hypersensitivity to losartan. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Fetal toxicity — discontinue immediately if pregnancy detected. "
            "Hypotension: in volume/salt-depleted patients. Renal impairment/failure: "
            "monitor renal function, especially with NSAIDs. Hyperkalemia: monitor potassium. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Aliskiren: contraindicated in diabetes or renal impairment. "
            "Potassium supplements/potassium-sparing diuretics: hyperkalemia risk. "
            "NSAIDs: reduce antihypertensive effect and may worsen renal function. "
            "Lithium: losartan increases lithium toxicity. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00678; RxNorm CUI 203160"
    },

    {
        "drug_name": "Enalapril",
        "generic_name": "enalapril maleate",
        "disease": "Hypertension",
        "drug_class": "ACE Inhibitor",
        "active_ingredient": "Enalapril Maleate",
        "description": (
            "Enalapril (Vasotec) is a prodrug converted to enalaprilat in the liver, which "
            "inhibits angiotensin-converting enzyme (ACE). This reduces formation of angiotensin II "
            "and decreases aldosterone secretion, leading to vasodilation and reduced blood pressure. "
            "Also used in heart failure and asymptomatic LV dysfunction. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Dry persistent cough (very common, 10–20%), dizziness, headache, fatigue, "
            "hyperkalemia, elevated creatinine. Rare but serious: angioedema (can be "
            "life-threatening), neutropenia/agranulocytosis (in renal impairment). "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy; history of ACE inhibitor-associated angioedema; "
            "hereditary or idiopathic angioedema; concomitant use with aliskiren in diabetes "
            "or renal impairment; concomitant use with sacubitril/valsartan (36 h washout needed). "
            "(Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Fetal toxicity — discontinue if pregnancy detected. "
            "Angioedema: can occur at any time — airway management critical. "
            "Hypotension (first-dose effect): especially in volume-depleted patients. "
            "Hyperkalemia and renal impairment: monitor regularly. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Aliskiren: dual RAAS blockade — contraindicated in diabetes/renal impairment. "
            "Potassium-sparing diuretics/supplements: serious hyperkalemia. "
            "NSAIDs: reduce antihypertensive effect, worsen renal function. "
            "Lithium: ACE inhibitors increase lithium levels. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00584; RxNorm CUI 3827"
    },

    {
        "drug_name": "Telmisartan",
        "generic_name": "telmisartan",
        "disease": "Hypertension",
        "drug_class": "Angiotensin II Receptor Blocker (ARB)",
        "active_ingredient": "Telmisartan",
        "description": (
            "Telmisartan (Micardis) is an ARB with the longest half-life (~24 h) among ARBs, "
            "providing sustained 24-hour blood pressure control with once-daily dosing. "
            "It is also a partial PPARγ agonist, potentially benefiting insulin resistance. "
            "Preferred for patients with ACE inhibitor-induced cough. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Upper respiratory infection, back pain, sinusitis, diarrhea, dizziness, "
            "hyperkalemia, UTI. Rare: angioedema, hypotension, elevated liver enzymes. "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy; hypersensitivity to telmisartan; "
            "concomitant use with aliskiren in diabetic patients or renal impairment (eGFR < 60). "
            "(Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Fetal toxicity — discontinue immediately if pregnancy detected. "
            "Hypotension: volume/salt-depleted patients at risk. "
            "Renal function: may worsen renal impairment, especially with NSAIDs. "
            "Hyperkalemia. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Digoxin: telmisartan increases digoxin peak and trough levels — monitor digoxin. "
            "Lithium: increased lithium toxicity reported. "
            "Ramipril: dual ARB+ACE-I combination not recommended. "
            "NSAIDs: reduced efficacy and renal risk. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00966; RxNorm CUI 73494"
    },

    {
        "drug_name": "Hydrochlorothiazide",
        "generic_name": "hydrochlorothiazide",
        "disease": "Hypertension",
        "drug_class": "Thiazide Diuretic",
        "active_ingredient": "Hydrochlorothiazide",
        "description": (
            "Hydrochlorothiazide (HCTZ) is a thiazide diuretic that inhibits sodium-chloride "
            "cotransporter in the distal convoluted tubule, increasing urinary excretion of "
            "sodium and water. Initial antihypertensive effect is from volume reduction; "
            "long-term effect involves vasodilation. Often used in combination regimens. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Hypokalemia, hyponatremia, hypomagnesemia, hyperuricemia, hyperglycemia, "
            "hyperlipidemia, photosensitivity, dizziness, headache, orthostatic hypotension, "
            "impotence. Rare: pancreatitis, agranulocytosis, severe cutaneous reactions. "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Anuria; hypersensitivity to hydrochlorothiazide or sulfonamides; "
            "renal decompensation. (Source: FDA label)"
        ),
        "warnings": (
            "Electrolyte imbalances: hypokalemia, hyponatremia — monitor electrolytes regularly. "
            "Glucose impairment: may worsen diabetes control. "
            "Hyperuricemia: can precipitate gout. "
            "Photosensitivity: squamous cell carcinoma risk with prolonged use (EMA warning). "
            "(Source: FDA DailyMed; EMA)"
        ),
        "major_interactions": (
            "Lithium: HCTZ increases lithium toxicity significantly. "
            "NSAIDs: reduce diuretic/antihypertensive effect. "
            "Antidiabetic agents: HCTZ may increase blood glucose. "
            "Corticosteroids: additive hypokalemia. "
            "Digoxin: hypokalemia from HCTZ increases digoxin toxicity. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00999; RxNorm CUI 5487"
    },

    {
        "drug_name": "Atenolol",
        "generic_name": "atenolol",
        "disease": "Hypertension",
        "drug_class": "Beta-1 Selective Adrenergic Blocker",
        "active_ingredient": "Atenolol",
        "description": (
            "Atenolol (Tenormin) is a cardioselective beta-1 adrenergic receptor blocker. "
            "It reduces cardiac output, heart rate, and blood pressure by blocking beta-1 "
            "receptors in the heart. Unlike non-selective beta-blockers, it has less effect "
            "on beta-2 receptors (bronchi, vasculature). Widely used in India. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Bradycardia, fatigue, dizziness, depression, cold extremities, sleep disturbances, "
            "impotence, dyspnea. In susceptible patients: bronchospasm. "
            "May mask tachycardia of hypoglycemia. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Sinus bradycardia; greater than first-degree heart block; "
            "cardiogenic shock; overt cardiac failure; hypersensitivity to atenolol. "
            "Caution in asthma/COPD despite cardioselectivity. (Source: FDA label)"
        ),
        "warnings": (
            "Do not abruptly discontinue: risk of severe angina exacerbation, MI, or arrhythmia — "
            "taper over 1–2 weeks. Masks hypoglycemia symptoms in diabetics. "
            "Peripheral arterial circulatory disorders may worsen. "
            "(Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Calcium channel blockers (verapamil, diltiazem): profound bradycardia/heart block. "
            "Clonidine: rebound hypertension if clonidine withdrawn while on beta-blocker. "
            "Insulin/oral antidiabetics: prolonged hypoglycemia, masks symptoms. "
            "NSAIDs: reduced antihypertensive effect. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00335; RxNorm CUI 1202"
    },

    {
        "drug_name": "Ramipril",
        "generic_name": "ramipril",
        "disease": "Hypertension",
        "drug_class": "ACE Inhibitor",
        "active_ingredient": "Ramipril",
        "description": (
            "Ramipril (Altace) is a prodrug ACE inhibitor converted to its active form ramiprilat. "
            "It has high tissue ACE affinity and long duration. Has proven cardiovascular protective "
            "effects in the HOPE trial — reduces MI, stroke, and cardiovascular death in high-risk "
            "patients. Widely prescribed in India. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Dry cough (10–15%), dizziness, headache, fatigue, hyperkalemia, "
            "elevated serum creatinine. Rare but serious: angioedema, hypotension, "
            "neutropenia, renal failure. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy; history of ACE inhibitor-associated angioedema; "
            "hereditary/idiopathic angioedema; concomitant aliskiren use in diabetes or "
            "eGFR < 60; concurrent sacubitril/valsartan (36 h washout required). "
            "(Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Fetal toxicity — discontinue if pregnancy detected. "
            "Angioedema: potentially life-threatening — higher incidence in Black patients. "
            "First-dose hypotension: especially in volume-depleted patients. "
            "Renal impairment and hyperkalemia: monitor. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Aliskiren: dual RAAS blockade contraindicated in diabetes/renal impairment. "
            "Potassium-sparing diuretics: serious hyperkalemia. "
            "NSAIDs: reduced antihypertensive effect and renal risk. "
            "Lithium: ACE inhibitors raise lithium levels. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00178; RxNorm CUI 35208"
    },

    {
        "drug_name": "Chlorthalidone",
        "generic_name": "chlorthalidone",
        "disease": "Hypertension",
        "drug_class": "Thiazide-like Diuretic",
        "active_ingredient": "Chlorthalidone",
        "description": (
            "Chlorthalidone (Hygroton) is a thiazide-like diuretic with a longer half-life "
            "(40–60 hours) than HCTZ, providing more sustained blood pressure control. "
            "Preferred over HCTZ by JNC guidelines and ALLHAT trial data for reducing "
            "cardiovascular events. Acts on the distal nephron to promote natriuresis. "
            "(Source: FDA label; JNC 8; DrugBank)"
        ),
        "side_effects": (
            "Hypokalemia, hyponatremia, hyperuricemia, hyperglycemia, elevated triglycerides, "
            "photosensitivity, orthostatic hypotension, muscle cramps, impotence. "
            "Rare: pancreatitis, aplastic anemia, severe skin reactions. "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Anuria; renal decompensation; hypersensitivity to chlorthalidone or sulfonamide-derived drugs. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Electrolyte imbalances: hypokalemia is the primary risk — supplement if needed. "
            "Glucose tolerance impairment: may worsen diabetes. "
            "Hyperuricemia: precipitate gout in susceptible patients. "
            "Photosensitivity reaction reported. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Lithium: increases lithium toxicity (reduced renal clearance). "
            "Digoxin: hypokalemia from chlorthalidone increases digoxin arrhythmia risk. "
            "NSAIDs: reduce diuretic and antihypertensive effects. "
            "Corticosteroids/amphotericin B: additive hypokalemia. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00310; RxNorm CUI 2409"
    },

    {
        "drug_name": "Carvedilol",
        "generic_name": "carvedilol",
        "disease": "Hypertension",
        "drug_class": "Non-selective Beta-blocker with Alpha-1 Blocking Activity",
        "active_ingredient": "Carvedilol",
        "description": (
            "Carvedilol (Coreg) is a non-cardioselective beta-adrenergic blocker with alpha-1 "
            "blocking properties, providing vasodilation in addition to reduced cardiac output. "
            "Used in hypertension, heart failure with reduced ejection fraction (HFrEF), and "
            "post-MI left ventricular dysfunction. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Dizziness, fatigue, hypotension, weight gain, bradycardia, diarrhea, edema, "
            "hyperglycemia (in diabetes), blurred vision. Rare: severe hepatocellular injury, "
            "thrombocytopenia. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Bronchial asthma or related bronchospastic conditions; "
            "second or third-degree AV block; sick sinus syndrome without pacemaker; "
            "decompensated cardiac failure; severe hepatic impairment; "
            "hypersensitivity to carvedilol. (Source: FDA label)"
        ),
        "warnings": (
            "Do not abruptly discontinue: gradually taper over 1–2 weeks. "
            "Mask hypoglycemia symptoms. Anesthesia: inform anesthesiologist. "
            "Deterioration of heart failure during initiation: start low, titrate slowly. "
            "Hepatotoxicity: rare but discontinue if signs emerge. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Verapamil/diltiazem: severe bradycardia and heart block — avoid combination. "
            "Digoxin: carvedilol increases digoxin levels ~15% — monitor. "
            "Insulin/oral antidiabetics: enhanced hypoglycemic effect, masked symptoms. "
            "CYP2D6 inhibitors (fluoxetine, paroxetine): increase carvedilol levels. "
            "(Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB02703; RxNorm CUI 20352"
    },

    {
        "drug_name": "Clonidine",
        "generic_name": "clonidine hydrochloride",
        "disease": "Hypertension",
        "drug_class": "Central Alpha-2 Adrenergic Agonist",
        "active_ingredient": "Clonidine Hydrochloride",
        "description": (
            "Clonidine (Catapres) stimulates alpha-2 adrenergic receptors in the brainstem, "
            "reducing sympathetic outflow to the heart and peripheral vasculature, lowering "
            "heart rate and blood pressure. Used in resistant hypertension, hypertensive urgency, "
            "and as an adjunct agent. (Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Dry mouth (most common), drowsiness, dizziness, constipation, sedation, "
            "headache, fatigue, rebound hypertension on abrupt discontinuation. "
            "Rare: AV block, liver function abnormalities, depression. "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Hypersensitivity to clonidine. "
            "Epidural formulation: contraindicated in patients with bleeding disorders "
            "or anticoagulant therapy (injection site risk). (Source: FDA label)"
        ),
        "warnings": (
            "CRITICAL — Rebound hypertension: abrupt withdrawal can cause rapid severe BP rise, "
            "nervousness, agitation — taper gradually. "
            "Sedation: impairs driving/operating machinery. "
            "Perioperative use: continue through surgery to avoid rebound. "
            "(Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Beta-blockers: abrupt clonidine withdrawal with concomitant beta-blocker causes "
            "severe rebound hypertension — must taper clonidine first, then beta-blocker. "
            "TCAs (tricyclic antidepressants): reduce antihypertensive effect. "
            "CNS depressants/alcohol: additive sedation. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00575; RxNorm CUI 2599"
    },

    # ─────────────────────────────────────────────────────────
    # ARTHRITIS  (10 drugs)
    # ─────────────────────────────────────────────────────────
    {
        "drug_name": "Ibuprofen",
        "generic_name": "ibuprofen",
        "disease": "Arthritis",
        "drug_class": "NSAID (Non-selective COX Inhibitor)",
        "active_ingredient": "Ibuprofen",
        "description": (
            "Ibuprofen is a propionic acid-derived NSAID that non-selectively inhibits "
            "cyclooxygenase-1 (COX-1) and COX-2 enzymes, reducing prostaglandin synthesis. "
            "Provides anti-inflammatory, analgesic, and antipyretic effects. "
            "Used for osteoarthritis, rheumatoid arthritis, and acute musculoskeletal pain. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Gastrointestinal: nausea, dyspepsia, abdominal pain, GI bleeding, peptic ulceration. "
            "Cardiovascular: increased risk of MI and stroke. Renal: fluid retention, "
            "edema, acute renal failure. Headache, dizziness, rash. "
            "Rare: hepatotoxicity, aseptic meningitis, serious skin reactions (SJS, TEN). "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Active GI bleeding or peptic ulcer disease; known hypersensitivity to ibuprofen "
            "or aspirin-exacerbated respiratory disease (NSAID/aspirin allergy); "
            "perioperative use in CABG surgery; severe renal or hepatic impairment; "
            "last trimester of pregnancy. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Cardiovascular thrombotic events (MI, stroke) — risk increases with "
            "dose and duration; contraindicated for CABG perioperative pain. "
            "GI risk: serious GI adverse events including bleeding, ulceration, perforation. "
            "Renal toxicity: renal papillary necrosis. Fetal toxicity (≥ 30 weeks). "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Aspirin: ibuprofen may interfere with aspirin's antiplatelet effect — "
            "take aspirin 2 h before ibuprofen. Warfarin: increased bleeding risk. "
            "ACE inhibitors/ARBs: reduced antihypertensive effect, acute renal failure risk. "
            "Lithium: NSAIDs increase lithium levels. Methotrexate: increases MTX toxicity. "
            "(Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB01050; RxNorm CUI 5640"
    },

    {
        "drug_name": "Diclofenac",
        "generic_name": "diclofenac sodium",
        "disease": "Arthritis",
        "drug_class": "NSAID (Phenylacetic Acid Derivative)",
        "active_ingredient": "Diclofenac Sodium",
        "description": (
            "Diclofenac (Voltaren) is an NSAID with preferential COX-2 inhibition at lower doses "
            "and additional inhibition of lipoxygenase and arachidonic acid release. "
            "Available as oral, topical gel, and injectable forms. "
            "Widely used in India for osteoarthritis, rheumatoid arthritis, and ankylosing spondylitis. "
            "(Source: FDA label; CDSCO approved)"
        ),
        "side_effects": (
            "GI: nausea, abdominal pain, dyspepsia, diarrhea, GI bleeding. "
            "Hepatotoxicity: elevations in liver enzymes (common), clinically important liver injury. "
            "Cardiovascular: increased MI/stroke risk. Renal: fluid retention, renal impairment. "
            "Rare: serious skin reactions (SJS, TEN, DRESS). (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Active GI bleeding/ulceration; NSAID/aspirin hypersensitivity/asthma triad; "
            "perioperative CABG; severe hepatic impairment; severe renal impairment (GFR < 15); "
            "last trimester of pregnancy; heart failure (oral forms). (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Cardiovascular thrombotic events (MI, stroke). "
            "Serious GI events. Hepatotoxicity: most symptomatic hepatic disease among NSAIDs — "
            "monitor LFTs. Renal toxicity. "
            "Topical diclofenac: still carries systemic cardiovascular/GI risk. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Warfarin/anticoagulants: increased bleeding risk — closely monitor INR. "
            "Methotrexate: diclofenac raises MTX levels, potentially fatal toxicity. "
            "Cyclosporine: increased nephrotoxicity. Digoxin: NSAIDs may raise digoxin levels. "
            "ACE inhibitors/ARBs: reduced efficacy and acute renal failure. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00586; RxNorm CUI 3355; CDSCO"
    },

    {
        "drug_name": "Naproxen",
        "generic_name": "naproxen sodium",
        "disease": "Arthritis",
        "drug_class": "NSAID (Propionic Acid Derivative)",
        "active_ingredient": "Naproxen Sodium",
        "description": (
            "Naproxen (Aleve, Naprosyn) is a propionic acid NSAID with a longer half-life "
            "(12–17 hours) allowing twice-daily dosing. It inhibits COX-1 and COX-2, reducing "
            "prostaglandin synthesis. Has a relatively more favorable cardiovascular profile "
            "among NSAIDs per PRECISION trial data. Used for OA, RA, and ankylosing spondylitis. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "GI: nausea, dyspepsia, abdominal pain, heartburn, GI bleeding. "
            "Fluid retention, edema, hypertension. Headache, dizziness. "
            "Tinnitus (high doses). Rare: hepatic abnormalities, renal papillary necrosis, "
            "serious skin reactions. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "NSAID/aspirin-exacerbated respiratory disease; active GI bleeding/peptic ulcer; "
            "perioperative CABG pain; severe renal or hepatic impairment; "
            "last trimester of pregnancy. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Cardiovascular thrombotic events (MI, stroke) and serious GI events "
            "including bleeding, ulceration, perforation. Fetal toxicity ≥ 30 weeks gestation. "
            "Renal toxicity with long-term use. Discontinue before surgery if possible. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Warfarin: increase bleeding risk — INR monitoring essential. "
            "ACE inhibitors/ARBs: reduced antihypertensive effect, renal impairment. "
            "Methotrexate: increased MTX plasma levels and toxicity. "
            "Probenecid: increases naproxen plasma levels. "
            "Lithium: NSAIDs raise lithium to toxic levels. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00788; RxNorm CUI 7052"
    },

    {
        "drug_name": "Methotrexate",
        "generic_name": "methotrexate",
        "disease": "Arthritis",
        "drug_class": "Disease-Modifying Antirheumatic Drug (DMARD) / Folate Antagonist",
        "active_ingredient": "Methotrexate",
        "description": (
            "Methotrexate (Rheumatrex, Trexall) is the anchor DMARD for rheumatoid arthritis. "
            "It inhibits dihydrofolate reductase, impairing purine and pyrimidine synthesis "
            "and reducing immune cell proliferation. At low weekly doses used in RA, "
            "anti-inflammatory effects may also involve adenosine pathway. Gold standard DMARD. "
            "(Source: FDA label; DrugBank; ACR Guidelines)"
        ),
        "side_effects": (
            "Nausea, vomiting, stomatitis, fatigue (common, reduced by folic acid supplementation). "
            "Hepatotoxicity: liver fibrosis/cirrhosis with cumulative doses. "
            "Pulmonary toxicity (methotrexate pneumonitis). Bone marrow suppression: "
            "pancytopenia, leukopenia. Teratogenicity. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy (Category X); breastfeeding; alcoholism or chronic liver disease; "
            "immunodeficiency syndromes; pre-existing blood dyscrasias; "
            "hypersensitivity to methotrexate; severe renal impairment (CrCl < 30 mL/min). "
            "(Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNINGS (multiple): Embryo-fetal toxicity; pulmonary toxicity; "
            "severe bone marrow suppression; severe GI toxicity; hepatotoxicity (fibrosis, cirrhosis); "
            "malignant lymphomas; tumor lysis syndrome; severe skin reactions; "
            "opportunistic infections. WEEKLY dosing — errors in daily dosing are fatal. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "NSAIDs (ibuprofen, diclofenac): reduce MTX renal clearance — potentially fatal "
            "toxicity; avoid or monitor closely. Trimethoprim/sulfamethoxazole: additive "
            "antifolate toxicity — avoid. Penicillins: reduce MTX clearance. "
            "Proton pump inhibitors: may increase MTX levels. "
            "Alcohol: increased hepatotoxicity. (Source: FDA label; RxNav; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00563; RxNorm CUI 7413; ACR RA Guidelines"
    },

    {
        "drug_name": "Hydroxychloroquine",
        "generic_name": "hydroxychloroquine sulfate",
        "disease": "Arthritis",
        "drug_class": "DMARD / Antimalarial",
        "active_ingredient": "Hydroxychloroquine Sulfate",
        "description": (
            "Hydroxychloroquine (Plaquenil) is an antimalarial DMARD used in rheumatoid arthritis "
            "and systemic lupus erythematosus. It accumulates in lysosomes, alters antigen "
            "processing and presentation, inhibits toll-like receptor signaling, and modulates "
            "cytokine production. Has favorable cardiovascular and metabolic side-effect profile. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Nausea, vomiting, diarrhea, abdominal cramps, headache, dizziness, skin rash. "
            "Ophthalmologic: retinal toxicity/maculopathy (irreversible with long-term use, "
            "dose-dependent). Rare: cardiomyopathy, QT prolongation, peripheral neuropathy, "
            "drug-induced lupus. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Known hypersensitivity to hydroxychloroquine or 4-aminoquinoline compounds; "
            "pre-existing macular disease or visual field changes attributed to HCQ. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "Retinopathy: most important long-term toxicity — irreversible macular damage. "
            "Baseline ophthalmic exam required; annual screening after 5 years (or earlier "
            "with risk factors). QT prolongation: risk with other QT-prolonging drugs. "
            "G6PD deficiency: hemolytic anemia risk. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "QT-prolonging drugs (azithromycin, fluoroquinolones, antiarrhythmics): additive "
            "QT prolongation — potentially fatal arrhythmia. "
            "Digoxin: hydroxychloroquine may increase digoxin levels. "
            "Antidiabetics: HCQ enhances hypoglycemic effect. "
            "Cyclosporine: HCQ increases cyclosporine levels. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB01611; RxNorm CUI 5521"
    },

    {
        "drug_name": "Celecoxib",
        "generic_name": "celecoxib",
        "disease": "Arthritis",
        "drug_class": "NSAID (Selective COX-2 Inhibitor)",
        "active_ingredient": "Celecoxib",
        "description": (
            "Celecoxib (Celebrex) is a selective COX-2 inhibitor that reduces prostaglandin "
            "synthesis with less COX-1 inhibition, resulting in fewer GI complications "
            "than non-selective NSAIDs. Used in osteoarthritis, rheumatoid arthritis, "
            "ankylosing spondylitis, and acute pain. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Abdominal pain, dyspepsia, diarrhea, nausea, headache, dizziness, "
            "fluid retention, hypertension, peripheral edema, upper respiratory infection. "
            "Rare: serious cardiovascular events (MI, stroke), serious GI events, "
            "serious skin reactions, hepatotoxicity. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Sulfonamide hypersensitivity (contains sulfonamide moiety); "
            "NSAID/aspirin-exacerbated respiratory disease; perioperative CABG pain; "
            "active GI bleeding; last trimester of pregnancy; severe hepatic impairment. "
            "(Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNING: Cardiovascular thrombotic events (MI, stroke) — "
            "risk increases with dose and duration; contraindicated for CABG perioperative pain. "
            "GI serious events still possible. Hepatotoxicity. Fetal toxicity ≥ 30 weeks. "
            "(Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Warfarin: celecoxib may increase anticoagulant effect — monitor INR. "
            "ACE inhibitors/ARBs: reduced antihypertensive effect. "
            "Lithium: celecoxib increases lithium levels ~17%. "
            "Fluconazole (CYP2C9 inhibitor): doubles celecoxib exposure — start at lowest dose. "
            "Methotrexate: NSAIDs increase MTX toxicity. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00482; RxNorm CUI 140587"
    },

    {
        "drug_name": "Sulfasalazine",
        "generic_name": "sulfasalazine",
        "disease": "Arthritis",
        "drug_class": "DMARD / Aminosalicylate",
        "active_ingredient": "Sulfasalazine",
        "description": (
            "Sulfasalazine (Azulfidine) is a DMARD composed of sulfapyridine linked to "
            "5-aminosalicylate. Used in rheumatoid arthritis, and first-line DMARD for "
            "ankylosing spondylitis peripheral arthritis. Mechanism includes inhibition of "
            "B cell activity and cytokine production. (Source: FDA label; ACR Guidelines)"
        ),
        "side_effects": (
            "Nausea, vomiting, anorexia, headache, dizziness, skin rash, oligospermia (reversible). "
            "Orange-yellow discoloration of urine/skin. Serious: agranulocytosis, aplastic anemia, "
            "hepatotoxicity, SJS/TEN, severe hypersensitivity reactions. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Hypersensitivity to sulfasalazine, salicylates, or sulfonamides; "
            "intestinal or urinary obstruction; porphyria; "
            "infants under 2 years (for IBD). (Source: FDA label)"
        ),
        "warnings": (
            "Blood dyscrasias: deaths reported from agranulocytosis — CBC monitoring required. "
            "Hepatic injury: liver function monitoring needed. "
            "Severe skin reactions (SJS/TEN): discontinue immediately. "
            "Oligospermia: occurs in men — reversible upon discontinuation. "
            "(Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Methotrexate: combined DMARD use can increase MTX-related toxicity — monitor CBC/LFTs. "
            "Digoxin: sulfasalazine reduces digoxin absorption by ~25%. "
            "Folic acid: sulfasalazine impairs folate absorption — supplement needed. "
            "Warfarin: may potentiate anticoagulant effect. (Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB00795; RxNorm CUI 9524"
    },

    {
        "drug_name": "Prednisolone",
        "generic_name": "prednisolone",
        "disease": "Arthritis",
        "drug_class": "Corticosteroid (Glucocorticoid)",
        "active_ingredient": "Prednisolone",
        "description": (
            "Prednisolone is an active metabolite of prednisone and a potent glucocorticoid. "
            "It suppresses inflammation through inhibition of phospholipase A2, reducing "
            "prostaglandin and leukotriene synthesis. Used as bridge therapy in RA and for "
            "acute arthritis flares. Widely used in India for various inflammatory conditions. "
            "(Source: FDA label; DrugBank; ICMR)"
        ),
        "side_effects": (
            "Short-term: insomnia, mood changes, increased appetite, hyperglycemia, hypertension. "
            "Long-term: Cushing's syndrome, osteoporosis, adrenal suppression, infections, "
            "cataracts, glaucoma, peptic ulceration, muscle weakness, growth suppression (pediatric). "
            "(Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Systemic fungal infections; known hypersensitivity to prednisolone. "
            "Relative: active GI bleeding, uncontrolled diabetes, active tuberculosis "
            "(give only with antitubercular cover). (Source: FDA label)"
        ),
        "warnings": (
            "Immunosuppression: increased risk of serious/fatal infections. "
            "Do not abruptly discontinue after long-term use — HPA axis suppression. "
            "Taper dose gradually. Osteoporosis: consider bisphosphonate prophylaxis "
            "for chronic use. Monitor blood glucose, BP, bone density. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "NSAIDs: additive GI ulcer/bleeding risk — add PPI prophylaxis. "
            "Antidiabetic agents: corticosteroids impair glucose control — dose adjustment needed. "
            "Live vaccines: contraindicated during immunosuppressive corticosteroid doses. "
            "CYP3A4 inducers (rifampin): reduce prednisolone efficacy. "
            "Warfarin: variable effects on INR — monitor. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB00860; RxNorm CUI 8638; ICMR"
    },

    {
        "drug_name": "Leflunomide",
        "generic_name": "leflunomide",
        "disease": "Arthritis",
        "drug_class": "DMARD / Pyrimidine Synthesis Inhibitor",
        "active_ingredient": "Leflunomide",
        "description": (
            "Leflunomide (Arava) is a DMARD that inhibits dihydroorotate dehydrogenase (DHODH), "
            "a mitochondrial enzyme essential for de novo pyrimidine synthesis in lymphocytes. "
            "This selectively reduces proliferating lymphocyte activity. "
            "Used as monotherapy or in combination with methotrexate for RA. "
            "(Source: FDA label; DrugBank; ACR Guidelines)"
        ),
        "side_effects": (
            "Diarrhea (most common), nausea, alopecia (reversible), rash, elevated ALT/AST, "
            "headache, hypertension. Serious: hepatotoxicity (including fatal liver failure), "
            "teratogenicity, bone marrow suppression, peripheral neuropathy, "
            "serious infections. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Pregnancy (Category X — highly teratogenic); breastfeeding; "
            "severe hepatic impairment; severe immunodeficiency; "
            "bone marrow dysplasia; serious active infections. "
            "Washout procedure required before pregnancy. (Source: FDA label)"
        ),
        "warnings": (
            "BOXED WARNINGS: Embryo-fetal toxicity (Category X) — two-year washout protocol with "
            "cholestyramine if pregnancy desired. Hepatotoxicity: fatal liver failure reported — "
            "monitor LFTs monthly for 6 months then every 6–8 weeks. "
            "Serious infections and malignancy risk. (Source: FDA DailyMed boxed warning)"
        ),
        "major_interactions": (
            "Methotrexate: combination increases hepatotoxicity risk significantly — monitor LFTs. "
            "Warfarin: leflunomide increases anticoagulant effect — monitor INR closely. "
            "Teriflunomide (active metabolite overlap): avoid combination. "
            "Cholestyramine/activated charcoal: used to accelerate drug elimination. "
            "(Source: FDA label; DrugBank)"
        ),
        "source": "FDA DailyMed; DrugBank DB01097; RxNorm CUI 161; ACR Guidelines"
    },

    {
        "drug_name": "Colchicine",
        "generic_name": "colchicine",
        "disease": "Arthritis",
        "drug_class": "Gout and Crystal Arthropathy Agent / Anti-inflammatory",
        "active_ingredient": "Colchicine",
        "description": (
            "Colchicine (Colcrys) is an alkaloid that disrupts microtubule polymerization, "
            "impairing neutrophil migration and activation at sites of crystal deposition. "
            "Used for acute gout arthritis treatment and prophylaxis, and "
            "familial Mediterranean fever. Also used in pericarditis. "
            "(Source: FDA label; DrugBank)"
        ),
        "side_effects": (
            "Diarrhea (most common, dose-limiting), nausea, vomiting, abdominal pain. "
            "Neuromuscular toxicity: myopathy, rhabdomyolysis (especially with statins/CsA). "
            "Bone marrow suppression: pancytopenia with overdose or in renal impairment. "
            "Alopecia with long-term use. (Source: FDA DailyMed; SIDER)"
        ),
        "contraindications": (
            "Concomitant use of P-glycoprotein or strong CYP3A4 inhibitors (cyclosporine, "
            "clarithromycin) in patients with renal or hepatic impairment — potentially fatal. "
            "Hypersensitivity to colchicine. (Source: FDA label)"
        ),
        "warnings": (
            "Fatal toxicity possible with overdose or drug-drug interactions. "
            "Myelosuppression: agranulocytosis, aplastic anemia can occur. "
            "Neuromuscular toxicity: proximal myopathy and neuropathy, especially in renal "
            "impairment or with statins — monitor CPK. (Source: FDA DailyMed)"
        ),
        "major_interactions": (
            "Strong CYP3A4 inhibitors (clarithromycin, ritonavir, ketoconazole): dramatically "
            "increase colchicine levels — potentially fatal; dose reduce or avoid. "
            "P-gp inhibitors (cyclosporine, ranolazine): increase colchicine exposure. "
            "Statins: additive myopathy/rhabdomyolysis risk — monitor CPK. "
            "Digoxin: colchicine may increase digoxin levels. (Source: FDA label; RxNav)"
        ),
        "source": "FDA DailyMed; DrugBank DB01394; RxNorm CUI 2683"
    },
]

# Build DataFrame
df = pd.DataFrame(records, columns=[
    "drug_name", "generic_name", "disease", "drug_class", "active_ingredient",
    "description", "side_effects", "contraindications", "warnings",
    "major_interactions", "source"
])

# Verify counts
print("=== DATASET SUMMARY ===")
print(df.groupby("disease").size())
print(f"\nTotal rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"\nNull check:\n{df.isnull().sum()}")

# Save
output_path = "english_master_dataset.csv"
df.to_csv(output_path, index=False, encoding="utf-8")
print(f"\nSaved to: {output_path}")
print("\nFirst row preview:")
print(df.iloc[0][["drug_name","disease","drug_class"]].to_string())