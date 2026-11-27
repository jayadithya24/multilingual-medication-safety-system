const DATA_PATH = `${(import.meta.env?.BASE_URL || "/").replace(/\/?$/, "/")}demo-data/`;
const LANGUAGES = ["en", "kn", "tulu"];
const SAMPLE_PATIENT = {
  username: "demo.patient",
  patient_id: "DEMO-PT-001",
  full_name: "Sample Patient",
  age: 68,
  gender: "Female",
  medical_condition: "Type 2 Diabetes, Hypertension, Rheumatoid Arthritis",
};
const SAMPLE_DOCTOR = {
  username: "demo.doctor",
  full_name: "Demo Doctor",
  role: "doctor",
};
const SAMPLE_SCHEDULES = [
  {
    schedule_id: "DEMO-SCH-001",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Metformin",
    dosage: "500 mg",
    instructions: "Take with food",
    frequency: "Twice daily",
    scheduled_times: ["08:00", "20:00"],
    reminder_enabled: false,
    is_active: true,
    status: "active",
    disease: "Type 2 Diabetes Mellitus",
  },
  {
    schedule_id: "DEMO-SCH-002",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Amlodipine",
    dosage: "5 mg",
    instructions: "Sample schedule only",
    frequency: "Once daily",
    scheduled_times: ["09:00"],
    reminder_enabled: false,
    is_active: true,
    status: "active",
    disease: "Hypertension",
  },
  {
    schedule_id: "DEMO-SCH-003",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Methotrexate",
    dosage: "As prescribed",
    instructions: "Sample schedule only",
    frequency: "Once weekly",
    scheduled_times: ["10:00"],
    reminder_enabled: false,
    is_active: true,
    status: "active",
    disease: "Rheumatoid Arthritis",
  },
  {
    schedule_id: "DEMO-SCH-004",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Ibuprofen",
    dosage: "As prescribed",
    instructions: "Sample schedule only",
    frequency: "As needed",
    scheduled_times: [],
    reminder_enabled: false,
    is_active: true,
    status: "active",
    disease: "Arthritis",
  },
];
const SAMPLE_HISTORY = [
  {
    history_id: "DEMO-HIST-001",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Metformin",
    dosage: "500 mg",
    scheduled_time: "08:00",
    taken_at: "2026-03-16T08:03:00Z",
    status: "TAKEN",
  },
  {
    history_id: "DEMO-HIST-002",
    patient_username: SAMPLE_PATIENT.username,
    medicine_name: "Amlodipine",
    dosage: "5 mg",
    scheduled_time: "09:00",
    taken_at: "2026-03-16T09:05:00Z",
    status: "TAKEN",
  },
];
const SAMPLE_PATIENT_ACCESS = {
  patient_id: SAMPLE_PATIENT.patient_id,
  username: SAMPLE_PATIENT.username,
  full_name: SAMPLE_PATIENT.full_name,
  conditions: ["Type 2 Diabetes", "Hypertension", "Rheumatoid Arthritis"],
  status: "ACCEPTED",
  requestId: "DEMO-ACCESS-001",
};

let datasetPromise;

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const source = text.replace(/^\uFEFF/, "");

  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    if (quoted) {
      if (character === '"' && source[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"') {
      quoted = true;
    } else if (character === ",") {
      row.push(field);
      field = "";
    } else if (character === "\n") {
      row.push(field.replace(/\r$/, ""));
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }

  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    if (row.some((value) => value !== "")) rows.push(row);
  }

  const [headers = [], ...records] = rows;
  return records.map((values) => Object.fromEntries(
    headers.map((header, index) => [header, values[index] || ""]),
  ));
}

async function loadAsset(filename, format = "csv") {
  const response = await fetch(`${DATA_PATH}${filename}`);
  if (!response.ok) {
    throw new Error(`Could not load static demo data: ${filename} (${response.status}).`);
  }
  return format === "json" ? response.json() : parseCsv(await response.text());
}

async function loadDemoData() {
  if (!datasetPromise) {
    datasetPromise = Promise.all([
      loadAsset("english_master_dataset.csv"),
      loadAsset("kannada_master_dataset.csv"),
      loadAsset("tulu_master_dataset.csv"),
      loadAsset("drug_disease.csv"),
      loadAsset("drug_sideeffects.csv"),
      loadAsset("drug_interactions.csv"),
      loadAsset("interaction_evidence.json", "json"),
    ]).then(([english, kannada, tulu, diseases, sideEffects, interactions, evidence]) => {
      const data = {
        english,
        languages: { en: english, kn: kannada, tulu },
        diseases,
        sideEffects,
        interactions: interactions.map((row, index) => ({ ...row, source_row: index + 2 })),
        evidence,
      };
      data.graph = buildGraph(data);
      return data;
    }).catch((error) => {
      datasetPromise = null;
      throw error;
    });
  }
  return datasetPromise;
}

function normalizeLanguage(language) {
  const normalized = String(language || "en").trim().toLowerCase();
  if (normalized === "tlu" || normalized === "te") return "tulu";
  return LANGUAGES.includes(normalized) ? normalized : "en";
}

function clean(value) {
  return String(value || "").trim();
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function matchMedicine(data, value) {
  const query = clean(value).toLocaleLowerCase();
  if (!query) return null;
  return data.english.find((medicine) => [
    medicine.drug_id,
    medicine.drug_name,
    medicine.generic_name,
    medicine.active_ingredient,
  ].some((field) => clean(field).toLocaleLowerCase() === query))
    || data.english.find((medicine) => [
      medicine.drug_id,
      medicine.drug_name,
      medicine.generic_name,
      medicine.active_ingredient,
    ].some((field) => clean(field).toLocaleLowerCase().includes(query)))
    || null;
}

function medicineForLanguage(data, medicine, language = "en") {
  if (!medicine) return null;
  const lang = normalizeLanguage(language);
  const localized = data.languages[lang].find((item) => item.drug_id === medicine.drug_id) || medicine;
  const translated = (field) => clean(localized[field]) || clean(medicine[field]);
  return {
    ...medicine,
    drug_name: translated("drug_name"),
    disease: translated("disease"),
    drug_class: translated("drug_class"),
    active_ingredient: translated("active_ingredient"),
    description: translated("description"),
    side_effects: translated("side_effects"),
    contraindications: translated("contraindications"),
    warnings: translated("warnings"),
    major_interactions: translated("major_interactions"),
    description_en: clean(medicine.description),
    description_kn: data.languages.kn.find((item) => item.drug_id === medicine.drug_id)?.description || "",
    description_tulu: data.languages.tulu.find((item) => item.drug_id === medicine.drug_id)?.description || "",
    warnings_en: clean(medicine.warnings),
    warnings_kn: data.languages.kn.find((item) => item.drug_id === medicine.drug_id)?.warnings || "",
    warnings_tulu: data.languages.tulu.find((item) => item.drug_id === medicine.drug_id)?.warnings || "",
    contraindications_en: clean(medicine.contraindications),
    contraindications_kn: data.languages.kn.find((item) => item.drug_id === medicine.drug_id)?.contraindications || "",
    contraindications_tulu: data.languages.tulu.find((item) => item.drug_id === medicine.drug_id)?.contraindications || "",
    lang,
    interactions: getMedicineInteractions(data, medicine).map((item) => ({
      drug_id: item.drug2_id || item.drug2.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      drug_name: item.drug2,
      severity: item.severity,
      description: item.description,
    })),
  };
}

function listMedicineNames(data, language = "en") {
  const lang = normalizeLanguage(language);
  return data.languages[lang]
    .map((medicine) => clean(medicine.drug_name))
    .filter(Boolean)
    .sort((first, second) => first.localeCompare(second));
}

function findEvidenceRule(data, first, second) {
  const left = first.toLocaleLowerCase();
  const right = second.toLocaleLowerCase();
  return data.evidence.rules.find((rule) => {
    const ruleLeft = rule.left.map((name) => name.toLocaleLowerCase());
    const ruleRight = rule.right.map((name) => name.toLocaleLowerCase());
    return (ruleLeft.includes(left) && ruleRight.includes(right))
      || (ruleLeft.includes(right) && ruleRight.includes(left));
  }) || null;
}

function resolveInteraction(data, firstValue, secondValue, language = "en") {
  const firstMedicine = matchMedicine(data, firstValue);
  const secondMedicine = matchMedicine(data, secondValue);
  if (!firstMedicine || !secondMedicine || firstMedicine.drug_id === secondMedicine.drug_id) return null;

  const firstName = firstMedicine.drug_name;
  const secondName = secondMedicine.drug_name;
  const matches = data.interactions.filter((row) => row.drug2_in_scope.toLowerCase() === "yes"
    && ((row.drug1_id === firstMedicine.drug_id && row.drug2_id === secondMedicine.drug_id)
      || (row.drug1_id === secondMedicine.drug_id && row.drug2_id === firstMedicine.drug_id)));
  const rule = findEvidenceRule(data, firstName, secondName);
  if (!matches.length && !rule) return null;

  const severities = unique(matches.map((row) => clean(row.severity).replace(/^./, (letter) => letter.toUpperCase())));
  const conflict = severities.length > 1;
  const reviewRequired = conflict || !severities.length || severities.includes("Unknown") || Boolean(rule?.review_note);
  const orderedNames = [firstName, secondName].sort((a, b) => a.localeCompare(b));
  const description = rule?.description
    || "An interaction record exists in the project dataset, but pair-specific clinical details are not included in this static demo.";

  return {
    drug1: orderedNames[0],
    drug2: orderedNames[1],
    severity: reviewRequired ? "Review required" : severities[0],
    source_severities: severities,
    review_required: reviewRequired,
    source: "local_dataset",
    analysis_method: "Recorded-pair lookup; no live service or ML inference",
    severity_clinically_validated: false,
    source_rows: matches.map((row) => row.source_row),
    description: conflict
      ? `Source records disagree on severity: ${severities.join(", ")}. Clinical review is required before assigning a rating.`
      : description,
    recommendation: rule?.recommendation
      || "The demo does not provide pair-specific management guidance. Consult a qualified clinician; missing records do not establish safety.",
    match_basis: rule?.basis || "Named medicine pair in the project dataset.",
    severity_basis: severities.length
      ? "Project dataset rating; severity labels are not clinically validated."
      : "The reference text identifies a potential risk but does not assign a severity rating.",
    evidence_sources: rule?.sources || [],
    evidence_basis: rule?.basis || "",
    review_note: rule?.review_note || "",
    lang: normalizeLanguage(language),
  };
}

function getMedicineInteractions(data, medicine) {
  const rows = data.interactions.filter((row) => row.drug1_id === medicine.drug_id || row.drug2_id === medicine.drug_id);
  return rows.map((row) => ({
    ...row,
    drug2: row.drug1_id === medicine.drug_id ? row.drug2 : row.drug1,
    drug2_id: row.drug1_id === medicine.drug_id ? row.drug2_id : row.drug1_id,
  }));
}

function interactionCoverage(data, names) {
  const uniqueNames = unique(names.map(clean));
  const supported = uniqueNames.filter((name) => matchMedicine(data, name));
  const unsupported = uniqueNames.filter((name) => !matchMedicine(data, name));
  const pairs = [];
  for (let first = 0; first < uniqueNames.length; first += 1) {
    for (let second = first + 1; second < uniqueNames.length; second += 1) {
      pairs.push([uniqueNames[first], uniqueNames[second]]);
    }
  }
  const records = pairs.filter(([first, second]) => resolveInteraction(data, first, second));
  return {
    total_medicines: uniqueNames.length,
    covered_medicines: supported.length,
    unsupported_medicines: unsupported,
    total_pairs: pairs.length,
    pairs_with_records: records.length,
    message: `${supported.length} of ${uniqueNames.length} medicines are in the reference catalog; ${unsupported.length} not checked. ${records.length} of ${pairs.length} pairs have interaction records. Missing records do not establish safety.`,
  };
}

function buildGraph(data) {
  const nodes = [];
  const links = [];
  const nodeIds = new Set();
  const edgeIds = new Set();
  const addNode = (id, name, type, extra = {}) => {
    if (!id || nodeIds.has(id)) return;
    nodes.push({ id, node_id: id, name, type, ...extra });
    nodeIds.add(id);
  };
  const addLink = (source, target, relationship, type, extra = {}) => {
    const key = `${source}:${target}:${relationship}`;
    if (!source || !target || edgeIds.has(key)) return;
    links.push({ source, target, relationship, type, ...extra });
    edgeIds.add(key);
  };

  data.english.forEach((medicine) => addNode(medicine.drug_id, medicine.drug_name, "drug", {
    generic_name: medicine.generic_name,
    drug_class: medicine.drug_class,
  }));
  data.diseases.forEach((row) => {
    addNode(row.disease_id, row.disease, "disease");
    addLink(row.drug_id, row.disease_id, "TREATS", "treats");
  });
  data.sideEffects.forEach((row) => {
    const id = `sideeffect:${clean(row.side_effect).toLocaleLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
    addNode(id, row.side_effect, "sideeffect");
    addLink(row.drug_id, id, "CAUSES", "causes");
  });
  for (let first = 0; first < data.english.length; first += 1) {
    for (let second = first + 1; second < data.english.length; second += 1) {
      const interaction = resolveInteraction(
        data,
        data.english[first].drug_name,
        data.english[second].drug_name,
      );
      if (interaction) {
        addLink(
          data.english[first].drug_id,
          data.english[second].drug_id,
          "INTERACTS_WITH",
          "interaction",
          {
            severity: interaction.severity,
            review_required: interaction.review_required,
            source_rows: interaction.source_rows,
          },
        );
      }
    }
  }

  return { nodes, links };
}

function focusedGraph(graph, names, pairOnly = false) {
  const selected = graph.nodes.filter((node) => node.type === "drug"
    && names.some((name) => node.name.toLocaleLowerCase() === clean(name).toLocaleLowerCase()));
  const selectedIds = new Set(selected.map((node) => node.node_id));
  const links = graph.links.filter((link) => (selectedIds.has(link.source) || selectedIds.has(link.target))
    && (!pairOnly || (selectedIds.has(link.source) && selectedIds.has(link.target))));
  const connected = new Set([...selectedIds, ...links.flatMap((link) => [link.source, link.target])]);
  return {
    nodes: graph.nodes.filter((node) => connected.has(node.node_id)),
    links,
    selected_drugs: selected.map((node) => node.name),
    source: "static_csv",
  };
}

function sampleRegimen(data) {
  const names = SAMPLE_SCHEDULES.map((schedule) => schedule.medicine_name);
  const interactions = [];
  for (let first = 0; first < names.length; first += 1) {
    for (let second = first + 1; second < names.length; second += 1) {
      const interaction = resolveInteraction(data, names[first], names[second]);
      if (interaction) interactions.push(interaction);
    }
  }
  const coverage = interactionCoverage(data, names);
  return {
    coverage,
    interactions,
    adherence: {
      interpretation: "Sample values for demonstration only. They are not patient records or a measure of clinical adherence.",
      from_date: "2026-02-17",
      timezone: "UTC",
      rows: SAMPLE_SCHEDULES.map((schedule, index) => ({
        schedule_id: schedule.schedule_id,
        medicine_name: schedule.medicine_name,
        recorded_events: index === 0 ? 8 : index === 1 ? 7 : 0,
        scheduled_days: 14,
        days_with_confirmation: index === 0 ? 8 : index === 1 ? 7 : 0,
        unconfirmed_days: index === 0 ? 6 : index === 1 ? 7 : 14,
      })),
    },
  };
}

function routeError(message, status = 404) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function makeInteractionResponse(data, names, language) {
  const coverage = interactionCoverage(data, names);
  const unsupported = coverage.unsupported_medicines.length > 0;
  const interaction = unsupported ? null : resolveInteraction(data, names[0], names[1], language);
  return interaction
    ? { status: "success", interaction, coverage }
    : {
      status: "not_found",
      message: `No interaction record was found for ${names.join(" and ")} in the static reference dataset.`,
      interaction: null,
      lang: normalizeLanguage(language),
      coverage,
    };
}

export async function handleDemoRequest(config) {
  const data = await loadDemoData();
  const method = (config.method || "get").toLowerCase();
  const url = new URL(config.url || "/", globalThis.location?.origin || "http://localhost");
  const path = decodeURIComponent(url.pathname.replace(/\/+$/, "") || "/");
  const params = { ...Object.fromEntries(url.searchParams), ...(config.params || {}) };
  const language = normalizeLanguage(params.lang);
  const graph = data.graph;
  const medicines = data.languages[language];

  if (method === "get" && path === "/health") return { status: "ok", mode: "static-demo" };
  if (method === "get" && path === "/medicines") return {
    status: "success",
    medicines: listMedicineNames(data, language),
  };
  if (method === "get" && path.startsWith("/medicine/")) {
    const medicine = matchMedicine(data, path.slice("/medicine/".length));
    if (!medicine) throw routeError("Medicine not found in the static catalog.");
    return { status: "success", medicine: medicineForLanguage(data, medicine, language) };
  }
  if (method === "get" && path === "/neo4j/search") {
    const query = clean(params.term).toLocaleLowerCase();
    if (!query) return { results: [] };
    const results = medicines.filter((medicine) => [
      medicine.drug_name,
      medicine.generic_name,
      medicine.active_ingredient,
      medicine.drug_id,
    ].some((field) => clean(field).toLocaleLowerCase().includes(query)))
      .slice(0, Number(params.limit) || 10)
      .map((medicine) => medicineForLanguage(data, medicine, language));
    return { results };
  }
  if (method === "get" && path === "/neo4j/diseases") {
    const diseaseNames = unique(medicines.map((medicine) => clean(medicine.disease))).sort((a, b) => a.localeCompare(b));
    return {
      status: "success",
      diseases: diseaseNames,
      lang: language,
      disease_count: diseaseNames.length,
      medicine_count: medicines.length,
    };
  }
  if (method === "get" && path.startsWith("/neo4j/diseases/") && path.endsWith("/drugs")) {
    const diseaseName = path.slice("/neo4j/diseases/".length, -"/drugs".length);
    const matching = medicines.filter((medicine) => clean(medicine.disease).toLocaleLowerCase() === diseaseName.toLocaleLowerCase());
    return {
      status: "success",
      disease: diseaseName,
      lang: language,
      drugs: matching.map((medicine) => medicineForLanguage(data, medicine, language)),
    };
  }
  if (method === "get" && path.startsWith("/neo4j/drugs/")) {
    const medicine = matchMedicine(data, path.slice("/neo4j/drugs/".length));
    if (!medicine) throw routeError("Medicine not found in the static catalog.");
    return medicineForLanguage(data, medicine, language);
  }
  if (method === "get" && path === "/neo4j/graph") return { status: "success", ...graph, source: "static_csv" };
  if (method === "get" && path === "/neo4j/drug-graph") {
    return focusedGraph(graph, [params.drug]);
  }
  if (method === "get" && path === "/neo4j/interaction-graph") {
    return focusedGraph(graph, [params.drug1, params.drug2], true);
  }
  if (method === "get" && path === "/interaction") {
    const names = [params.drug1, params.drug2].map(clean);
    if (!names.every(Boolean)) throw routeError("Choose two medicines to check their interaction.", 422);
    return makeInteractionResponse(data, names, language);
  }
  if (method === "post" && path === "/interaction/multi") {
    const body = typeof config.data === "string" ? JSON.parse(config.data || "{}") : (config.data || {});
    const names = Array.isArray(body.drugs) ? body.drugs.map(clean).filter(Boolean) : [];
    if (names.length < 2) throw routeError("At least two medicines are required.", 422);
    const results = [];
    for (let first = 0; first < names.length; first += 1) {
      for (let second = first + 1; second < names.length; second += 1) {
        const result = makeInteractionResponse(data, [names[first], names[second]], language);
        if (result.interaction) results.push(result.interaction);
      }
    }
    const reviewRequired = results.some((item) => item.review_required);
    const severityOrder = { Severe: 3, High: 3, Moderate: 2, Mild: 1, Low: 1 };
    const maxSeverity = reviewRequired
      ? "Review required"
      : results.reduce((maximum, item) => severityOrder[item.severity] > (severityOrder[maximum] || 0) ? item.severity : maximum, "None");
    return {
      status: "success",
      drugs_analyzed: names,
      total_interactions_found: results.length,
      max_severity: maxSeverity,
      interactions: results,
      lang: language,
      coverage: interactionCoverage(data, names),
    };
  }
  if (method === "get" && path === "/patient-schedule") {
    return { status: "success", schedules: SAMPLE_SCHEDULES };
  }
  if (method === "get" && path === "/patient-schedule/removed") {
    return { status: "success", schedules: [] };
  }
  if (method === "get" && path === "/patient/medication-history") {
    return { status: "success", history: SAMPLE_HISTORY };
  }
  if (method === "get" && path === "/patient/profile") {
    return { status: "success", profile: SAMPLE_PATIENT };
  }
  if (method === "get" && path === "/patient/access-requests") {
    return {
      requests: [{
        requestId: "DEMO-ACCESS-001",
        doctorId: SAMPLE_DOCTOR.username,
        doctorName: SAMPLE_DOCTOR.full_name,
        status: "ACCEPTED",
        expiresAt: "2026-12-31T23:59:59Z",
      }],
    };
  }
  if (method === "get" && path === "/patient/access-log") {
    return {
      events: [{
        createdAt: "2026-03-15T10:00:00Z",
        doctorId: SAMPLE_DOCTOR.username,
        action: "demo_record_view",
        category: "read",
      }],
      next_cursor: null,
    };
  }
  if (method === "get" && path === "/doctor/reference-status") {
    return { graph_check: { status: "available", message: "Static CSV reference data is loaded." } };
  }
  if (method === "get" && path === "/auth/me") return SAMPLE_DOCTOR;
  if (method === "get" && path === "/auth/providers") return { google_enabled: false };
  if (method === "get" && path === "/doctor/patients") {
    return { status: "success", patients: [SAMPLE_PATIENT_ACCESS] };
  }
  if (method === "get" && path === "/doctor/medication-history") {
    return { status: "success", history: SAMPLE_HISTORY };
  }
  if (method === "get" && /^\/doctor\/patients\/[^/]+\/medications$/.test(path)) {
    return {
      status: "success",
      patient_username: SAMPLE_PATIENT.username,
      medications: SAMPLE_SCHEDULES,
      history: SAMPLE_HISTORY,
      survey_summary: {
        last_survey_date: "2026-03-01",
        side_effects_reported: ["No sample reports recorded"],
        lifestyle_factors: "Synthetic demonstration value; not patient-reported.",
      },
    };
  }
  if (method === "get" && /^\/doctor\/patients\/[^/]+\/regimen$/.test(path)) {
    return sampleRegimen(data);
  }
  if (method === "get" && /^\/doctor\/patients\/[^/]+\/report$/.test(path)) {
    return {
      generated_at: "2026-03-16T10:00:00Z",
      doctor: SAMPLE_DOCTOR.username,
      consent: { respondedAt: "2026-03-01T10:00:00Z", expiresAt: "2026-12-31T23:59:59Z", scope: ["medications", "history"] },
      patient: SAMPLE_PATIENT,
      prescriptions: SAMPLE_SCHEDULES,
      history: SAMPLE_HISTORY,
    };
  }
  if (method === "get" && path === "/admin/doctor-requests") {
    return {
      requests: [{
        request_id: "DEMO-REQUEST-001",
        full_name: "Sample Doctor Applicant",
        email: "doctor@example.invalid",
        medical_registration_no: "DEMO-REG-001",
        specialization: "General Medicine",
        hospital: "Sample Clinic",
        status: "pending",
      }],
    };
  }
  if (method === "post" && path === "/prescription-ocr") {
    const medicine = medicineForLanguage(data, matchMedicine(data, "metformin"), language);
    return {
      filename: "sample-prescription.png",
      lang: language,
      demo_output: true,
      ocr_result: {
        medicine: medicine.drug_name,
        dosage: "500 mg",
        instructions: "Take with food (sample output)",
        medicine_details: medicine,
      },
    };
  }
  if (method === "post" && path === "/upload-image") {
    return {
      filename: "sample-medicine-image.png",
      lang: language,
      demo_output: true,
      ocr_result: { detected_medicine: "Metformin", confidence: 0.98, note: "Predefined demo output; the selected image was not processed or uploaded." },
    };
  }
  if (method === "post" && path === "/voice-search") {
    const requestedMedicine = params.medicine_name || "Metformin";
    const found = matchMedicine(data, requestedMedicine);
    if (!found) throw routeError("No matching sample medicine was found.");
    const medicine = medicineForLanguage(data, found, language);
    return {
      status: "success",
      demo_output: true,
      detected_text: medicine.drug_name,
      detected_medicine: medicine.drug_name,
      medicine_details: medicine,
      response_text: `${medicine.drug_name}: ${medicine.description}`,
      response_language: language,
      lang: language,
      detected_language: language,
    };
  }
  if (method === "get" && path === "/tts") {
    throw routeError("Audio playback is not available in the static demo. The text result is available.", 501);
  }
  if (method === "post" && path === "/auth/logout") return { status: "success" };

  const readOnlyPath = path.startsWith("/admin/")
    || path.startsWith("/patient/")
    || path.startsWith("/patient-schedule")
    || path.startsWith("/doctor/")
    || path.startsWith("/auth/")
    || path.startsWith("/fcm/");
  if (readOnlyPath && method !== "get") {
    throw routeError("This is a read-only static demo. Changes are not saved.", 405);
  }
  throw routeError(`No static demo response is defined for ${method.toUpperCase()} ${path}.`, 404);
}

export const demoFixtures = {
  samplePatient: SAMPLE_PATIENT,
  sampleSchedules: SAMPLE_SCHEDULES,
  sampleHistory: SAMPLE_HISTORY,
};
