import { useMemo } from "react";

function Reports() {
    const reportSummary = useMemo(
        () => [
            {
                label: "Recent medication checks",
                value: "0",
                detail: "No activity recorded yet.",
            },
            {
                label: "Safety alerts",
                value: "0",
                detail: "No critical interactions flagged.",
            },
            {
                label: "Uploaded records",
                value: "0",
                detail: "Prescription history is empty.",
            },
        ],
        []
    );

    return (
        <div style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
            <section>
                <p style={{ margin: 0, textTransform: "uppercase", letterSpacing: "0.12em", color: "#4b5563" }}>
                    Clinical Reports
                </p>
                <h1 style={{ margin: "0.5rem 0 0.5rem" }}>Reports</h1>
                <p style={{ margin: 0, color: "#4b5563" }}>
                    Review medication summaries and safety history when records are available.
                </p>
            </section>

            <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginTop: "2rem" }}>
                {reportSummary.map((item) => (
                    <article
                        key={item.label}
                        style={{
                            background: "#f9fafb",
                            border: "1px solid #e5e7eb",
                            borderRadius: 12,
                            padding: "1.25rem",
                        }}
                    >
                        <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>{item.label}</p>
                        <h2 style={{ margin: "0.75rem 0", fontSize: 32 }}>{item.value}</h2>
                        <p style={{ margin: 0, color: "#4b5563" }}>{item.detail}</p>
                    </article>
                ))}
            </section>
        </div>
    );
}

export default Reports;
