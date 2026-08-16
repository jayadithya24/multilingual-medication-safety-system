import { useEffect, useState } from "react";
import "./AnalysisHistory.css";

function AnalysisHistory() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadHistory = async () => {
            try {
                setLoading(true);
                setError("");

                const token =
    localStorage.getItem("mmss_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("access_token");

                const response = await fetch(
                    "http://127.0.0.1:8000/doctor/medication-history",
                    {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${token}`,
                            "Content-Type": "application/json",
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error("Failed to load medication history");
                }

                const data = await response.json();

                setHistory(data.history || []);
            } catch (err) {
                console.error(err);
                setError("Unable to load medication history.");
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, []);

    return (
        <div className="analysis-history">

            {/* Hero */}
            <section className="analysis-history__hero">

                <p className="analysis-history__kicker">
                    MEDICATION HISTORY
                </p>

                <h1>
                    Analysis History
                </h1>

                <p>
                    Review previously recorded medication intake
                    and patient medication activity.
                </p>

            </section>


            {/* History Panel */}
            <section className="analysis-history__panel">

                <div className="analysis-history__header">

                    <div>
                        <p className="analysis-history__label">
                            RECORDED ACTIVITY
                        </p>

                        <h2>
                            Medication History
                        </h2>
                    </div>

                    <span className="analysis-history__count">
                        {history.length} records
                    </span>

                </div>


                {/* Loading */}
                {loading && (
                    <div className="analysis-history__state">
                        Loading medication history...
                    </div>
                )}


                {/* Error */}
                {!loading && error && (
                    <div className="analysis-history__error">
                        {error}
                    </div>
                )}


                {/* Empty */}
                {!loading && !error && history.length === 0 && (
                    <div className="analysis-history__state">
                        No medication history recorded yet.
                    </div>
                )}


                {/* History Records */}
                {!loading && !error && history.length > 0 && (

                    <div className="analysis-history__list">

                        {history.map((record) => (

                            <article
                                className="history-card"
                                key={record.history_id}
                            >

                                <div className="history-card__icon">
                                    💊
                                </div>


                                <div className="history-card__main">

                                    <div className="history-card__top">

                                        <div>

                                            <h3>
                                                {record.medicine_name}
                                            </h3>

                                            <p>
                                                Patient:{" "}
                                                {record.patient_username}
                                            </p>

                                        </div>

                                        <span className="history-card__status">
                                            {record.status}
                                        </span>

                                    </div>


                                    <div className="history-card__details">

                                        <div>
                                            <span>
                                                DOSAGE
                                            </span>

                                            <strong>
                                                {record.dosage || "—"}
                                            </strong>
                                        </div>


                                        <div>
                                            <span>
                                                DISEASE
                                            </span>

                                            <strong>
                                                {record.disease || "—"}
                                            </strong>
                                        </div>


                                        <div>
                                            <span>
                                                SCHEDULED
                                            </span>

                                            <strong>
                                                {record.scheduled_time || "—"}
                                            </strong>
                                        </div>


                                        <div>
                                            <span>
                                                DATE
                                            </span>

                                            <strong>
                                                {record.date || "—"}
                                            </strong>
                                        </div>

                                    </div>

                                </div>

                            </article>

                        ))}

                    </div>

                )}

            </section>

        </div>
    );
}

export default AnalysisHistory;