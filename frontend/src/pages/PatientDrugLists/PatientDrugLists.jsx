import { useEffect, useState } from "react";
import api from "../../services/api";
import "./PatientDrugLists.css";

function PatientDrugLists() {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState("");
    const [medications, setMedications] = useState([]);
    const [requestingPatient, setRequestingPatient] = useState("");

    const [loading, setLoading] = useState(true);
    const [loadingMedications, setLoadingMedications] = useState(false);
    const [error, setError] = useState("");

    // --------------------------------------------------
    // Load real registered patients from MongoDB
    // --------------------------------------------------

    useEffect(() => {
        const loadPatients = async () => {
            try {
                setLoading(true);
                setError("");

                const response = await api.get("/doctor/patients");

                console.log("Doctor patients:", response.data);

                setPatients(response.data.patients || []);

            } catch (err) {
                console.error("Error loading patients:", err);

                const detail = err?.response?.data?.detail;

                setError(
                    detail || "Unable to load registered patients."
                );
            } finally {
                setLoading(false);
            }
        };

        loadPatients();
    }, []);

    // --------------------------------------------------
    // Selecting a patient only shows consent state. Medication access is explicit.
    // --------------------------------------------------

    const requestAccess = async (patientId) => {
        try {
            setRequestingPatient(patientId);
            await api.post("/doctor/access-request", { patient_id: patientId });
            const response = await api.get("/doctor/patients");
            setPatients(response.data.patients || []);
        } catch (err) {
            setError(err?.response?.data?.detail || "Unable to request access.");
        } finally {
            setRequestingPatient("");
        }
    };

    const viewPatientDetails = async (patientId) => {
        try {
            setLoadingMedications(true);
            setSelectedPatient(patientId);
            const response = await api.get(`/doctor/patients/${encodeURIComponent(patientId)}/medications`);
            setMedications(response.data.medications || []);
            setError("");
        } catch (err) {
            setMedications([]);
            setError(err?.response?.data?.detail || "Unable to load patient medications.");
        } finally {
            setLoadingMedications(false);
        }
    };

    // --------------------------------------------------
    // Find selected patient's details
    // --------------------------------------------------

    const selectedPatientData = patients.find(
        (patient) =>
            patient.patient_id === selectedPatient
    );

    return (
        <div className="patient-drug-lists">

            {/* Hero */}

            <section className="patient-drug-lists__hero">

                <p className="patient-drug-lists__kicker">
                    PATIENT MEDICATIONS
                </p>

                <h1>
                    Patient Drug Lists
                </h1>

                <p>
                    Review medicines currently associated
                    with registered patients.
                </p>

            </section>


            <section className="patient-drug-lists__results">
                <div className="patient-drug-lists__results-header">
                    <div><p>ACCESS REQUESTS</p><h2>Patients</h2></div>
                    <span>{patients.length} patients</span>
                </div>
                {loading ? <div className="patient-drug-lists__loading">Loading patients...</div> : (
                    <div className="patient-drug-lists__grid">
                        {patients.map((patient) => (
                            <article className="patient-drug-card" key={patient.patient_id}>
                                <div className="patient-drug-card__content">
                                    <h3>{patient.full_name}</h3>
                                    <p className="patient-drug-card__generic">Patient ID: {patient.patient_id}</p>
                                </div>
                                <div className="patient-drug-card__schedule">
                                    {patient.status === "NONE" && <button type="button" onClick={() => requestAccess(patient.patient_id)} disabled={requestingPatient === patient.patient_id}>{requestingPatient === patient.patient_id ? "Requesting..." : "Request Access"}</button>}
                                    {patient.status === "PENDING" && <strong>Pending</strong>}
                                    {patient.status === "REJECTED" && <strong>Rejected</strong>}
                                    {patient.status === "ACCEPTED" && <button type="button" onClick={() => viewPatientDetails(patient.patient_id)}>View Patient Details</button>}
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


            {/* Patient Information */}

            {selectedPatientData && (

                <section className="patient-drug-lists__patient">

                    <div>

                        <span className="patient-drug-lists__label">
                            PATIENT
                        </span>

                        <h2>
                            {selectedPatientData.full_name}
                        </h2>

                        <p>
                            Patient ID:{" "}
                            {selectedPatientData.patient_id}
                        </p>

                    </div>


                    <div className="patient-drug-lists__patient-meta">

                    </div>

                </section>

            )}


            {/* Medication Results */}

            {selectedPatient && (

                <section className="patient-drug-lists__results">

                    <div className="patient-drug-lists__results-header">

                        <div>

                            <p>
                                CURRENT MEDICATIONS
                            </p>

                            <h2>
                                Medication List
                            </h2>

                        </div>

                        <span>
                            {medications.length} medicines
                        </span>

                    </div>


                    {/* Loading */}

                    {loadingMedications ? (

                        <div className="patient-drug-lists__loading">
                            Loading medications...
                        </div>

                    ) : medications.length === 0 ? (

                        <div className="patient-drug-lists__empty">
                            No medicines found for this patient.
                        </div>

                    ) : (

                        <div className="patient-drug-lists__grid">

                            {medications.map(
                                (medicine, index) => (

                                    <article
                                        className="patient-drug-card"
                                        key={
                                            medicine.schedule_id ||
                                            `${medicine.medicine_id}-${index}`
                                        }
                                    >

                                        <div className="patient-drug-card__icon">
                                            💊
                                        </div>


                                        <div className="patient-drug-card__content">

                                            <h3>
                                                {medicine.medicine_name}
                                            </h3>

                                            <p className="patient-drug-card__generic">
                                                {medicine.dosage
                                                    ? `Dosage: ${medicine.dosage}`
                                                    : "Dosage not specified"}
                                            </p>


                                            {medicine.disease && (

                                                <span className="patient-drug-card__class">
                                                    {medicine.disease}
                                                </span>

                                            )}

                                        </div>


                                        <div className="patient-drug-card__schedule">

                                            <span>
                                                Schedule
                                            </span>

                                            <strong>
                                                {medicine.frequency ||
                                                    "As prescribed"}
                                            </strong>

                                        </div>

                                    </article>

                                )
                            )}

                        </div>

                    )}

                </section>

            )}

        </div>
    );
}

export default PatientDrugLists;