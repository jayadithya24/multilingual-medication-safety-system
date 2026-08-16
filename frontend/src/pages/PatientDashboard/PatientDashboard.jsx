import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
    getPatientSchedule,
    markMedicineAsTaken,
    getMedicationHistory,
} from "../../services/patientScheduleService";

import "./PatientDashboard.css";

function PatientDashboard() {
    const navigate = useNavigate();
    const [schedules, setSchedules] = useState([]);
    const [history, setHistory] = useState([]);

    const [loading, setLoading] = useState(true);
    const [historyLoading, setHistoryLoading] = useState(false);

    const [error, setError] = useState("");
    const [actionLoading, setActionLoading] = useState("");

    const loadSchedule = async () => {
        try {
            setLoading(true);
            setError("");

            const response = await getPatientSchedule();

            setSchedules(response.schedules || []);
        } catch (error) {
            console.error("Schedule loading error:", error);

            setError(
                error?.response?.data?.detail ||
                "Unable to load your medication schedule."
            );
        } finally {
            setLoading(false);
        }
    };

    const loadHistory = async () => {
        try {
            setHistoryLoading(true);

            const response = await getMedicationHistory();

            setHistory(response.history || []);
        } catch (error) {
            console.error("History loading error:", error);
        } finally {
            setHistoryLoading(false);
        }
    };

    useEffect(() => {
        loadSchedule();
        loadHistory();
    }, []);

    const handleMarkAsTaken = async (scheduleId) => {
        try {
            setActionLoading(scheduleId);
            setError("");

            await markMedicineAsTaken(scheduleId);

            // Refresh both schedule and history
            await Promise.all([
                loadSchedule(),
                loadHistory(),
            ]);

        } catch (error) {
            console.error("Mark as taken error:", error);

            setError(
                error?.response?.data?.detail ||
                "Unable to mark medicine as taken."
            );
        } finally {
            setActionLoading("");
        }
    };

    return (
        <div className="patient-dashboard">
            <div className="patient-dashboard-shell">

                {/* Header */}
               <header className="patient-dashboard-header">

    <div>
        <p className="patient-dashboard-kicker">
            Patient Portal
        </p>

        <h1>My Medication Dashboard</h1>

        <p>
            Manage your medicine schedule and track your
            medication history.
        </p>
    </div>

    <div className="patient-dashboard-actions">

        <button
            type="button"
            className="prescription-button"
            onClick={() => navigate("/prescription")}
        >
            + Add Prescription
        </button>

        <button
            type="button"
            className="refresh-button"
            onClick={() => {
                loadSchedule();
                loadHistory();
            }}
        >
            Refresh
        </button>

    </div>

</header>
                {error && (
                    <div className="patient-dashboard-error">
                        {error}
                    </div>
                )}

                {/* Schedule */}
                <section className="dashboard-section">

                    <div className="dashboard-section-header">
                        <div>
                            <h2>Medicine Schedule</h2>
                            <p>
                                Your currently scheduled medicines.
                            </p>
                        </div>
                    </div>

                    {loading ? (
                        <div className="dashboard-loading">
                            Loading your medicine schedule...
                        </div>
                    ) : schedules.length === 0 ? (
                        <div className="dashboard-empty">
                            <h3>No medicines scheduled</h3>
                            <p>
                                You currently don't have any medicines
                                in your schedule.
                            </p>
                        </div>
                    ) : (
                        <div className="schedule-grid">

                            {schedules.map((schedule) => (
                                <div
                                    className={`schedule-card ${
                                        schedule.status === "taken"
                                            ? "schedule-card-taken"
                                            : ""
                                    }`}
                                    key={schedule.schedule_id}
                                >

                                    <div className="schedule-card-top">

                                        <div>
                                            <h3>
                                                {schedule.medicine_name}
                                            </h3>

                                            <p className="medicine-dosage">
                                                {schedule.dosage}
                                            </p>
                                        </div>

                                        <span
                                            className={`schedule-status ${
                                                schedule.status === "taken"
                                                    ? "status-taken"
                                                    : "status-pending"
                                            }`}
                                        >
                                            {schedule.status === "taken"
                                                ? "Taken"
                                                : "Pending"}
                                        </span>

                                    </div>

                                    <div className="schedule-details">

                                        <div>
                                            <span>Time</span>
                                            <strong>
                                                {schedule.scheduled_time}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>Frequency</span>
                                            <strong>
                                                {schedule.frequency}
                                            </strong>
                                        </div>

                                        {schedule.disease && (
                                            <div>
                                                <span>Disease</span>
                                                <strong>
                                                    {schedule.disease}
                                                </strong>
                                            </div>
                                        )}

                                    </div>

                                    {schedule.status !== "taken" && (
                                        <button
                                            type="button"
                                            className="taken-button"
                                            disabled={
                                                actionLoading ===
                                                schedule.schedule_id
                                            }
                                            onClick={() =>
                                                handleMarkAsTaken(
                                                    schedule.schedule_id
                                                )
                                            }
                                        >
                                            {actionLoading ===
                                            schedule.schedule_id
                                                ? "Updating..."
                                                : "✓ Mark as Taken"}
                                        </button>
                                    )}

                                    {schedule.status === "taken" && (
                                        <div className="taken-message">
                                            ✓ Medicine marked as taken
                                        </div>
                                    )}

                                </div>
                            ))}

                        </div>
                    )}

                </section>

                {/* History */}
                <section className="dashboard-section">

                    <div className="dashboard-section-header">
                        <div>
                            <h2>Medication History</h2>
                            <p>
                                Medicines that you have marked as taken.
                            </p>
                        </div>
                    </div>

                    {historyLoading ? (
                        <div className="dashboard-loading">
                            Loading medication history...
                        </div>
                    ) : history.length === 0 ? (
                        <div className="dashboard-empty">
                            <h3>No medication history</h3>
                            <p>
                                Your taken medicines will appear here.
                            </p>
                        </div>
                    ) : (
                        <div className="history-list">

                            {history.map((record) => (
                                <div
                                    className="history-card"
                                    key={record.history_id}
                                >

                                    <div className="history-main">
                                        <h3>
                                            {record.medicine_name}
                                        </h3>

                                        <p>
                                            {record.dosage}
                                        </p>
                                    </div>

                                    <div className="history-info">
                                        <span>
                                            Scheduled:{" "}
                                            {record.scheduled_time}
                                        </span>

                                        <span>
                                            Taken:{" "}
                                            {record.taken_at
                                                ? new Date(
                                                      record.taken_at
                                                  ).toLocaleString()
                                                : "-"}
                                        </span>
                                    </div>

                                    <span className="history-status">
                                        ✓ Taken
                                    </span>

                                </div>
                            ))}

                        </div>
                    )}

                </section>

            </div>
        </div>
    );
}

export default PatientDashboard;