import { useEffect, useState } from "react";
import api from "../../services/api";

function Reports() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadReports = async () => {
            try {
                const response = await api.get("/doctor/medication-history");
                setHistory(response.data?.history || []);
            } catch (err) {
                setError(
                    err.response?.data?.detail ||
                    "Unable to load medication reports."
                );
            } finally {
                setLoading(false);
            }
        };

        loadReports();
    }, []);

    const completedChecks = history.filter(
        (record) =>
            String(record.status || "").toLowerCase() === "taken"
    ).length;

    const safetyAlerts = history.filter(
        (record) =>
            ["risk", "caution", "critical"].includes(
                String(record.status || "").toLowerCase()
            )
    ).length;

    const uniquePatients = new Set(
        history.map((record) => record.patient_username).filter(Boolean)
    ).size;

    if (loading) {
        return <div style={{ padding: "2rem" }}>Loading reports...</div>;
    }

    return (
        <div style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
            <section>
                <p
                    style={{
                        margin: 0,
                        textTransform: "uppercase",
                        letterSpacing: "0.12em",
                        color: "#4b5563",
                    }}
                >
                    Clinical Reports
                </p>

                <h1 style={{ margin: "0.5rem 0" }}>Reports</h1>

                <p style={{ margin: 0, color: "#4b5563" }}>
                    Medication history and safety information for patients
                    accessible to you.
                </p>
            </section>

            {error && (
                <p style={{ marginTop: "1.5rem", color: "#b91c1c" }}>
                    {error}
                </p>
            )}

            <section
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: "1rem",
                    marginTop: "2rem",
                }}
            >
                <article
                    style={{
                        background: "#f9fafb",
                        border: "1px solid #e5e7eb",
                        borderRadius: 12,
                        padding: "1.25rem",
                    }}
                >
                    <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                        Medication checks
                    </p>
                    <h2 style={{ margin: "0.75rem 0", fontSize: 32 }}>
                        {history.length}
                    </h2>
                    <p style={{ margin: 0, color: "#4b5563" }}>
                        Recorded medication history
                    </p>
                </article>

                <article
                    style={{
                        background: "#f9fafb",
                        border: "1px solid #e5e7eb",
                        borderRadius: 12,
                        padding: "1.25rem",
                    }}
                >
                    <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                        Completed checks
                    </p>
                    <h2 style={{ margin: "0.75rem 0", fontSize: 32 }}>
                        {completedChecks}
                    </h2>
                    <p style={{ margin: 0, color: "#4b5563" }}>
                        Records marked as taken
                    </p>
                </article>

                <article
                    style={{
                        background: "#f9fafb",
                        border: "1px solid #e5e7eb",
                        borderRadius: 12,
                        padding: "1.25rem",
                    }}
                >
                    <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                        Safety alerts
                    </p>
                    <h2 style={{ margin: "0.75rem 0", fontSize: 32 }}>
                        {safetyAlerts}
                    </h2>
                    <p style={{ margin: 0, color: "#4b5563" }}>
                        Records with risk-related status
                    </p>
                </article>

                <article
                    style={{
                        background: "#f9fafb",
                        border: "1px solid #e5e7eb",
                        borderRadius: 12,
                        padding: "1.25rem",
                    }}
                >
                    <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>
                        Patients
                    </p>
                    <h2 style={{ margin: "0.75rem 0", fontSize: 32 }}>
                        {uniquePatients}
                    </h2>
                    <p style={{ margin: 0, color: "#4b5563" }}>
                        Patients with recorded history
                    </p>
                </article>
            </section>

            <section style={{ marginTop: "2rem" }}>
                <h2>Medication History</h2>

                {history.length === 0 ? (
                    <p style={{ color: "#6b7280" }}>
                        No medication history is available for your accessible
                        patients.
                    </p>
                ) : (
                    <div style={{ display: "grid", gap: "1rem" }}>
                        {history.map((record, index) => (
                            <article
                                key={
                                    record.history_id ||
                                    `${record.patient_username}-${index}`
                                }
                                style={{
                                    border: "1px solid #e5e7eb",
                                    borderRadius: 12,
                                    padding: "1rem",
                                }}
                            >
                                <strong>
                                    {record.medicine_name || "Unknown medicine"}
                                </strong>

                                <p>
                                    Patient:{" "}
                                    {record.patient_username || "—"}
                                </p>

                                <p>
                                    Status: {record.status || "—"}
                                </p>

                                <p>
                                    Dosage: {record.dosage || "—"}
                                </p>

                                <p>
                                    Disease: {record.disease || "—"}
                                </p>
                            </article>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}

export default Reports;
