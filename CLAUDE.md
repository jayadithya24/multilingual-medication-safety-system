# CLAUDE.md
# AI-Powered Multilingual Voice-Assisted Medication Information and Safety Monitoring System
# Project Bible for Claude Code

---

## WHAT THIS PROJECT ACTUALLY IS

A **mobile + web application** that lets users (patients, doctors, researchers) identify
medications and check drug safety information in **three languages: English, Kannada, Tulu**.

Users can:
1. **Take a photo of a medicine strip / prescription** → system reads it via OCR → returns drug info
2. **Speak a drug name or question** → system converts speech to text → returns drug info
3. **Type a drug name** → system searches and returns drug info

The system then:
- Shows what the drug is, what disease it treats, dosage, side effects, contraindications, warnings
- Checks if two or more drugs interact dangerously
- Classifies interaction severity (Mild / Moderate / Severe)
- Returns everything in the user's chosen language (English / Kannada / Tulu)
- Speaks the result back via Text-to-Speech

**The knowledge base is a Neo4j graph database** storing drugs, diseases, side effects,
and interactions as a connected graph — not flat tables.

---

## PROJECT SCOPE (DO NOT EXPAND BEYOND THIS)

**Diseases covered — EXACTLY THESE THREE, NO MORE:**
- Type 2 Diabetes
- Hypertension (High Blood Pressure)
- Arthritis (Osteoarthritis + Rheumatoid Arthritis + Gout)

**WHY these 3 — say this to your panel:**
These 3 are the most prevalent NCDs in India AND they frequently co-occur in
the same elderly patient. A 68-year-old in coastal Karnataka commonly has all 3
simultaneously — taking Metformin (Diabetes) + Amlodipine (HTN) + Ibuprofen
(Arthritis). That combination creates real, dangerous polypharmacy risk:
  Metformin + Ibuprofen  = SEVERE   (lactic acidosis risk)
  Amlodipine + Ibuprofen = MODERATE (BP medication undermined by NSAID)
  Metformin + Amlodipine = MILD     (no significant interaction)
This co-occurrence scenario is your primary demo. No existing multilingual
tool handles this combination in Kannada or Tulu.

**Languages:**
- English
- Kannada (standard literary Kannada)
- Tulu (genuine Tulu vocabulary written in Kannada script — NOT translated Kannada)

**Drugs:** 30 total (10 per disease). See datasets/english_master_dataset.csv.

**DO NOT add diseases beyond these 3.**
**DO NOT add drugs outside these 3 disease areas.**
**DO NOT add a 4th language.**
Scalability answer: The pipeline supports adding new diseases — we chose depth over breadth.

**User roles (3 roles — Researcher merged into Doctor):**
- Patient → upload prescription, voice/text search, view basic drug info, view safety alerts
- Doctor → everything Patient can, PLUS: check drug interactions, verify interactions, compare medicines, view full clinical side effect detail, explore drug relationships (graph view), analyze drug network, view reports, export data
- Administrator → manage drug database, users, datasets

**WHY Researcher = Doctor:**
The original report called the advanced user "Researcher" as an academic label.
Doctor end-user feedback confirmed doctors are the ones who need advanced drug
analysis (interaction checking, graph exploration, drug comparison) — not
academic researchers. Merging these two roles simplifies the system and
accurately reflects real-world usage.

**IMPORTANT:** Patients do NOT check drug interactions directly.
That is a Doctor-only feature. Confirmed by doctor end-user feedback.

---

## TECH STACK

### Frontend
- **Flutter** (mobile app — iOS + Android)
- React.js mentioned in diagrams but Flutter is primary

### Backend
- **FastAPI** (Python) — main API server, runs on Uvicorn
- Handles: auth, OCR, speech, drug queries, interaction engine, multilingual response

### Databases
- **Neo4j Aura** — graph database for drugs, diseases, side effects, interactions
- **MongoDB** — user data, prescription upload history, session data

### AI / Processing Components
- **OCR:** PaddleOCR — extracts drug names from prescription images
- **Speech-to-Text:** Whisper (OpenAI, runs locally) or Vosk (offline)
- **Text-to-Speech:** gTTS or pyttsx3
- **Translation/Multilingual:** custom — using pre-built Kannada/Tulu datasets (no live translation API needed for core data)
- **NLP:** spaCy or simple regex for entity extraction from OCR/STT output

### Infrastructure
- Nginx (serves React static files if web version needed)
- File storage for prescription images and datasets

---

## FOLDER STRUCTURE (USE THIS EXACTLY)

```
project-root/
│
├── CLAUDE.md                          ← this file
│
├── datasets/                          ← Shreyas's data pipeline (COMPLETE)
│   ├── build_dataset.py               ← generates english_master_dataset.csv
│   ├── split_master_dataset.py        ← splits master into 3 Neo4j-ready CSVs
│   ├── build_kannada_dataset.py       ← Kannada master dataset
│   ├── build_tulu_dataset.py          ← Tulu master dataset (genuine Tulu vocab)
│   ├── english_master_dataset.csv     ← 30 drugs, 11 columns (GENERATED)
│   ├── kannada_master_dataset.csv     ← 30 drugs in Kannada (GENERATED)
│   ├── tulu_master_dataset.csv        ← 30 drugs in Tulu (GENERATED)
│   ├── drug_disease.csv               ← drug_id, drug_name, disease_id, disease
│   ├── drug_sideeffects.csv           ← drug_id, drug_name, side_effect
│   └── drug_interactions.csv          ← drug1_id, drug1, drug2_id, drug2, drug2_in_scope, severity
│
├── neo4j/                             ← Knowledge graph setup
│   ├── schema.cypher                  ← Node/relationship constraints and indexes
│   ├── load_data.py                   ← Loads CSVs into Neo4j Aura
│   └── queries.cypher                 ← All Cypher query templates
│
├── backend/                           ← FastAPI application
│   ├── main.py                        ← FastAPI app entry point
│   ├── requirements.txt
│   ├── config.py                      ← env vars, DB connections
│   ├── routers/
│   │   ├── auth.py                    ← login, register, JWT
│   │   ├── drugs.py                   ← drug search, info retrieval
│   │   ├── interactions.py            ← drug interaction checking
│   │   ├── ocr.py                     ← image upload + PaddleOCR
│   │   ├── speech.py                  ← audio upload + Whisper STT
│   │   └── research.py                ← researcher endpoints
│   ├── services/
│   │   ├── neo4j_service.py           ← Neo4j driver + all Cypher queries
│   │   ├── mongo_service.py           ← MongoDB operations
│   │   ├── ocr_service.py             ← PaddleOCR processing pipeline
│   │   ├── stt_service.py             ← Whisper/Vosk STT pipeline
│   │   ├── tts_service.py             ← Text-to-Speech
│   │   ├── interaction_engine.py      ← severity classification + disclaimer logic
│   │   └── language_service.py        ← returns data in correct language (EN/KN/Tulu)
│   └── models/
│       ├── drug.py                    ← Pydantic models
│       ├── user.py
│       └── interaction.py
│
├── frontend/                          ← Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── home_screen.dart
│   │   │   ├── search_screen.dart
│   │   │   ├── camera_screen.dart     ← prescription photo upload
│   │   │   ├── voice_screen.dart      ← voice query
│   │   │   ├── drug_detail_screen.dart
│   │   │   ├── interaction_screen.dart
│   │   │   └── login_screen.dart
│   │   ├── services/
│   │   │   ├── api_service.dart       ← all FastAPI calls
│   │   │   └── auth_service.dart
│   │   └── models/
│   │       ├── drug_model.dart
│   │       └── interaction_model.dart
│   └── pubspec.yaml
│
└── diagrams/                          ← UML / architecture diagrams
    └── UML_Diagrams.pptx
```

---

## DATABASE SCHEMA — NEO4J KNOWLEDGE GRAPH

### Nodes

```cypher
// Drug node
(:Drug {
  drug_id: "metformin",           // stable English slug — ALWAYS use this for MERGE
  drug_name: "Metformin",
  generic_name: "metformin hydrochloride",
  drug_class: "Biguanide",
  active_ingredient: "Metformin Hydrochloride",
  description_en: "...",
  description_kn: "...",
  description_tulu: "...",
  warnings_en: "...",
  warnings_kn: "...",
  warnings_tulu: "...",
  contraindications_en: "...",
  contraindications_kn: "...",
  contraindications_tulu: "...",
  source: "FDA DailyMed; DrugBank DB00331"
})

// Disease node
(:Disease {
  disease_id: "type-2-diabetes",
  disease_name: "Type 2 Diabetes",
  disease_name_kn: "ಟೈಪ್ 2 ಮಧುಮೇಹ",
  disease_name_tulu: "ಟೈಪ್ 2 ಮಧುಮೇಹ"
})

// SideEffect node
(:SideEffect {
  name: "Nausea",
  name_kn: "ವಾಕರಿಕೆ",
  name_tulu: "ತಿಕ್ಕಾಯಿ"
})

// Interaction node
(:Interaction {
  interaction_id: "metformin-ibuprofen",
  drug1_id: "metformin",
  drug2_id: "ibuprofen",
  severity: "Moderate",           // Mild / Moderate / Severe
  description: "...",
  disclaimer: "Consult your doctor before acting on this information.",
  drug2_in_scope: "yes"           // yes = drug2 is in our 30-drug set
})

// User node (MongoDB handles most user data, but Neo4j tracks research queries)
(:User {
  user_id: "...",
  role: "patient|doctor|researcher|admin"
})
```

### Relationships

```cypher
(:Drug)-[:TREATS]->(:Disease)
(:Drug)-[:HAS_SIDE_EFFECT]->(:SideEffect)
(:Drug)-[:INTERACTS_WITH {severity, description, disclaimer}]->(:Drug)
(:Drug)-[:CONTAINS]->(:ActiveIngredient)
(:Drug)-[:CONTRAINDICATED_FOR]->(:Disease)
```

### Critical Rules
- **ALWAYS `MERGE` on `drug_id`** — never on `drug_name` (case/spacing issues)
- **NEVER create duplicate nodes** — use MERGE not CREATE for all Drug/Disease nodes
- `drug2_in_scope = "yes"` means both drugs are in your 30-drug set (real graph edge)
- `drug2_in_scope = "no"` means drug2 is external (Alcohol, NSAIDs as class, etc.)

---

## API ENDPOINTS — COMPLETE LIST

### Auth
```
POST /auth/register          → create account (patient/doctor/researcher)
POST /auth/login             → returns JWT token
POST /auth/logout
```

### Drug Information
```
GET  /drugs/search?q={name}&lang={en|kn|tulu}
     → fuzzy search drug by name, returns drug info in requested language

GET  /drugs/{drug_id}?lang={en|kn|tulu}
     → full drug detail (description, side effects, warnings, contraindications)

GET  /drugs/disease/{disease_id}?lang={en|kn|tulu}
     → all drugs that treat a given disease

GET  /drugs/{drug_id}/side-effects?lang={en|kn|tulu}
     → list of side effects for a drug
```

### Interaction Engine (Doctor role only)
```
POST /interactions/check
     body: { drug_ids: ["metformin", "ibuprofen"], lang: "en" }
     → returns all interactions between the listed drugs, with severity + disclaimer

GET  /interactions/{drug_id}?lang={en|kn|tulu}
     → all known interactions for a single drug
```

### OCR (Image Input)
```
POST /ocr/extract
     body: multipart/form-data { image: <file> }
     → runs PaddleOCR, returns extracted drug names as list
     → then client calls /drugs/search for each name
```

### Speech (Voice Input)
```
POST /speech/transcribe
     body: multipart/form-data { audio: <file>, lang: "en|kn|tulu" }
     → runs Whisper STT, returns transcribed text
     → client uses text to call /drugs/search
```

### Text-to-Speech (Response)
```
POST /tts/speak
     body: { text: "...", lang: "en|kn|tulu" }
     → returns audio file (mp3) of spoken text
```

### Research (Researcher role only)
```
GET  /research/graph/explore?drug_id={id}
     → returns graph neighbourhood of a drug (N hops)

GET  /research/graph/network
     → returns full drug interaction network (for visualization)

GET  /research/export?format=csv|json
     → exports dataset
```

### Admin
```
POST /admin/drugs/add
POST /admin/drugs/update/{drug_id}
GET  /admin/users
POST /admin/datasets/reload         → re-runs Neo4j load from CSVs
```

---

## DATA PIPELINE — WHAT IS ALREADY BUILT (DO NOT REBUILD)

Shreyas has already completed this. Do not modify these files:

| File | Status | What it does |
|------|--------|--------------|
| `datasets/build_dataset.py` | ✅ COMPLETE | Generates english_master_dataset.csv (30 drugs, 11 cols) |
| `datasets/split_master_dataset.py` | ✅ COMPLETE | Splits into drug_disease, drug_sideeffects, drug_interactions CSVs with drug_id slugs and drug2_in_scope flags |
| `datasets/build_kannada_dataset.py` | ✅ COMPLETE | 30 drugs in standard literary Kannada |
| `datasets/build_tulu_dataset.py` | ✅ COMPLETE | 30 drugs in genuine Tulu vocabulary (Kannada script) |

**To regenerate datasets:**
```bash
cd datasets/
pip install pandas
python build_dataset.py
python split_master_dataset.py
python build_kannada_dataset.py
python build_tulu_dataset.py
```

---

## NEO4J LOAD SEQUENCE

When `load_data.py` runs, it must follow this exact order:

```
1. Create constraints and indexes (schema.cypher)
2. MERGE Disease nodes (from drug_disease.csv)
3. MERGE Drug nodes (from english_master_dataset.csv)
4. CREATE TREATS relationships (from drug_disease.csv)
5. CREATE HAS_SIDE_EFFECT relationships (from drug_sideeffects.csv)
6. MERGE Interaction nodes + INTERACTS_WITH relationships (from drug_interactions.csv, drug2_in_scope = "yes" only for graph edges)
7. Add multilingual properties to Drug nodes (from kannada_master_dataset.csv and tulu_master_dataset.csv — match on drug_id)
```

---

## INTERACTION ENGINE LOGIC

```python
# Severity classification (already implemented in split_master_dataset.py)
SEVERE_KEYWORDS = [
    "fatal", "contraindicated", "potentially fatal",
    "life-threatening", "avoid combination",
    "dramatically increase", "serious hyperkalemia"
]
MODERATE_KEYWORDS = [
    "monitor", "increase", "risk", "caution", "additive"
]

# Every interaction result MUST include:
{
    "drug1": "Metformin",
    "drug2": "Ibuprofen",
    "severity": "Severe",
    "description": "NSAIDs reduce MTX renal clearance...",
    "disclaimer": "Consult your doctor before acting on this information. This system supports decision-making and does not replace clinical judgment.",
    "drug2_in_scope": "yes"
}
```

---

## LANGUAGE SERVICE LOGIC

```python
# Drug info is stored in Neo4j with _en, _kn, _tulu suffixes
# Language service picks the right field

def get_drug_info(drug_id: str, lang: str):
    suffix = {"en": "_en", "kn": "_kn", "tulu": "_tulu"}.get(lang, "_en")
    # query Neo4j for drug_id, return fields with correct suffix
    # fallback to _en if _kn or _tulu field is empty

# Tulu is NOT a translation of Kannada
# Tulu has genuinely different vocabulary — stored separately
# e.g. nausea: Kannada = ವಾಕರಿಕೆ, Tulu = ತಿಕ್ಕಾಯಿ
# e.g. stomach pain: Kannada = ಹೊಟ್ಟೆ ನೋವು, Tulu = ಬೊಜ್ಜು ನೋವು
```

---

## KNOWN LIMITATIONS (ACKNOWLEDGE IN PRESENTATION)

1. **Severity is population-level, not personalized** — individual physiology varies.
   Addressed with disclaimer on every result.

2. **30 drugs only** — covers ~80-85% of routine outpatient cases (Diabetes, HTN,
   Arthritis) by design. Expanding requires running the same data pipeline.

3. **OCR accuracy** — prescription handwriting quality affects extraction. Post-processing
   with Levenshtein distance string matching mitigates this.

4. **No real-time drug database sync** — data is static from FDA/DrugBank sources.
   Dataset was compiled in 2025. New drugs or updated warnings require manual pipeline re-run.

5. **Tulu NLP** — no Tulu STT model exists. Voice input in Tulu uses the Kannada STT
   model as a fallback (Tulu is written in Kannada script). This is a documented limitation.

---

## WHAT EACH TEAM MEMBER DOES

| Member | Role | Responsibilities |
|--------|------|-----------------|
| **Shreyas Damle** | Data & Language Lead | Dataset pipeline ✅ COMPLETE, UML/system diagrams, Neo4j schema design, Cypher queries, multilingual data (EN/KN/Tulu) |
| **Jayadithya G Salian** | Backend Lead | FastAPI implementation, Neo4j integration, interaction engine, API endpoints |
| **Nidhi K** | Frontend Lead | Flutter app, all UI screens, API integration, language selector |
| **Vijayalakshmi Kannan** | AI/ML Lead | OCR (PaddleOCR), STT (Whisper/Vosk), TTS (gTTS), NLP entity extraction |

**Shreyas's completed deliverables (do not rebuild any of these):**
- english_master_dataset.csv — 30 drugs, 11 columns, FDA/DrugBank/ICMR sourced
- kannada_master_dataset.csv — same 30 drugs in standard literary Kannada
- tulu_master_dataset.csv — same 30 drugs in genuine Tulu vocabulary (Kannada script)
- drug_disease.csv — with drug_id slugs and disease_id slugs
- drug_sideeffects.csv — one side effect per row, drug_id keyed
- drug_interactions.csv — with severity, drug2_in_scope flag, parenthesis-aware parsing
- All 9 system diagrams (Use Case, Class, Sequence, Activity, Component, Deployment, System Architecture, DFD L0, DFD L1)
- This CLAUDE.md

---

## DO NOT DO THESE THINGS

- Do NOT rebuild the dataset scripts — they are complete and tested
- Do NOT use drug_name for Neo4j MERGE — always use drug_id (slug)
- Do NOT allow patients to access /interactions/check — Doctor role only
- Do NOT use a live translation API for core drug data — use the pre-built multilingual CSVs
- Do NOT add pediatric dosage logic — explicitly out of scope
- Do NOT claim the severity rating is clinically validated — always show disclaimer
- Do NOT mix Tulu and Kannada vocabulary — they are separate datasets for a reason

---

## IMPLEMENTATION PRIORITY ORDER

Build in this exact sequence. Each phase must be working before starting the next.

### Phase 1 — Neo4j Knowledge Graph (Week 1–2)
```
[ ] schema.cypher — constraints + indexes
[ ] load_data.py — load all 6 CSVs into Neo4j Aura
[ ] Verify graph in Neo4j Browser (node counts, relationship counts)
[ ] queries.cypher — all 8 query templates
[ ] Test all Cypher queries manually in Neo4j Browser
```

### Phase 2 — FastAPI Core (Week 2–3)
```
[ ] main.py + config.py setup
[ ] neo4j_service.py — driver + all query functions
[ ] /drugs/search endpoint (text search, returns EN first)
[ ] /drugs/{drug_id} endpoint
[ ] /interactions/check endpoint
[ ] Test all endpoints with Postman/curl
```

### Phase 3 — Auth + Language (Week 3)
```
[ ] auth.py — JWT login/register
[ ] mongo_service.py — user storage
[ ] language_service.py — EN/KN/Tulu field selection
[ ] Add lang= param to all drug endpoints
[ ] Role-based access (patient cannot hit /interactions/check)
```

### Phase 4 — OCR + Speech (Week 4)
```
[ ] ocr_service.py — PaddleOCR pipeline
[ ] /ocr/extract endpoint
[ ] stt_service.py — Whisper pipeline
[ ] /speech/transcribe endpoint
[ ] tts_service.py — gTTS pipeline
[ ] /tts/speak endpoint
```

### Phase 5 — Flutter Frontend (Week 4–5)
```
[ ] api_service.dart — all API calls
[ ] login_screen.dart
[ ] search_screen.dart (text search)
[ ] camera_screen.dart (OCR)
[ ] voice_screen.dart (STT)
[ ] drug_detail_screen.dart
[ ] interaction_screen.dart (Doctor only)
[ ] Language selector (EN / KN / Tulu)
```

### Phase 6 — Integration + Testing (Week 5–6)
```
[ ] End-to-end test: photo → OCR → drug search → result displayed
[ ] End-to-end test: voice → STT → drug search → TTS spoken result
[ ] End-to-end test: doctor checks interaction → severity + disclaimer shown
[ ] Test all three languages
[ ] Performance: response time < 3 seconds for all queries
```

---

## CYPHER QUERY TEMPLATES (IMPLEMENT THESE)

```cypher
// 1. Search drug by name (fuzzy)
MATCH (d:Drug)
WHERE toLower(d.drug_name) CONTAINS toLower($query)
   OR toLower(d.generic_name) CONTAINS toLower($query)
RETURN d LIMIT 10

// 2. Get full drug info
MATCH (d:Drug {drug_id: $drug_id})
OPTIONAL MATCH (d)-[:TREATS]->(dis:Disease)
OPTIONAL MATCH (d)-[:HAS_SIDE_EFFECT]->(se:SideEffect)
RETURN d, collect(dis) as diseases, collect(se) as side_effects

// 3. Check drug interactions (Doctor only)
MATCH (d1:Drug {drug_id: $drug1_id})-[r:INTERACTS_WITH]->(d2:Drug {drug_id: $drug2_id})
RETURN d1.drug_name, d2.drug_name, r.severity, r.description, r.disclaimer

// 4. All interactions for a drug
MATCH (d:Drug {drug_id: $drug_id})-[r:INTERACTS_WITH]->(d2:Drug)
RETURN d2.drug_name, r.severity, r.description, r.disclaimer
ORDER BY r.severity

// 5. All drugs for a disease
MATCH (d:Drug)-[:TREATS]->(dis:Disease {disease_id: $disease_id})
RETURN d.drug_id, d.drug_name, d.drug_class

// 6. Interaction severity lookup (multi-drug)
UNWIND $drug_ids AS drug_id
MATCH (d1:Drug {drug_id: drug_id})-[r:INTERACTS_WITH]->(d2:Drug)
WHERE d2.drug_id IN $drug_ids AND d1.drug_id < d2.drug_id
RETURN d1.drug_name, d2.drug_name, r.severity, r.description, r.disclaimer
ORDER BY
  CASE r.severity WHEN 'Severe' THEN 1 WHEN 'Moderate' THEN 2 ELSE 3 END

// 7. Drug contraindications
MATCH (d:Drug {drug_id: $drug_id})-[:CONTRAINDICATED_FOR]->(dis:Disease)
RETURN d.drug_name, collect(dis.disease_name)

// 8. Graph neighbourhood (Researcher)
MATCH (d:Drug {drug_id: $drug_id})-[r]-(connected)
RETURN d, r, connected LIMIT 50
```

---

## ENVIRONMENT VARIABLES (.env)

```
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/medication_db

SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

ENVIRONMENT=development
```

---

## QUICK REFERENCE — KEY NUMBERS FOR PRESENTATION

- **30 drugs** total (10 Type 2 Diabetes, 10 Hypertension, 10 Arthritis)
- **3 languages** (English, Kannada, Tulu)
- **11 columns** in master dataset
- **~320 side effect rows** after splitting
- **~157 interaction rows** after splitting
- **9 in-scope drug-drug interactions** (both drugs in our 30-drug set)
- **Drug IDs are English slugs** — consistent across all 3 language datasets
- **Data sources:** FDA DailyMed, DrugBank CC BY-NC 4.0, RxNorm, SIDER, ICMR, CDSCO
- **Response time target:** < 3 seconds for all queries
- **Severity levels:** Mild, Moderate, Severe (heuristic, not clinically validated)
- **Disclaimer on every interaction result** — system supports, not replaces, doctors

---

