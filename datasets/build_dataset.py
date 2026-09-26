# -*- coding: utf-8 -*-
# Plain-language rewrite of the English master dataset.
# Structure preserved; only the prose fields are rewritten for a general audience.
# Every specific clinical fact (thresholds, named drugs, named risks) from the
# original is kept -- only the phrasing changes.

import csv
from pathlib import Path

ENGLISH = {
"metformin": {
  "description": "Metformin is usually the first medicine doctors try for type 2 diabetes. It works by telling the liver to release less sugar into the blood, and it helps the body's cells respond better to insulin so they take in more sugar from the blood. On its own, it's very unlikely to make your blood sugar drop too low. (Source: FDA label; ICMR Diabetes Guidelines 2018)",
  "side_effects": "Common: diarrhea, nausea, vomiting, gas, stomach discomfort, indigestion, headache, a metallic taste in the mouth. Taking it long-term can lower your vitamin B12 levels. Rare but serious: a dangerous buildup of acid in the blood called lactic acidosis. (Source: FDA DailyMed label; SIDER)",
  "contraindications": "Avoid if you have poor kidney function, are in diabetic ketoacidosis (a dangerous high-sugar emergency), or are allergic to metformin. You'll need to stop it for a short time before and after a scan that uses injected contrast dye. (Source: FDA label)",
  "warnings": "IMPORTANT: Metformin carries a rare but potentially fatal risk of lactic acidosis (a dangerous acid buildup in the blood). This risk is higher if you have kidney or liver problems, heart failure, drink alcohol, or are 65 or older. Your doctor will usually stop this medicine before surgery or a contrast dye scan. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Certain seizure/glaucoma medicines (topiramate, acetazolamide) raise the risk of lactic acidosis. Alcohol also raises this risk. Contrast dye used in scans requires pausing metformin for about 48 hours before and after. Cimetidine (an acid-reflux medicine) can raise metformin levels in your blood. (Source: RxNav/DrugBank DDI)",
},
"glipizide": {
  "description": "Glipizide helps a type 2 diabetic's pancreas release more insulin, which lowers blood sugar. It's usually added alongside diet and exercise changes. (Source: FDA label; DrugBank)",
  "side_effects": "Most common: blood sugar dropping too low (hypoglycemia). Also nausea, diarrhea, constipation, dizziness, headache, skin rash, sun sensitivity, weight gain. Rare: blood disorders, liver problems, low sodium levels. (Source: FDA DailyMed label; SIDER)",
  "contraindications": "Not for type 1 diabetes or diabetic ketoacidosis (a diabetes emergency). Avoid if allergic to glipizide or sulfa drugs, or if you have severe kidney or liver problems. Not recommended in pregnancy. (Source: FDA label)",
  "warnings": "The main risk is blood sugar dropping too low, which is more likely in elderly or frail patients, those with kidney/liver problems, irregular meals, hard exercise, or alcohol use. Some studies link this drug class to a higher risk of heart-related death. People with a G6PD enzyme deficiency can develop anemia from red blood cell breakdown. (Source: FDA DailyMed)",
  "major_interactions": "Antifungal medicines fluconazole and miconazole can push your blood sugar too low. So can NSAID painkillers, warfarin, and aspirin-type medicines. Beta-blockers (heart/BP medicines) can hide the warning signs of low blood sugar. Rifampin (an antibiotic) can make glipizide work less well. (Source: RxNav/DrugBank DDI)",
},
"glimepiride": {
  "description": "Glimepiride helps the pancreas release more insulin to lower blood sugar in type 2 diabetes. It carries a somewhat lower risk of blood sugar dropping too low compared with older similar drugs, and can be used alone or together with metformin or insulin. (Source: FDA label; DrugBank)",
  "side_effects": "Blood sugar dropping too low, dizziness, headache, nausea, weakness, weight gain, skin reactions (itching, redness, hives). Rare: drops in white blood cells or platelets, and anemia from red blood cell breakdown. (Source: FDA label; SIDER)",
  "contraindications": "Not for type 1 diabetes or diabetic ketoacidosis. Avoid if allergic to glimepiride or sulfa drugs, if you have severely reduced kidney function, or liver problems. (Source: FDA label)",
  "warnings": "Low blood sugar is the main risk, especially with skipped meals, kidney/liver problems, or in elderly patients. People with a G6PD enzyme deficiency can develop anemia. Some data links this drug class to a higher risk of heart-related death. (Source: FDA DailyMed)",
  "major_interactions": "Certain antifungal and cholesterol medicines (fluconazole, gemfibrozil) can raise glimepiride levels significantly. Blood-pressure medicines (ACE inhibitors) and aspirin-type medicines can push blood sugar lower. Steroids and water pills (thiazides) work against it, raising blood sugar. (Source: DrugBank; RxNav)",
},
"sitagliptin": {
  "description": "Sitagliptin (brand name Januvia) helps the body release more of its own insulin after meals and reduces a hormone that raises blood sugar — but only when blood sugar is actually high, so it rarely causes it to drop too low on its own. Used alone or added to other diabetes medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Common cold-like symptoms, sore throat, headache, urinary tract infections. Rare but serious: inflamed pancreas (pancreatitis), severe joint pain, a blistering skin reaction, or a serious allergic reaction. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if you've had a serious allergic reaction to sitagliptin. Use carefully if you've had pancreatitis before. Not for type 1 diabetes or diabetic ketoacidosis. (Source: FDA label)",
  "warnings": "Stop the medicine and contact your doctor right away if you develop signs of pancreatitis (severe stomach pain). Some patients report severe joint pain. Use cautiously if you already have heart failure. People with reduced kidney function need a lower dose. (Source: FDA DailyMed)",
  "major_interactions": "May slightly raise levels of digoxin (a heart medicine) — your doctor may want to monitor this. Combining with insulin or sulfonylurea diabetes drugs raises the risk of blood sugar dropping too low. No major interactions through liver enzyme pathways. (Source: FDA label; RxNav)",
},
"empagliflozin": {
  "description": "Empagliflozin (brand name Jardiance) works in the kidneys, making the body pass out extra sugar in urine instead of absorbing it back into the blood. It also has proven benefits for the heart and kidneys in people with type 2 diabetes. (Source: FDA label; DrugBank)",
  "side_effects": "Urinary tract infections, genital yeast infections, needing to urinate more often, cold-like symptoms, high cholesterol, nausea. Rare but serious: diabetic ketoacidosis (even with only mildly high blood sugar), a rare but severe genital infection called Fournier's gangrene, and a possible increased risk of lower-leg amputation. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with significantly reduced kidney function, dialysis patients, or those with a serious allergy to empagliflozin. Not for type 1 diabetes. (Source: FDA label)",
  "warnings": "Can trigger diabetic ketoacidosis even when blood sugar looks nearly normal — your doctor may pause it before surgery. Watch for sudden pain or swelling around the genitals or between the legs, which could signal the rare Fournier's gangrene infection — seek care immediately. Can cause dehydration/low blood pressure, especially with water pills or in older adults. Report any foot or leg wounds promptly. (Source: FDA DailyMed)",
  "major_interactions": "Combining with insulin or other insulin-boosting diabetes drugs raises the risk of blood sugar dropping too low — your dose may need adjusting. Water pills (diuretics) combined with this can increase dehydration and low blood pressure risk. The antibiotic rifampin and similar drugs may make it work less well. (Source: FDA label; DrugBank)",
},
"pioglitazone": {
  "description": "Pioglitazone (brand name Actos) makes the body's tissues and liver more sensitive to insulin, helping lower blood sugar without pushing the pancreas to release more insulin. (Source: FDA label; DrugBank)",
  "side_effects": "Weight gain, fluid swelling, cold-like symptoms, headache, sinus infection. Serious: fluid buildup that can worsen or trigger heart failure, bone fractures (especially in women), vision changes from fluid behind the eye, and a possible increased risk of bladder cancer with long-term use. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with moderate-to-severe heart failure, active or past bladder cancer, or a known allergy to pioglitazone. Not for type 1 diabetes. (Source: FDA label)",
  "warnings": "IMPORTANT: Can cause or worsen heart failure by causing fluid retention — watch for swelling, sudden weight gain, or shortness of breath. Do not use if you currently have bladder cancer. Women taking this long-term have a higher risk of bone fractures. Get regular eye checks, since it can affect vision. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Gemfibrozil (a cholesterol medicine) significantly raises pioglitazone levels — the dose is usually limited to 15 mg/day if combined. The antibiotic rifampin makes it less effective. Combining with insulin raises the risk of fluid retention and heart failure. (Source: FDA label; DrugBank)",
},
"insulin-glargine": {
  "description": "Insulin glargine (brand names Lantus, Basaglar) is a long-acting, man-made insulin. One injection under the skin lasts about 24 hours with a fairly steady effect, giving background blood-sugar control for both type 1 and type 2 diabetes. (Source: FDA label; DrugBank)",
  "side_effects": "Blood sugar dropping too low is the most common and most serious effect. Also injection-site reactions (pain, redness, swelling, or skin changes), weight gain, fluid swelling, low potassium levels, and allergic reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Don't use if you're allergic to insulin glargine or its ingredients, or if you're currently experiencing low blood sugar. Not for injection into a vein. (Source: FDA label)",
  "warnings": "Low blood sugar is the biggest risk and can be life-threatening if severe — know the warning signs (shakiness, sweating, confusion). Never mix this insulin with other insulins in the same syringe. If you're at risk of low potassium, your levels should be checked. Any change to your insulin routine should be made carefully and with medical guidance. (Source: FDA DailyMed)",
  "major_interactions": "Beta-blockers (heart/BP medicines) can hide the warning signs of low blood sugar and slow recovery from it. Certain blood pressure medicines, aspirin-type drugs, and some antidepressants can make insulin work more strongly, raising the risk of blood sugar dropping too low. Steroids, water pills, and some psychiatric medicines work against it, raising blood sugar. (Source: FDA label; RxNav)",
},
"dapagliflozin": {
  "description": "Dapagliflozin (brand names Farxiga/Forxiga) makes the kidneys release more sugar into the urine instead of reabsorbing it, lowering blood sugar. It's also approved to help certain types of heart failure and chronic kidney disease, even in people who don't have diabetes. (Source: FDA label; DrugBank)",
  "side_effects": "Genital yeast infections (more common in women), urinary tract infections, cold-like symptoms, back pain, needing to urinate more often, nausea, high cholesterol. Rare: diabetic ketoacidosis, the rare severe genital infection Fournier's gangrene, and severe urinary infections. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with severely reduced kidney function, end-stage kidney disease, dialysis patients, or type 1 diabetes (for blood-sugar use). Avoid if allergic to dapagliflozin. (Source: FDA label)",
  "warnings": "Can trigger diabetic ketoacidosis even when blood sugar looks close to normal. Can cause dehydration or low blood pressure, especially in older adults or those on water pills. Seek immediate care for sudden pain, swelling, or redness around the genitals, which could be the rare but serious Fournier's gangrene infection. Report any signs of a severe urinary infection (fever, back pain). (Source: FDA DailyMed)",
  "major_interactions": "Combining with insulin or sulfonylurea diabetes drugs raises the risk of blood sugar dropping too low. Water pills combined with this can worsen dehydration. Certain other medicines (like mefenamic acid, a painkiller) may raise dapagliflozin levels. (Source: FDA label; DrugBank)",
},
"vildagliptin": {
  "description": "Vildagliptin (brand name Galvus) is a commonly used diabetes medicine in India and Europe that helps the body release more of its own insulin after meals and lowers a hormone that raises blood sugar, without pushing blood sugar too low on its own. Often added on top of metformin. (Source: DrugBank; CDSCO)",
  "side_effects": "Cold-like symptoms, headache, dizziness, fluid swelling, nausea. Can raise liver enzyme levels, so liver function needs monitoring. Rare: inflamed pancreas, severe skin reactions, upper respiratory infections. (Source: DrugBank; EMA label)",
  "contraindications": "Not for people with significant liver problems, severe kidney impairment (unless the dose is adjusted), a known allergy to vildagliptin, type 1 diabetes, or diabetic ketoacidosis. (Source: EMA label; DrugBank)",
  "warnings": "Your doctor should check your liver function before starting and periodically during treatment, and stop the medicine if liver problems develop. Contact your doctor if you develop severe stomach pain, which could signal pancreatitis. (Source: EMA SmPC; DrugBank DB04876)",
  "major_interactions": "Combining with insulin or sulfonylurea diabetes drugs may need a lower dose of those drugs to avoid blood sugar dropping too low. ACE inhibitor blood-pressure medicines have been linked to a higher risk of swelling reactions (angioedema) when combined. No major liver-enzyme-based drug interactions. (Source: DrugBank; EMA label)",
},
"acarbose": {
  "description": "Acarbose (brand names Glucobay, Precose) slows down how quickly the gut breaks down and absorbs carbohydrates from food, which reduces how much blood sugar rises after meals. This can be especially useful with the high-carbohydrate diets common in India. (Source: FDA label; ICMR Diabetes Guidelines)",
  "side_effects": "Very common: gas, stomach pain, diarrhea, and bloating — these are related to the dose and usually ease over time. Rare: raised liver enzymes, liver problems with high doses, bowel blockage. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with inflammatory bowel disease, bowel ulcers, partial bowel blockage, chronic digestive disorders, cirrhosis, significantly reduced kidney function, or type 1 diabetes. (Source: FDA label)",
  "warnings": "To reduce stomach side effects, doctors usually start at a low dose (25 mg) and increase it slowly. If your blood sugar drops too low while on this medicine combined with insulin or a sulfonylurea, you must treat it with pure glucose, not regular table sugar, since acarbose blocks the enzyme that breaks down table sugar. Liver enzymes should be checked periodically. (Source: FDA DailyMed)",
  "major_interactions": "Digestive enzyme supplements (like amylase or pancreatin) make acarbose less effective — avoid combining them. Activated charcoal also reduces its effect. It may lower the absorption of digoxin (a heart medicine). (Source: FDA label; DrugBank)",
},
"amlodipine": {
  "description": "Amlodipine (brand name Norvasc) relaxes and widens blood vessels by blocking calcium from entering the muscle cells in vessel walls, which lowers blood pressure. It's also used for chest pain (angina) and is one of the most commonly prescribed first-choice blood pressure medicines in India. (Source: FDA label; ICMR Hypertension Guidelines)",
  "side_effects": "Most common: swelling in the ankles/feet, flushing, headache, dizziness, a racing heartbeat, tiredness, drowsiness, nausea. Rare: gum swelling, liver problems, a significant drop in blood pressure. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if you're allergic to amlodipine or similar calcium-channel blockers. Use with caution if you have severe narrowing of the aortic heart valve. (Source: FDA label)",
  "warnings": "Blood pressure can drop too much, especially if you have severe aortic valve narrowing. Chest pain or a heart attack can occasionally worsen right when starting this type of medicine, particularly in people with significant blocked heart arteries. Ankle swelling may require a dose change. (Source: FDA DailyMed)",
  "major_interactions": "Certain antifungal and antibiotic medicines (ketoconazole, ritonavir, clarithromycin) can raise amlodipine levels significantly — blood pressure should be monitored. Rifampin (an antibiotic) makes it less effective. If you take simvastatin (a cholesterol medicine), your dose should be limited to 20 mg/day. Levels of cyclosporine and tacrolimus (organ transplant medicines) may rise. (Source: FDA label; RxNav)",
},
"losartan": {
  "description": "Losartan (brand name Cozaar) blocks the action of a hormone (angiotensin II) that narrows blood vessels and raises blood pressure. It also helps protect the kidneys in people with diabetes-related kidney damage, and is often chosen for people who develop a dry cough on ACE-inhibitor blood pressure medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Dizziness, cold-like symptoms, stuffy nose, back pain, tiredness, high potassium levels, and a rise in a kidney blood marker (creatinine). Rare: a swelling allergic reaction (angioedema, less common than with ACE inhibitors), low blood pressure, kidney problems. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Do not use during pregnancy at any stage — it can seriously harm the baby. Avoid combining with aliskiren (another blood pressure medicine) if you have diabetes or reduced kidney function. Avoid if allergic to losartan. (Source: FDA label)",
  "warnings": "IMPORTANT: Can seriously harm an unborn baby — stop immediately and tell your doctor if you become pregnant. Can cause low blood pressure if you're dehydrated or on a low-salt diet. Kidney function and potassium levels should be checked periodically, especially if you also take NSAID painkillers. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Combining with aliskiren is not recommended if you have diabetes or kidney problems. Potassium supplements or potassium-sparing water pills can push potassium too high. NSAID painkillers reduce its blood-pressure-lowering effect and can strain the kidneys. It can raise lithium levels to a toxic degree. (Source: FDA label; RxNav)",
},
"enalapril": {
  "description": "Enalapril (brand name Vasotec) is converted by the liver into its active form, which blocks an enzyme (ACE) involved in narrowing blood vessels. This relaxes blood vessels and lowers blood pressure, and it's also used for heart failure. (Source: FDA label; DrugBank)",
  "side_effects": "A dry, persistent cough is very common (about 1 in 5 to 1 in 10 people). Also dizziness, headache, tiredness, high potassium, and a rise in kidney blood markers. Rare but serious: a swelling allergic reaction (angioedema) that can be life-threatening, and low white blood cell counts in people with kidney problems. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid during pregnancy. Do not use if you've ever had swelling reactions (angioedema) from an ACE-inhibitor medicine, or a hereditary swelling condition. Avoid combining with aliskiren if you have diabetes or kidney problems, and don't combine with sacubitril/valsartan without a 36-hour gap between them. (Source: FDA label)",
  "warnings": "IMPORTANT: Can seriously harm an unborn baby — stop immediately if you become pregnant. Watch for sudden swelling of the face, lips, tongue, or throat (angioedema), which needs emergency care. Blood pressure can drop noticeably after the first dose, especially if you're dehydrated. Kidney function and potassium should be checked regularly. (Source: FDA DailyMed)",
  "major_interactions": "Combining with aliskiren is not recommended in diabetes or kidney disease. Potassium-sparing water pills or potassium supplements can raise potassium to dangerous levels. NSAID painkillers reduce its effect and can strain the kidneys. It can raise lithium levels. (Source: FDA label; RxNav)",
},
"telmisartan": {
  "description": "Telmisartan (brand name Micardis) blocks the hormone that narrows blood vessels, and lasts longer in the body than most similar drugs (about 24 hours), giving steady blood pressure control with one dose a day. It may also modestly help the body respond better to insulin, and is often used in people who cough on ACE-inhibitor medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Cold-like symptoms, back pain, sinus problems, diarrhea, dizziness, high potassium, urinary tract infections. Rare: swelling allergic reaction, low blood pressure, raised liver enzymes. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid during pregnancy. Avoid if allergic to telmisartan. Avoid combining with aliskiren if you have diabetes or reduced kidney function. (Source: FDA label)",
  "warnings": "IMPORTANT: Can seriously harm an unborn baby — stop immediately if you become pregnant. Blood pressure can drop if you're dehydrated or on a low-salt diet. Can worsen kidney function, especially combined with NSAID painkillers. Potassium levels should be monitored. (Source: FDA DailyMed)",
  "major_interactions": "Raises blood levels of digoxin (a heart medicine) — this needs monitoring. Can increase lithium toxicity. Combining with ramipril (another blood-pressure medicine acting on the same system) isn't recommended. NSAID painkillers reduce its effect and add kidney risk. (Source: FDA label; DrugBank)",
},
"hydrochlorothiazide": {
  "description": "Hydrochlorothiazide (often called HCTZ) is a water pill (diuretic) that makes the kidneys pass out more salt and water, which lowers blood pressure — first by reducing fluid volume, and over time by relaxing blood vessels. It's often combined with other blood pressure medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Can lower potassium, sodium, and magnesium levels, and raise uric acid, blood sugar, and cholesterol. Also sun sensitivity, dizziness, headache, lightheadedness on standing, and reduced sexual function. Rare: pancreas inflammation, blood disorders, severe skin reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people who produce no urine, are allergic to hydrochlorothiazide or sulfa drugs, or have significant kidney failure. (Source: FDA label)",
  "warnings": "Salt and mineral levels in the blood (especially potassium and sodium) should be checked regularly. Can make diabetes harder to control. Can trigger gout by raising uric acid. Long-term use raises the risk of skin cancer with excess sun exposure, so use sun protection. (Source: FDA DailyMed; EMA)",
  "major_interactions": "Significantly raises the risk of lithium toxicity if taken together. NSAID painkillers reduce its water-pill and blood-pressure effects. Can raise blood sugar, working against diabetes medicines. Steroids add to potassium loss. Low potassium from this medicine can make digoxin (a heart medicine) more likely to cause problems. (Source: FDA label; RxNav)",
},
"atenolol": {
  "description": "Atenolol (brand name Tenormin) is a beta-blocker that mainly targets receptors in the heart, slowing the heart rate and reducing how hard it pumps, which lowers blood pressure. It's widely used in India and has less effect on the lungs than older beta-blockers. (Source: FDA label; DrugBank)",
  "side_effects": "Slow heart rate, tiredness, dizziness, low mood, cold hands/feet, sleep problems, reduced sexual function, shortness of breath. In people prone to it, can trigger airway tightening (bronchospasm). Can hide the fast heartbeat that normally warns of low blood sugar. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with a very slow heart rate, significant heart block, cardiogenic shock, or overt heart failure. Avoid if allergic to atenolol. Use cautiously in asthma or COPD despite being more heart-selective than older beta-blockers. (Source: FDA label)",
  "warnings": "Do not stop this medicine suddenly — this can trigger worsening chest pain, a heart attack, or an abnormal heart rhythm; your doctor will taper it down over 1–2 weeks. In people with diabetes, it can hide the warning signs of low blood sugar. Can worsen poor circulation in the arms/legs. (Source: FDA DailyMed)",
  "major_interactions": "Combining with certain blood-pressure medicines (verapamil, diltiazem) can cause a dangerously slow heart rate or heart block. If you're also on clonidine, stopping it while still on this drug can cause a sharp rebound rise in blood pressure. Combined with insulin or diabetes tablets, it can prolong and hide low blood sugar. NSAID painkillers reduce its blood-pressure-lowering effect. (Source: FDA label; RxNav)",
},
"ramipril": {
  "description": "Ramipril (brand name Altace) is converted by the body into its active form, which blocks the ACE enzyme involved in narrowing blood vessels, lowering blood pressure. Large trials have shown it reduces heart attacks, strokes, and cardiovascular deaths in high-risk patients, and it's widely prescribed in India. (Source: FDA label; DrugBank)",
  "side_effects": "Dry cough (about 1 in 10), dizziness, headache, tiredness, high potassium, and rising kidney blood markers. Rare but serious: a swelling allergic reaction, low blood pressure, low white blood cell counts, kidney failure. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid during pregnancy. Do not use if you've had a swelling reaction to an ACE-inhibitor before, or a hereditary swelling condition. Avoid combining with aliskiren if you have diabetes or an eGFR (kidney function score) below 60. Avoid combining with sacubitril/valsartan without a 36-hour gap. (Source: FDA label)",
  "warnings": "IMPORTANT: Can seriously harm an unborn baby — stop immediately if you become pregnant. Watch for sudden swelling of the face, lips, tongue, or throat, which can be life-threatening and occurs more often in Black patients. Blood pressure can drop noticeably with the first dose, especially if dehydrated. Kidney function and potassium should be monitored. (Source: FDA DailyMed)",
  "major_interactions": "Combining with aliskiren is not recommended in diabetes or kidney disease. Potassium-sparing water pills can cause dangerously high potassium. NSAID painkillers reduce its effect and add kidney strain. It can raise lithium levels. (Source: FDA label; RxNav)",
},
"chlorthalidone": {
  "description": "Chlorthalidone (brand name Hygroton) is a water pill similar to hydrochlorothiazide but longer-acting (its effect lasts 40–60 hours), giving steadier blood pressure control. Large studies have favored it over HCTZ for reducing heart-related events. (Source: FDA label; JNC 8; DrugBank)",
  "side_effects": "Can lower potassium and sodium, raise uric acid and blood sugar, and raise triglycerides (a type of blood fat). Also sun sensitivity, lightheadedness on standing, muscle cramps, reduced sexual function. Rare: pancreas inflammation, severe blood or skin reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people who produce no urine, have significant kidney failure, or are allergic to chlorthalidone or sulfa-related drugs. (Source: FDA label)",
  "warnings": "Low potassium is the main risk — your doctor may recommend a supplement. Can make blood sugar control harder in diabetics. Can trigger gout attacks by raising uric acid. Watch for unusual sun sensitivity. (Source: FDA DailyMed)",
  "major_interactions": "Raises the risk of lithium toxicity. Low potassium caused by this medicine can make digoxin (a heart medicine) more likely to cause an irregular heartbeat. NSAID painkillers reduce its diuretic and blood-pressure effects. Steroids and amphotericin B add to potassium loss. (Source: FDA label; DrugBank)",
},
"carvedilol": {
  "description": "Carvedilol (brand name Coreg) is a beta-blocker that also relaxes blood vessels directly, giving it a dual blood-pressure-lowering effect. It's used for high blood pressure, heart failure with a weakened pumping heart, and after a heart attack. (Source: FDA label; DrugBank)",
  "side_effects": "Dizziness, tiredness, low blood pressure, weight gain, slow heart rate, diarrhea, swelling, higher blood sugar in diabetics, blurred vision. Rare: serious liver injury, low platelet counts. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Not for people with asthma or related breathing conditions, significant heart block without a pacemaker, sick sinus syndrome without a pacemaker, decompensated heart failure, severe liver problems, or an allergy to carvedilol. (Source: FDA label)",
  "warnings": "Do not stop suddenly — your doctor will taper the dose down over 1–2 weeks. Can hide the warning signs of low blood sugar. Tell your anesthesiologist you're taking this before any surgery. Heart failure can temporarily worsen when first starting this medicine, so doses are increased slowly. Stop if signs of liver problems appear. (Source: FDA DailyMed)",
  "major_interactions": "Combining with verapamil or diltiazem (other heart/BP medicines) can cause a dangerously slow heart rate — this combination is usually avoided. It raises digoxin levels by about 15%, so monitoring is needed. Combined with insulin or diabetes tablets, it can strengthen and hide low blood sugar. Certain antidepressants (fluoxetine, paroxetine) can raise carvedilol levels. (Source: FDA label; RxNav)",
},
"clonidine": {
  "description": "Clonidine (brand name Catapres) works in the brain to reduce nerve signals that raise heart rate and constrict blood vessels, lowering both. It's used for hard-to-control high blood pressure, sudden severe high blood pressure, and sometimes alongside other blood pressure medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Dry mouth is very common. Also drowsiness, dizziness, constipation, sedation, headache, tiredness, and a sharp rebound rise in blood pressure if stopped suddenly. Rare: heart rhythm changes, liver test changes, low mood. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if allergic to clonidine. The epidural (spinal injection) form should not be used in people with bleeding disorders or on blood thinners, due to injection-site bleeding risk. (Source: FDA label)",
  "warnings": "CRITICAL: Do not stop this medicine suddenly — doing so can cause a rapid, severe rise in blood pressure along with nervousness and agitation. It must be tapered off gradually. It can cause drowsiness, so be careful driving or operating machinery. If you're having surgery, this medicine is usually continued through the procedure to avoid a rebound spike. (Source: FDA DailyMed)",
  "major_interactions": "If you're on a beta-blocker and stop clonidine abruptly, this can cause a severe rebound rise in blood pressure — clonidine must be tapered off first, then the beta-blocker. Certain antidepressants (tricyclics) can reduce its blood-pressure-lowering effect. Alcohol and sedating medicines add to drowsiness. (Source: FDA label; RxNav)",
},
"ibuprofen": {
  "description": "Ibuprofen is a common pain and anti-inflammatory medicine (an NSAID) that reduces pain, fever, and swelling by blocking certain body chemicals (prostaglandins). Used for arthritis and general aches and pains. (Source: FDA label; DrugBank)",
  "side_effects": "Stomach-related: nausea, indigestion, stomach pain, and — with regular use — stomach bleeding or ulcers. Heart-related: a higher risk of heart attack and stroke with regular use. Kidney-related: fluid retention, swelling, and rarely sudden kidney injury. Also headache, dizziness, rash. Rare: liver problems, brain lining inflammation, severe skin reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if you currently have stomach bleeding or an ulcer, or if you're allergic to ibuprofen or aspirin-type medicines (including asthma triggered by these). Not to be used for pain right after heart bypass surgery. Avoid with significant kidney or liver problems, or in the last three months of pregnancy. (Source: FDA label)",
  "warnings": "IMPORTANT: Regular use raises the risk of heart attack and stroke, and this risk increases with higher doses and longer use — never use it around heart bypass surgery. Can cause serious stomach problems, including bleeding, ulcers, and (rarely) a hole in the stomach wall, sometimes without warning symptoms. Can harm the kidneys. Avoid in late pregnancy, as it can harm the baby. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "If you take low-dose aspirin to protect your heart, taking ibuprofen too close to it can block aspirin's protective effect — take aspirin at least 2 hours before ibuprofen. It increases bleeding risk with warfarin (a blood thinner). It can reduce the effect of blood pressure medicines (ACE inhibitors/ARBs) and stress the kidneys. It raises lithium levels. It significantly increases the toxicity risk of methotrexate. (Source: FDA label; RxNav)",
},
"diclofenac": {
  "description": "Diclofenac (brand name Voltaren) is a widely used NSAID pain and anti-inflammatory medicine, available as tablets, gel, or injection, commonly prescribed in India for arthritis. (Source: FDA label; CDSCO approved)",
  "side_effects": "Stomach-related: nausea, stomach pain, indigestion, diarrhea, and possible stomach bleeding. Liver-related: raised liver enzymes are common, and, less often, more serious liver injury. Heart-related: a higher risk of heart attack and stroke. Also fluid retention and kidney strain. Rare: severe skin reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid with active stomach bleeding or ulcers, an allergy to NSAIDs/aspirin (including NSAID-triggered asthma), right after heart bypass surgery, severe liver or kidney problems (specifically a GFR kidney score under 15), late pregnancy, or heart failure (for tablet forms). (Source: FDA label)",
  "warnings": "IMPORTANT: Raises the risk of heart attack and stroke. Can cause serious stomach bleeding or ulcers. Of the common NSAIDs, this one is more often linked to noticeable liver problems — your doctor may check liver function. Can strain the kidneys. Even the gel form carries some of the same heart and stomach risks as the tablets, just at a lower level. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Increases bleeding risk with warfarin and other blood thinners — INR blood tests should be monitored closely. Can raise methotrexate levels to a potentially dangerous degree. Increases kidney-related side effects of cyclosporine. May raise digoxin levels. Reduces the effectiveness of blood pressure medicines (ACE inhibitors/ARBs) and can trigger sudden kidney problems. (Source: FDA label; DrugBank)",
},
"naproxen": {
  "description": "Naproxen (brand names Aleve, Naprosyn) is a long-acting NSAID pain and anti-inflammatory medicine that lasts long enough for twice-daily dosing. Research suggests it may carry a somewhat lower heart risk than some other NSAIDs. Used for arthritis and related joint conditions. (Source: FDA label; DrugBank)",
  "side_effects": "Nausea, indigestion, stomach pain, heartburn, and possible stomach bleeding. Fluid retention, swelling, raised blood pressure. Headache, dizziness. Ringing in the ears at high doses. Rare: liver problems, kidney damage, severe skin reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if you have NSAID/aspirin-triggered asthma, active stomach bleeding or ulcers, right after heart bypass surgery, severe kidney or liver problems, or in late pregnancy. (Source: FDA label)",
  "warnings": "IMPORTANT: Can raise the risk of heart attack and stroke, and can cause serious stomach bleeding, ulcers, or a hole in the stomach wall. Can harm an unborn baby if taken in late pregnancy. Long-term use can damage the kidneys. Your doctor may want you to stop it before surgery if possible. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Increases bleeding risk with warfarin — INR should be monitored closely. Reduces the effect of blood pressure medicines (ACE inhibitors/ARBs) and can strain the kidneys. Raises methotrexate levels and toxicity risk. Probenecid (a gout medicine) raises naproxen levels. Can raise lithium to toxic levels. (Source: FDA label; RxNav)",
},
"methotrexate": {
  "description": "Methotrexate is the main long-term medicine used to control rheumatoid arthritis. It works by slowing down the immune system's overactive response that causes joint inflammation. It's taken once a week (not daily) and is considered the standard first choice for this condition. (Source: FDA label; DrugBank; ACR Guidelines)",
  "side_effects": "Common (often reduced by taking folic acid alongside it): nausea, vomiting, mouth sores, tiredness. Serious: liver scarring with long-term use, lung inflammation, and a drop in blood cell counts. Can cause serious birth defects if taken during pregnancy. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Never use during pregnancy or while breastfeeding. Avoid with alcohol dependence or ongoing liver disease, weakened immune systems, existing blood disorders, an allergy to methotrexate, or significantly reduced kidney function. (Source: FDA label)",
  "warnings": "IMPORTANT — MULTIPLE SERIOUS RISKS: this medicine can seriously harm an unborn baby; can cause lung damage; can severely lower blood cell counts; can cause serious stomach/gut problems; can damage the liver over time (scarring); has been linked to certain cancers; and can cause severe skin reactions and serious infections. CRITICAL: this is a WEEKLY medicine — accidentally taking it daily can be fatal. Always double-check your dosing schedule with your doctor or pharmacist. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "NSAID painkillers (ibuprofen, diclofenac) reduce how well the kidneys clear methotrexate, which can cause potentially fatal toxicity — this combination is usually avoided or closely monitored. Certain antibiotics (trimethoprim/sulfamethoxazole) add to its toxic effects and should be avoided. Penicillin-type antibiotics slow its clearance. Acid-reflux medicines (proton pump inhibitors) may raise its levels. Alcohol increases liver damage risk. (Source: FDA label; RxNav; DrugBank)",
},
"hydroxychloroquine": {
  "description": "Hydroxychloroquine (brand name Plaquenil) is originally an anti-malaria medicine that also calms an overactive immune system, and is used for rheumatoid arthritis and lupus. It tends to have a gentler effect on the heart and metabolism than many other arthritis medicines. (Source: FDA label; DrugBank)",
  "side_effects": "Nausea, vomiting, diarrhea, stomach cramps, headache, dizziness, skin rash. Eye-related: with long-term use, it can cause irreversible damage to the retina (the light-sensing part of the eye), which is dose-dependent. Rare: heart muscle problems, heart rhythm changes, nerve damage, drug-triggered lupus. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if allergic to hydroxychloroquine or related anti-malaria medicines, or if you already have retina (eye) disease or vision-field changes caused by this type of drug. (Source: FDA label)",
  "warnings": "The most important long-term risk is irreversible damage to the retina — you'll need an eye exam before starting, and yearly eye checks after 5 years of use (sooner if you have other risk factors). It can affect the heart's electrical rhythm, especially combined with other heart-rhythm-affecting medicines. People with a G6PD enzyme deficiency have a higher risk of anemia from red blood cell breakdown. (Source: FDA DailyMed)",
  "major_interactions": "Combining with other medicines that affect heart rhythm (certain antibiotics like azithromycin and fluoroquinolones, and anti-arrhythmia drugs) can add up to a dangerous, potentially fatal heart rhythm problem. It can raise digoxin (a heart medicine) levels. It can strengthen the blood-sugar-lowering effect of diabetes medicines. It can raise cyclosporine levels. (Source: FDA label; DrugBank)",
},
"celecoxib": {
  "description": "Celecoxib (brand name Celebrex) is an NSAID pain and anti-inflammatory medicine designed to be gentler on the stomach than older NSAIDs, while still relieving pain and swelling. Used for osteoarthritis, rheumatoid arthritis, ankylosing spondylitis, and short-term pain. (Source: FDA label; DrugBank)",
  "side_effects": "Stomach pain, indigestion, diarrhea, nausea, headache, dizziness, fluid swelling, raised blood pressure, cold-like symptoms. Rare but serious: heart attack, stroke, serious stomach problems, severe skin reactions, liver problems. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if you're allergic to sulfa-related medicines (this drug contains a sulfa-related component), have NSAID/aspirin-triggered asthma, are having pain relief right after heart bypass surgery, have active stomach bleeding, are in the last three months of pregnancy, or have severe liver problems. (Source: FDA label)",
  "warnings": "IMPORTANT: Raises the risk of heart attack and stroke, and this risk grows with higher doses and longer use — never use right after heart bypass surgery. Serious stomach problems (including bleeding) can still occur, even though it's gentler on the stomach than older NSAIDs. Can affect the liver. Avoid from 30 weeks of pregnancy onward, as it can harm the baby. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Can increase the blood-thinning effect of warfarin — INR should be monitored. Reduces the effectiveness of blood pressure medicines (ACE inhibitors/ARBs). Raises lithium levels by about 17%. Fluconazole (an antifungal medicine) roughly doubles celecoxib levels — a lower starting dose is used together. Raises methotrexate toxicity risk. (Source: FDA label; RxNav)",
},
"sulfasalazine": {
  "description": "Sulfasalazine (brand name Azulfidine) is used long-term to control rheumatoid arthritis and certain related joint conditions, working by calming an overactive immune response. (Source: FDA label; ACR Guidelines)",
  "side_effects": "Nausea, vomiting, loss of appetite, headache, dizziness, skin rash, and a temporary, harmless drop in sperm count that reverses after stopping. It can turn urine and skin an orange-yellow color, which is harmless. Serious: severe drops in blood cell counts, liver problems, severe skin reactions, and serious allergic reactions. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid if allergic to sulfasalazine, aspirin-type medicines, or sulfa drugs, or if you have a bowel or urinary blockage, the blood disorder porphyria, or (for bowel disease use) are an infant under 2. (Source: FDA label)",
  "warnings": "This medicine can, rarely, cause severe and sometimes fatal drops in blood cell counts — regular blood tests are needed to catch this early. Liver function should also be monitored. Stop immediately and seek care if you develop a severe skin reaction (blistering or peeling skin). Reduced sperm count in men reverses once the medicine is stopped. (Source: FDA DailyMed)",
  "major_interactions": "Combined with methotrexate (another arthritis medicine), the risk of side effects from both increases — regular blood and liver tests are needed. It reduces absorption of digoxin (a heart medicine) by about 25%. It blocks absorption of folic acid, so a folic acid supplement is usually needed. It can strengthen the effect of blood thinners like warfarin. (Source: FDA label; DrugBank)",
},
"prednisolone": {
  "description": "Prednisolone is a strong steroid medicine that quickly calms inflammation throughout the body. It's often used as a short-term \"bridge\" while slower-acting arthritis medicines start working, or for sudden flare-ups, and is widely used in India for many inflammatory conditions. (Source: FDA label; DrugBank; ICMR)",
  "side_effects": "Short-term: trouble sleeping, mood changes, increased appetite, raised blood sugar, raised blood pressure. Long-term: a rounded \"moon face\" and weight changes (Cushing's syndrome), weakened bones, the body's own steroid production shutting down, higher infection risk, cataracts, glaucoma, stomach ulcers, muscle weakness, and slowed growth in children. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Avoid with active fungal infections throughout the body, or if allergic to prednisolone. Use cautiously with active stomach bleeding, poorly controlled diabetes, or active tuberculosis (only with TB treatment covering it at the same time). (Source: FDA label)",
  "warnings": "This medicine weakens the immune system, raising the risk of serious or even fatal infections. Never stop it suddenly after taking it for a while — your body's own steroid production needs time to recover, so your doctor will taper the dose down gradually. Long-term use weakens bones, so your doctor may recommend a bone-protecting medicine. Blood sugar, blood pressure, and bone health should be monitored regularly. (Source: FDA DailyMed)",
  "major_interactions": "Combined with NSAID painkillers, the risk of stomach ulcers and bleeding increases — a stomach-protecting medicine is often added. It works against diabetes medicines, raising blood sugar. Live vaccines should not be given while on immune-suppressing steroid doses. The antibiotic rifampin makes prednisolone less effective. It can cause unpredictable changes in warfarin's blood-thinning effect, so INR needs monitoring. (Source: FDA label; RxNav)",
},
"leflunomide": {
  "description": "Leflunomide (brand name Arava) calms the overactive immune cells that drive rheumatoid arthritis by blocking a process those cells need to multiply. Used alone or together with methotrexate. (Source: FDA label; DrugBank; ACR Guidelines)",
  "side_effects": "Most common: diarrhea. Also nausea, hair thinning (which reverses), rash, raised liver enzymes, headache, raised blood pressure. Serious: liver damage (including rare fatal liver failure), harm to an unborn baby, lowered blood cell counts, nerve damage in the hands/feet, and serious infections. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Never use during pregnancy — it can cause serious birth defects — or while breastfeeding. Avoid with severe liver problems, a severely weakened immune system, certain bone marrow conditions, or serious active infections. If you plan to become pregnant, a special \"washout\" procedure is needed first to clear the drug from your body. (Source: FDA label)",
  "warnings": "IMPORTANT: Can cause serious birth defects — women who might become pregnant need a two-year drug-clearing (\"washout\") procedure with another medicine (cholestyramine) if pregnancy is planned sooner. Can cause serious, sometimes fatal, liver damage — liver blood tests are checked monthly for the first 6 months, then every 6–8 weeks. Also raises the risk of serious infections and certain cancers. (Source: FDA DailyMed boxed warning)",
  "major_interactions": "Combining with methotrexate significantly raises the risk of liver damage — liver tests need close monitoring. It increases the blood-thinning effect of warfarin — INR should be watched closely. It should not be combined with teriflunomide (a related medicine). Cholestyramine or activated charcoal can be used to help clear the drug from the body faster if needed. (Source: FDA label; DrugBank)",
},
"colchicine": {
  "description": "Colchicine (brand name Colcrys) calms the intense inflammation of a gout attack by stopping certain white blood cells from rushing to the site of crystal buildup in joints. Used to treat and prevent gout attacks, for a rare inherited fever condition, and sometimes for inflammation around the heart. (Source: FDA label; DrugBank)",
  "side_effects": "Diarrhea is common and often the sign to reduce the dose. Also nausea, vomiting, stomach pain. Can cause muscle damage (especially combined with certain cholesterol medicines or cyclosporine). Can suppress bone marrow, causing very low blood cell counts if overdosed or with kidney problems. Long-term use can cause hair thinning. (Source: FDA DailyMed; SIDER)",
  "contraindications": "Do not combine with certain strong antibiotics or antifungals (like cyclosporine or clarithromycin) if you also have kidney or liver problems — this combination can be fatal. Avoid if allergic to colchicine. (Source: FDA label)",
  "warnings": "Taking too much, or combining it with certain other medicines, can be fatal. It can severely suppress bone marrow, causing dangerously low blood cell counts. It can also damage muscles (causing pain, weakness, or muscle breakdown), especially in people with kidney problems or those also taking statins — muscle-related blood tests may be checked. (Source: FDA DailyMed)",
  "major_interactions": "Certain strong antibiotics and antifungals (clarithromycin, ketoconazole) and the HIV medicine ritonavir dramatically raise colchicine levels, which can be fatal — the dose is usually reduced or the combination avoided. Cyclosporine and ranolazine also raise colchicine levels. Cholesterol medicines called statins add to the risk of muscle damage. It can raise digoxin levels. (Source: FDA label; RxNav)",
},
}

def build_english_csv(input_path, output_path):
    with open(input_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Map drug_name (lowercase, hyphenated) to our dict keys
    def key_for(row):
        name = row['drug_name'].strip().lower().replace(' ', '-')
        return name

    missing = []
    for row in rows:
        k = key_for(row)
        if k not in ENGLISH:
            missing.append(k)
            continue
        for field in ['description', 'side_effects', 'contraindications', 'warnings', 'major_interactions']:
            row[field] = ENGLISH[k][field]

    if missing:
        print("MISSING KEYS (not rewritten, left as-is):", missing)

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")

if __name__ == '__main__':
    dataset_path = Path(__file__).resolve().parent / 'english_master_dataset.csv'
    build_english_csv(
        dataset_path,
        dataset_path
    )