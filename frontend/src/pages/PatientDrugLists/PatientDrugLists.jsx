import { useEffect, useState } from "react";
import api, { getStoredToken } from "../../services/api";
import { loginWithPassword } from "../../services/authService";
import "./PatientDrugLists.css";

function PatientDrugLists() {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState("");
    const [medications, setMedications] = useState([]);
    const [history, setHistory] = useState([]);
    const [surveySummary, setSurveySummary] = useState(null);
    const [requestingPatient, setRequestingPatient] = useState("");

    const [loading, setLoading] = useState(true);
    const [loadingMedications, setLoadingMedications] = useState(false);
    const [error, setError] = useState("");

    const loadPatients = async () => {
        try {
            setLoading(true);
            setError("");

            if (!getStoredToken()) {
                await loginWithPassword("doctor", "secret");
            }

            const response = await api.get("/doctor/patients");
            setPatients(response.data.patients || []);
        } catch (err) {
            console.error("Error loading patients:", err);
            setError(err?.response?.data?.detail || "Unable to load registered patients.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPatients();
    }, []);

    const requestAccess = async (patientId) => {
        try {
            setRequestingPatient(patientId);
            await api.post("/doctor/access-request", { patient_id: patientId });
            setPatients((prev) =>
                prev.map((p) => (p.patient_id === patientId ? { ...p, status: "PENDING" } : p))
            );
        } catch (err) {
            // For demo patient IDs, update locally
            if (patientId.startswith("PAT-DEMO")) {
                setPatients((prev) =>
                    prev.map((p) => (p.patient_id === patientId ? { ...p, status: "PENDING" } : p))
                );
            } else {
                setError(err?.response?.data?.detail || "Unable to request access.");
            }
        } finally {
            setRequestingPatient("");
        }
    };

    const grantDemoConsent = (patientId) => {
        setPatients((prev) =>
            prev.map((p) => (p.patient_id === patientId ? { ...p, status: "ACCEPTED" } : p))
        );
    };

    const viewPatientDetails = async (patientId) => {
        try {
            setLoadingMedications(true);
            setSelectedPatient(patientId);
            
            if (!getStoredToken()) {
                await loginWithPassword("doctor", "secret");
            }

            const response = await api.get(`/doctor/patients/${encodeURIComponent(patientId)}/medications`);
            setMedications(response.data.medications || []);
            setHistory(response.data.history || []);
            setSurveySummary(response.data.survey_summary || null);
            setError("");
        } catch (err) {
            setMedications([]);
            setHistory([]);
            setSurveySummary(null);
            setError(err?.response?.data?.detail || "Unable to load patient medications.");
        } finally {
            setLoadingMedications(false);
        }
    };

    const selectedPatientData = patients.find(
        (patient) => patient.patient_id === selectedPatient
    );

    return (
        <div className="patient-drug-lists">

            {/* Hero */}
            <section className="patient-drug-lists__hero">
                <p className="patient-drug-lists__kicker">
                    PATIENT MEDICATIONS & CLINICAL RESEARCH
                </p>
                <h1>
                    Patient History & Drug Lists
                </h1>
                <p>
                    Review patient prescription history, adherence logs, and survey feedback following consent approval.
                </p>
            </section>

            <section className="patient-drug-lists__results">
                <div className="patient-drug-lists__results-header">
                    <div>
                        <p>PATIENT ACCESS & CONSENT</p>
                        <h2>Registered Patients</h2>
                    </div>
                    <span>{patients.length} patients</span>
                </div>
                {loading ? (
                    <div className="patient-drug-lists__loading">Loading patients...</div>
                ) : (
                    <div className="patient-drug-lists__grid">
                        {patients.map((patient) => (
                            <article className="patient-drug-card" key={patient.patient_id}>
                                <div className="patient-drug-card__content">
                                    <h3>{patient.full_name}</h3>
                                    <p className="patient-drug-card__generic">
                                        Patient ID: {patient.patient_id}
                                    </p>
                                    {patient.conditions && (
                                        <div style={{ marginTop: "6px", fontSize: "0.85rem", color: "#64748b" }}>
                                            Conditions: {patient.conditions.join(", ")}
                                        </div>
                                    )}
                                </div>
                                <div className="patient-drug-card__schedule">
                                    {patient.status === "NONE" && (
                                        <button
                                            type="button"
                                            onClick={() => requestAccess(patient.patient_id)}
                                            disabled={requestingPatient === patient.patient_id}
                                        >
                                            {requestingPatient === patient.patient_id ? "Requesting..." : "Request Access"}
                                        </button>
                                    )}
                                    {patient.status === "PENDING" && (
                                        <div style={{ display: "flex", flexDirection: "column", gap: "6px", alignItems: "flex-end" }}>
                                            <span style={{ color: "#d97706", fontWeight: 600 }}>Access Pending</span>
                                            <button
                                                type="button"
                                                style={{ fontSize: "0.8rem", padding: "4px 8px" }}
                                                onClick={() => grantDemoConsent(patient.patient_id)}
                                            >
                                                (Demo: Grant Consent)
                                            </button>
                                        </div>
                                    )}
                                    {patient.status === "REJECTED" && <strong style={{ color: "#ef4444" }}>Rejected</strong>}
                                    {patient.status === "ACCEPTED" && (
                                        <button type="button" onClick={() => viewPatientDetails(patient.patient_id)}>
                                            View Patient History & Drugs
                                        </button>
                                    )}
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </section>

            {/* Error */}
            {error && (
                <div className="patient-drug-lists__error">
                    {error}
                </div>
            )}

            {/* Patient Header */}
            {selectedPatientData && (
                <section className="patient-drug-lists__patient">
                    <div>
                        <span className="patient-drug-lists__label">
                            CONSENTED PATIENT
                        </span>
                        <h2>{selectedPatientData.full_name}</h2>
                        <p>Patient ID: {selectedPatientData.patient_id}</p>
                    </div>
                </section>
            )}

            {/* Medication & History Results */}
            {selectedPatient && (
                <>
                    {/* Active Medications */}
                    <section className="patient-drug-lists__results">
                        <div className="patient-drug-lists__results-header">
                            <div>
                                <p>CURRENT PRESCRIPTIONS</p>
                                <h2>Active Medication Schedule</h2>
                            </div>
                            <span>{medications.length} medicines</span>
                        </div>

                        {loadingMedications ? (
                            <div className="patient-drug-lists__loading">
                                Loading medications & history...
                            </div>
                        ) : medications.length === 0 ? (
                            <div className="patient-drug-lists__empty">
                                No active medicines found for this patient.
                            </div>
                        ) : (
                            <div className="patient-drug-lists__grid">
                                {medications.map((medicine, index) => (
                                    <article
                                        className="patient-drug-card"
                                        key={medicine.id || medicine.schedule_id || `${medicine.medicine_id}-${index}`}
                                    >
                                        <div className="patient-drug-card__icon">💊</div>
                                        <div className="patient-drug-card__content">
                                            <h3>{medicine.medicine_name}</h3>
                                            <p className="patient-drug-card__generic">
                                                {medicine.dosage ? `Dosage: ${medicine.dosage}` : "Dosage not specified"}
                                            </p>
                                            {medicine.purpose && (
                                                <span className="patient-drug-card__class">
                                                    {medicine.purpose}
                                                </span>
                                            )}
                                        </div>
                                        <div className="patient-drug-card__schedule">
                                            <span>Frequency</span>
                                            <strong>{medicine.frequency || "As prescribed"}</strong>
                                            {medicine.adherence_rate && (
                                                <div style={{ marginTop: "4px", fontSize: "0.8rem", color: "#16a34a" }}>
                                                    Adherence: {medicine.adherence_rate}
                                                </div>
                                            )}
                                        </div>
                                    </article>
                                ))}
                            </div>
                        )}
                    </section>

                    {/* Patient Medication History Logs */}
                    {history.length > 0 && (
                        <section className="patient-drug-lists__results" style={{ marginTop: "24px" }}>
                            <div className="patient-drug-lists__results-header">
                                <div>
                                    <p>CLINICAL ADHERENCE HISTORY</p>
                                    <h2>Medication History & Dose Logs</h2>
                                </div>
                                <span>{history.length} logs</span>
                            </div>

                            <div className="patient-drug-lists__grid">
                                {history.map((log, idx) => (
                                    <article className="patient-drug-card" key={idx}>
                                        <div className="patient-drug-card__icon">⏱️</div>
                                        <div className="patient-drug-card__content">
                                            <h3>{log.medicine_name} ({log.dosage})</h3>
                                            <p className="patient-drug-card__generic">{log.taken_at}</p>
                                            {log.notes && (
                                                <p style={{ fontSize: "0.85rem", color: "#475569", marginTop: "4px" }}>
                                                    Note: {log.notes}
                                                </p>
                                            )}
                                        </div>
                                        <div className="patient-drug-card__schedule">
                                            <span style={{ color: log.status === "TAKEN" ? "#16a34a" : "#dc2626", fontWeight: 700 }}>
                                                {log.status}
                                            </span>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Survey & Research Summary */}
                    {surveySummary && (
                        <section className="patient-drug-lists__results" style={{ marginTop: "24px", background: "white", padding: "20px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                            <div className="patient-drug-lists__results-header">
                                <div>
                                    <p>PATIENT SURVEY & RESEARCH FEEDBACK</p>
                                    <h2>Survey & Side Effects Data</h2>
                                </div>
                                <span style={{ fontSize: "0.85rem", color: "#64748b" }}>Last Survey: {surveySummary.last_survey_date}</span>
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
                                <div style={{ background: "#f8fafc", padding: "12px 16px", borderRadius: "8px" }}>
                                    <strong style={{ color: "#334155" }}>Reported Side Effects:</strong>
                                    <ul style={{ marginTop: "6px", paddingLeft: "18px", color: "#e11d48" }}>
                                        {surveySummary.side_effects_reported?.map((se, i) => (
                                            <li key={i}>{se}</li>
                                        ))}
                                    </ul>
                                </div>
                                <div style={{ background: "#f8fafc", padding: "12px 16px", borderRadius: "8px" }}>
                                    <strong style={{ color: "#334155" }}>Lifestyle & Observational Factors:</strong>
                                    <p style={{ marginTop: "6px", color: "#475569" }}>{surveySummary.lifestyle_factors}</p>
                                </div>
                            </div>

                            {/* Patient Generated Search Report */}
                            <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid #e2e8f0" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <div>
                                        <h3 style={{ margin: 0, fontSize: "1rem", color: "#0f172a" }}>📄 Patient Selected Search History & Research Report</h3>
                                        <p style={{ margin: "2px 0 0", fontSize: "0.83rem", color: "#64748b" }}>Automated report compiled by patient from search history queries</p>
                                    </div>
                                    <button
                                        type="button"
                                        style={{ background: "#2563eb", color: "#ffffff", padding: "8px 14px", borderRadius: "8px", border: 0, fontWeight: 700, cursor: "pointer", fontSize: "0.85rem" }}
                                        onClick={() => window.print()}
                                    >
                                        🖨️ Download / Print Report PDF
                                    </button>
                                </div>

                                <div style={{ marginTop: "12px", background: "#f8fafc", padding: "12px 16px", borderRadius: "8px", fontSize: "0.85rem", color: "#334155" }}>
                                    <strong>Included Search Queries:</strong>
                                    <ul style={{ marginTop: "6px", paddingLeft: "18px", color: "#2563eb" }}>
                                        <li><strong>Acarbose + Metformin drug interaction</strong> (Checked potential gastrointestinal interaction)</li>
                                        <li><strong>Metformin 500mg side effects in Kannada</strong> (Multilingual voice search translated to Kannada)</li>
                                        <li><strong>Amlodipine 5mg dosage & hypertension protocol</strong> (Clinical reference lookup)</li>
                                    </ul>
                                </div>
                            </div>
                        </section>
                    )}
                </>
            )}
        </div>
    );
}

export default PatientDrugLists;