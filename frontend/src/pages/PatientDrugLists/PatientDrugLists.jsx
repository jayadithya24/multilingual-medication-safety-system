import { useEffect, useState } from "react";
import api from "../../services/api";
import "./PatientDrugLists.css";

function PatientDrugLists() {
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState("");
    const [medications, setMedications] = useState([]);

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
    // When doctor selects a patient
    // --------------------------------------------------

    const handlePatientChange = async (event) => {
        const username = event.target.value;

        setSelectedPatient(username);
        setMedications([]);
        setError("");

        if (!username) {
            return;
        }

        try {
            setLoadingMedications(true);

            const response = await api.get(
                `/doctor/patients/${encodeURIComponent(username)}/drugs`
            );

            console.log(
                "Selected patient medications:",
                response.data
            );

            setMedications(
                response.data.medications || []
            );

        } catch (err) {
            console.error(
                "Error loading patient medications:",
                err
            );

            // If patient has no medication records,
            // don't treat it as a serious page error.
            if (err?.response?.status === 404) {
                setMedications([]);
            } else {
                const detail = err?.response?.data?.detail;

                setError(
                    detail || "Unable to load patient medications."
                );
            }

        } finally {
            setLoadingMedications(false);
        }
    };

    // --------------------------------------------------
    // Find selected patient's details
    // --------------------------------------------------

    const selectedPatientData = patients.find(
        (patient) =>
            patient.username === selectedPatient
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


            {/* Patient Selector */}

            <section className="patient-drug-lists__selector">

                <label htmlFor="patient-select">
                    Select Patient
                </label>

                <select
                    id="patient-select"
                    value={selectedPatient}
                    onChange={handlePatientChange}
                    disabled={loading}
                >

                    <option value="">
                        {loading
                            ? "Loading patients..."
                            : "Select a patient"}
                    </option>

                    {patients.map((patient) => (

                        <option
                            key={patient.username}
                            value={patient.username}
                        >
                            {patient.full_name}
                        </option>

                    ))}

                </select>

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

                        <p>
                            Email:{" "}
                            {selectedPatientData.email}
                        </p>

                    </div>


                    <div className="patient-drug-lists__patient-meta">

                        <div>
                            <span>
                                Age
                            </span>

                            <strong>
                                {selectedPatientData.age ?? "Not provided"}
                            </strong>
                        </div>


                        <div>
                            <span>
                                Gender
                            </span>

                            <strong>
                                {selectedPatientData.gender ?? "Not provided"}
                            </strong>
                        </div>


                        <div>
                            <span>
                                Condition
                            </span>

                            <strong>
                                {selectedPatientData.medical_condition ??
                                    "Not provided"}
                            </strong>
                        </div>

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