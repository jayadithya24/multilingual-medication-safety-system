import { useSearchParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import PatientNavigation from "../../components/PatientNavigation/PatientNavigation";
import Loading from "../../components/Loading/Loading";
import MedicineCard from "../../components/MedicineCard/MedicineCard";
import VoicePlayback from "../../components/VoicePlayback";

import { searchMedicine, fetchMedicines } from "../../services/medicineService";
import VoiceSearch from "../VoiceSearch/VoiceSearch";
import api from "../../services/api";
import { registerMedicationNotifications, sendTestNotification } from "../../services/fcmService";


import {
    fetchPatientSchedule,
    markMedicineAsTaken,
    deletePatientSchedule,
    fetchMedicationHistory,
} from "../../services/patientScheduleService";

import "./PublicDashboard.css";

const languageOptions = [
    { value: "en", label: "English" },
    { value: "kn", label: "Kannada" },
    { value: "tulu", label: "Tulu" },
];

function getNextDose(schedules) {
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    const doses = schedules.flatMap((schedule) =>
        (schedule.scheduled_times || []).map((time) => {
            const [hours, minutes] = time.split(":").map(Number);
            const minutesToday = hours * 60 + minutes;
            return {
                label: `${schedule.medicine_name} ${schedule.dosage}`,
                time,
                offset: minutesToday >= currentMinutes ? minutesToday : minutesToday + 1440,
            };
        }),
    );
    return doses.sort((first, second) => first.offset - second.offset)[0] || null;
}

function PublicDashboard() {
    const [searchParams] = useSearchParams();
    const requestedTab = searchParams.get("tab");
    const activeTab = ["voice", "medicines"].includes(requestedTab) ? requestedTab : "text";
    const [lang, setLang] = useState("en");

    // Medicine search
    const [medicineNames, setMedicineNames] = useState([]);
    const [query, setQuery] = useState("");
    const [textLoading, setTextLoading] = useState(false);
    const [textError, setTextError] = useState("");
    const [textResult, setTextResult] = useState(null);
    const searchVersion = useRef(0);

    // Patient medication
    const [schedules, setSchedules] = useState([]);
    const [history, setHistory] = useState([]);
    const [scheduleLoading, setScheduleLoading] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [scheduleError, setScheduleError] = useState("");
    const [historyError, setHistoryError] = useState("");
    const [takingMedicineId, setTakingMedicineId] = useState(null);
    const [deletingMedicineId, setDeletingMedicineId] = useState(null);
    const [schedulePendingDeletion, setSchedulePendingDeletion] = useState(null);
    const [accessRequests, setAccessRequests] = useState([]);
    const [accessRequestError, setAccessRequestError] = useState("");
    const [notificationStatus, setNotificationStatus] = useState("");
    const [testNotificationLoading, setTestNotificationLoading] = useState(false);

    // Load medicine names
    useEffect(() => {
        let isMounted = true;

        const loadMedicines = async () => {
            try {
                const response = await fetchMedicines(lang);

                if (isMounted) {
                    setMedicineNames(response.medicines || []);
                }
            } catch (error) {
                console.error(error);

                if (isMounted) {
                    setMedicineNames([]);
                }
            }
        };

        loadMedicines();

        return () => {
            isMounted = false;
        };
    }, [lang]);

    const enableNotifications = () => {
        registerMedicationNotifications()
            .then((result) => {
                console.info("[FCM] Registration result:", result);
                if (result.registered) {
                    setNotificationStatus("Medication reminders enabled");
                } else {
                    setNotificationStatus(`Medication reminders unavailable: ${result.reason}`);
                }
            })
            .catch((error) => {
                console.error("[FCM] Registration failed:", error);
                setNotificationStatus(`Medication reminders failed: ${error.message}`);
            });
    };

    const handleTestNotification = async () => {
        try {
            setTestNotificationLoading(true);
            const result = await sendTestNotification();
            setNotificationStatus(result.message || "Test notification sent.");
        } catch (error) {
            console.error("[FCM] Test notification failed:", error);
            setNotificationStatus(error?.response?.data?.detail || "Test notification failed.");
        } finally {
            setTestNotificationLoading(false);
        }
    };

    // -----------------------------
    // TEXT SEARCH
    // -----------------------------

    const resetTextState = () => {
        setTextError("");
        setTextResult(null);
    };

    const handleSearch = async () => {
        if (!query.trim()) {
            setTextError("Enter a medicine name first.");
            return;
        }

        const version = ++searchVersion.current;
        try {
            setTextLoading(true);
            resetTextState();

            const response = await searchMedicine(query.trim(), lang);
            if (version !== searchVersion.current) return;
            setTextResult(response);
        } catch (error) {
            if (version !== searchVersion.current) return;
            console.error(error);
            setTextError(
                "Unable to search for that medicine right now."
            );
        } finally {
            if (version === searchVersion.current) setTextLoading(false);
        }
    };

    // -----------------------------
    // PATIENT MEDICATION
    // -----------------------------

    const loadPatientMedication = async () => {
        try {
            setScheduleLoading(true);
            setHistoryLoading(true);

            setScheduleError("");
            setHistoryError("");

            const [scheduleResponse, historyResponse] =
                await Promise.all([
                    fetchPatientSchedule(),
                    fetchMedicationHistory(),
                ]);

            setSchedules(
                scheduleResponse.schedules || []
            );

            setHistory(
                historyResponse.history || []
            );

        } catch (error) {
            console.error(error);

            const status = error?.response?.status;

            if (status === 401) {
                setScheduleError(
                    "Your session has expired. Please login again."
                );
            } else if (status === 403) {
                setScheduleError(
                    "Only patient accounts can access medication schedules."
                );
            } else {
                setScheduleError(
                    "Unable to load your medication schedule."
                );
            }

            setSchedules([]);
            setHistory([]);
        } finally {
            setScheduleLoading(false);
            setHistoryLoading(false);
        }
    };

    const loadAccessRequests = async () => {
        try {
            const response = await api.get("/patient/access-requests");
            setAccessRequests(response.data.requests || []);
            setAccessRequestError("");
        } catch (error) {
            setAccessRequestError(error?.response?.data?.detail || "Unable to load access requests.");
        }
    };

    const respondToAccessRequest = async (requestId, decision) => {
        try {
            await api.put(`/patient/access-request/${encodeURIComponent(requestId)}/${decision}`);
            await loadAccessRequests();
        } catch (error) {
            setAccessRequestError(error?.response?.data?.detail || "Unable to update access request.");
        }
    };

    // Load patient schedule/history when My Medicines tab opens
    useEffect(() => {
        if (activeTab !== "medicines") return;
        let active = true;
        Promise.all([fetchPatientSchedule(), fetchMedicationHistory()])
            .then(([scheduleResponse, historyResponse]) => {
                if (!active) return;
                setSchedules(scheduleResponse.schedules || []);
                setHistory(historyResponse.history || []);
                setScheduleError("");
            })
            .catch(() => { if (active) setScheduleError("Unable to load your medicines. Refresh or sign in again."); });
        api.get("/patient/access-requests")
            .then(({ data }) => { if (active) { setAccessRequests(data.requests || []); setAccessRequestError(""); } })
            .catch(() => { if (active) setAccessRequestError("Unable to load access requests. Please refresh."); });
        return () => { active = false; };
    }, [activeTab]);

    const handleMarkAsTaken = async (scheduleId) => {
        try {
            setTakingMedicineId(scheduleId);

            await markMedicineAsTaken(scheduleId);

            // Reload schedule + history after marking medicine taken
            await loadPatientMedication();
        } catch (error) {
            console.error(error);

            alert(
                error?.response?.data?.detail ||
                "Unable to mark medicine as taken."
            );
        } finally {
            setTakingMedicineId(null);
        }
    };

    const confirmDeleteMedicine = async () => {
        if (!schedulePendingDeletion) {
            return;
        }

        const schedule = schedulePendingDeletion;
        try {
            setDeletingMedicineId(schedule.schedule_id);
            setScheduleError("");

            await deletePatientSchedule(schedule.schedule_id);
            setSchedules((currentSchedules) =>
                currentSchedules.filter(
                    (item) => item.schedule_id !== schedule.schedule_id
                )
            );
            setSchedulePendingDeletion(null);
        } catch (error) {
            console.error(error);
            setScheduleError(
                error?.response?.data?.detail ||
                "Unable to remove this medicine from your schedule."
            );
        } finally {
            setDeletingMedicineId(null);
        }
    };

    // -----------------------------
    // RESULTS
    // -----------------------------

    const textMedicine = textResult?.results?.[0] ?? null;
    const firstSentence = (value) => String(value || "").trim().match(/^.*?(?:[.!?।](?=\s|$)|$)/u)?.[0] || "";
    const spokenSummary = textMedicine ? [
        textMedicine.drug_name,
        firstSentence(textMedicine.description || textMedicine.disease),
        firstSentence(textMedicine.warnings),
    ].filter(Boolean).join(". ") : "";




    const nextDose = getNextDose(schedules);
    const pageHeading = {
        text: ["My Medication Dashboard", "Search medicines, scan medicine strips, use voice search, and manage your medication schedule."],
        voice: ["Voice Search", "Speak a medicine name or question, upload audio, and listen to medicine information in your language."],
        medicines: ["My Medicines", "Manage your medication schedule, mark doses as taken, and review your medication history."],
    }[activeTab];

    return (
        <div className="patient-portal">
            <section className="patient-shell">


                {/* HERO */}
                <div className="patient-hero">
                    <p className="patient-kicker">
                        Patient Portal
                    </p>

                    <h1>
                        {pageHeading[0]}
                    </h1>

                    <p>
                        {pageHeading[1]}
                    </p>
                </div>

            <PatientNavigation />

                {/* TOOLBAR */}
                {activeTab === "text" && <div className="patient-toolbar">

                    <label className="patient-language">
                        <span>Language</span>

                        <select
                            value={lang}
                            onChange={(event) => {
                                searchVersion.current += 1;
                                setLang(event.target.value);
                                setTextResult(null);
                                setTextLoading(false);
                                setTextError("");
                            }}
                        >
                            {languageOptions.map(
                                (option) => (
                                    <option
                                        key={option.value}
                                        value={option.value}
                                    >
                                        {option.label}
                                    </option>
                                )
                            )}
                        </select>
                    </label>
                </div>

                }

                {/* MAIN PANEL */}
                <div className="patient-panel">

                    {/* =========================
                        MEDICINE SEARCH
                    ========================= */}
                    {activeTab === "text" && (
                        <div className="patient-section">

                            <div className="patient-section__header">
                                <h2>
                                    Medicine Search
                                </h2>

                                <p>
                                    Search by drug name,
                                    generic name, or active
                                    ingredient.
                                </p>
                            </div>

                            <datalist id="patient-medicine-options">
                                {medicineNames.map(
                                    (medicine) => (
                                        <option
                                            key={medicine}
                                            value={medicine}
                                        />
                                    )
                                )}
                            </datalist>

                            <div className="patient-search-row">

                                <input
                                    type="text"
                                    list="patient-medicine-options"
                                    value={query}
                                    onChange={(event) =>
                                        setQuery(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Type a medicine name"
                                />

                                <button
                                    type="button"
                                    onClick={handleSearch}
                                    disabled={textLoading}
                                >
                                    {textLoading
                                        ? "Searching..."
                                        : "Search"}
                                </button>

                            </div>

                            {textLoading && <Loading />}

                            {textError && (
                                <div className="patient-error">
                                    {textError}
                                </div>
                            )}

                            {textResult && (
                                <div className="patient-result">
                                    {spokenSummary && <VoicePlayback text={spokenSummary} language={lang} controls={false} />}

                                    {textMedicine ? (
                                        <MedicineCard
                                            medicine={
                                                textMedicine
                                            }
                                        />
                                    ) : (
                                        <div className="patient-empty">
                                            Medicine not found.
                                        </div>
                                    )}

                                </div>
                            )}
                        </div>
                    )}

                    {/* =========================
                        VOICE
                    ========================= */}
                    {activeTab === "voice" && <VoiceSearch embedded />}

                    {/* =========================
                        MY MEDICINES
                    ========================= */}
                    {activeTab === "medicines" && (
                        <div className="patient-section">

                            <div className="patient-section__header patient-medicines-header">

                                <div>
                                    <h2>
                                        My Medicines
                                    </h2>

                                    <p>
                                        View your medicine
                                        schedule and track
                                        medicines you have
                                        taken.
                                    </p>
                                </div>

                                <button
                                    type="button"
                                    className="patient-refresh-button"
                                    onClick={
                                        () => { loadPatientMedication(); loadAccessRequests(); }
                                    }
                                    disabled={
                                        scheduleLoading ||
                                        historyLoading
                                    }
                                >
                                    Refresh
                                </button>

                            </div>

                            <details className="patient-medication-block">
                                <summary>Doctor access requests ({accessRequests.filter((request) => request.status === "PENDING").length} pending)</summary>
                                {accessRequestError && <div className="patient-error">{accessRequestError}</div>}
                                {accessRequests.length === 0 && !accessRequestError && (
                                    <div className="patient-empty">No medication access requests.</div>
                                )}
                                {accessRequests.map((request) => (
                                    <div className="patient-history-card" key={request.requestId}>
                                        <div>
                                            <h3>Dr. {request.doctorName} wants access to your medication details.</h3>
                                            <p>Status: {request.status}</p>
                                        </div>
                                        {request.status === "PENDING" && (
                                            <div>
                                                <button type="button" onClick={() => respondToAccessRequest(request.requestId, "accept")}>Accept</button>
                                                <button type="button" onClick={() => respondToAccessRequest(request.requestId, "reject")}>Reject</button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </details>

                            {/* SCHEDULE */}
                            <div className="patient-medication-block">

                                <div className="patient-medication-title">
                                    <h3>
                                        💊 Medicine Schedule
                                    </h3>

                                    <span>
                                        {
                                            schedules.length
                                        }{" "}
                                        scheduled
                                    </span>
                                </div>
                                {notificationStatus && <div className="patient-empty">{notificationStatus}</div>}
                                <button type="button" onClick={enableNotifications}>Enable Notifications</button>
                                <details className="patient-notification-tools">
                                <summary>Check notification delivery</summary>
                                <p>Keep the backend running and enable browser notifications on this device.</p>
                                <button
                                    type="button"
                                    className="patient-refresh-button"
                                    onClick={handleTestNotification}
                                    disabled={testNotificationLoading}
                                >
                                    {testNotificationLoading ? "Sending..." : "Send Test Notification"}
                                </button>
                                </details>
                                {nextDose && (
                                    <div className="patient-empty">
                                        Next scheduled dose: {nextDose.label} at {nextDose.time}
                                    </div>
                                )}

                                {scheduleLoading && (
                                    <Loading />
                                )}

                                {scheduleError && (
                                    <div className="patient-error">
                                        {scheduleError}
                                    </div>
                                )}

                                {!scheduleLoading &&
                                    !scheduleError &&
                                    schedules.length === 0 && (
                                        <div className="patient-empty">
                                            No medicines have
                                            been scheduled yet.
                                        </div>
                                    )}

                                <div className="patient-schedule-list">

                                    {schedules.map(
                                        (schedule) => (
                                            <div
                                                key={
                                                    schedule.schedule_id
                                                }
                                                className={`patient-schedule-card ${
                                                    schedule.status ===
                                                    "taken"
                                                        ? "is-taken"
                                                        : ""
                                                }`}
                                            >

                                                <div className="patient-schedule-main">

                                                    <div>
                                                        <h3>
                                                            {
                                                                schedule.medicine_name
                                                            }
                                                        </h3>

                                                        <p className="patient-dosage">
                                                            {
                                                                schedule.dosage
                                                            }
                                                        </p>
                                                    </div>

                                                    <span
                                                        className={`patient-status ${
                                                            schedule.status ===
                                                            "taken"
                                                                ? "taken"
                                                                : "pending"
                                                        }`}
                                                    >
                                                        {schedule.status ===
                                                        "taken"
                                                            ? "✓ Taken"
                                                            : schedule.reminder_enabled ? "Reminders on" : "Reminders off"}
                                                    </span>

                                                </div>

                                                <div className="patient-schedule-details">
                                                    {schedule.last_taken_at && <p>Last recorded dose: {new Date(schedule.last_taken_at).toLocaleString()}</p>}
                                                    {schedule.instructions && <p>Instructions: {schedule.instructions}</p>}

                                                    <div>
                                                        <span>
                                                            Time
                                                        </span>
                                                        <strong>
                                                            {(schedule.scheduled_times || []).join(", ") || "As needed"}
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Frequency
                                                        </span>
                                                        <strong>
                                                            {
                                                                schedule.frequency
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Disease
                                                        </span>
                                                        <strong>
                                                            {
                                                                schedule.disease ||
                                                                "—"
                                                            }
                                                        </strong>
                                                    </div>

                                                </div>

                                                <div className="patient-schedule-actions">
                                                    {schedule.status !==
                                                        "taken" && (
                                                        <button
                                                            type="button"
                                                            className="patient-taken-button"
                                                            onClick={() =>
                                                                handleMarkAsTaken(
                                                                    schedule.schedule_id
                                                                )
                                                            }
                                                            disabled={
                                                                takingMedicineId ===
                                                                    schedule.schedule_id ||
                                                                deletingMedicineId ===
                                                                    schedule.schedule_id
                                                            }
                                                        >
                                                            {takingMedicineId ===
                                                            schedule.schedule_id
                                                                ? "Saving..."
                                                                : "✓ Mark as Taken"}
                                                        </button>
                                                    )}

                                                    <button
                                                        type="button"
                                                        className="patient-delete-button"
                                                        onClick={() =>
                                                            setSchedulePendingDeletion(schedule)
                                                        }
                                                        disabled={
                                                            takingMedicineId ===
                                                                schedule.schedule_id ||
                                                            deletingMedicineId ===
                                                                schedule.schedule_id
                                                        }
                                                    >
                                                        {deletingMedicineId ===
                                                        schedule.schedule_id
                                                            ? "Removing..."
                                                            : "Remove from schedule"}
                                                    </button>
                                                </div>

                                                {schedule.status ===
                                                    "taken" && (
                                                    <div className="patient-taken-message">
                                                        ✓ Medicine
                                                        marked as
                                                        taken
                                                    </div>
                                                )}

                                            </div>
                                        )
                                    )}

                                </div>

                            </div>

                            {/* HISTORY */}
                            <div className="patient-medication-block">

                                <div className="patient-medication-title">
                                    <h3>
                                        📋 Medication History
                                    </h3>

                                    <span>
                                        {history.length}{" "}
                                        records
                                    </span>
                                </div>

                                {historyLoading && (
                                    <Loading />
                                )}

                                {historyError && (
                                    <div className="patient-error">
                                        {historyError}
                                    </div>
                                )}

                                {!historyLoading &&
                                    history.length === 0 && (
                                        <div className="patient-empty">
                                            No medication history
                                            yet.
                                        </div>
                                    )}

                                <div className="patient-history-list">

                                    {history.map(
                                        (record) => (
                                            <div
                                                key={
                                                    record.history_id
                                                }
                                                className="patient-history-card"
                                            >

                                                <div>
                                                    <h3>
                                                        {
                                                            record.medicine_name
                                                        }
                                                    </h3>

                                                    <p>
                                                        {
                                                            record.dosage
                                                        }
                                                    </p>
                                                </div>

                                                <div className="patient-history-info">

                                                    <span>
                                                        Scheduled:{" "}
                                                        {
                                                            record.scheduled_time
                                                        }
                                                    </span>

                                                    <span>
                                                        Taken:{" "}
                                                        {record.taken_at
                                                            ? new Date(
                                                                record.taken_at
                                                            ).toLocaleString()
                                                            : "—"}
                                                    </span>

                                                </div>

                                                <span className="patient-status taken">
                                                    ✓ Taken
                                                </span>

                                            </div>
                                        )
                                    )}

                                </div>

                            </div>

                        </div>
                    )}

                </div>
            </section>

            {schedulePendingDeletion && (
                <div
                    className="medicine-delete-modal-backdrop"
                    role="presentation"
                    onMouseDown={(event) => {
                        if (event.target === event.currentTarget && !deletingMedicineId) {
                            setSchedulePendingDeletion(null);
                        }
                    }}
                >
                    <section
                        className="medicine-delete-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="delete-medicine-title"
                        aria-describedby="delete-medicine-description"
                    >
                        <div className="medicine-delete-modal__icon" aria-hidden="true">
                            🗑
                        </div>
                        <p className="medicine-delete-modal__eyebrow">Medication schedule</p>
                        <h2 id="delete-medicine-title">Remove medicine?</h2>
                        <p id="delete-medicine-description">
                            Remove <strong>{schedulePendingDeletion.medicine_name}</strong> from your active schedule?
                            Its reminders will stop, but your medication history will stay available.
                        </p>
                        <div className="medicine-delete-modal__actions">
                            <button
                                type="button"
                                className="medicine-delete-modal__cancel"
                                onClick={() => setSchedulePendingDeletion(null)}
                                disabled={Boolean(deletingMedicineId)}
                            >
                                Keep medicine
                            </button>
                            <button
                                type="button"
                                className="medicine-delete-modal__confirm"
                                onClick={confirmDeleteMedicine}
                                disabled={Boolean(deletingMedicineId)}
                            >
                                {deletingMedicineId ? "Removing..." : "Remove medicine"}
                            </button>
                        </div>
                    </section>
                </div>
            )}
        </div>
    );
}

export default PublicDashboard;
