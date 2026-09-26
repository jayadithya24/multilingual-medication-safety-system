import { useState } from "react";
import "./PatientReportGeneratorModal.css";

const mockSearchHistory = [
    {
        id: "SRCH-001",
        query: "Acarbose + Metformin drug interaction",
        date: "2026-09-20 21:30",
        type: "Drug Interaction Check",
        summary: "Checked potential gastrointestinal interaction between Acarbose and Metformin.",
    },
    {
        id: "SRCH-002",
        query: "Metformin 500mg side effects in Kannada",
        date: "2026-09-19 14:15",
        type: "Multilingual Voice Search",
        summary: "Voice query translated to Kannada detailing mild nausea precautions.",
    },
    {
        id: "SRCH-003",
        query: "Amlodipine hypertension protocol & dosage",
        date: "2026-09-18 10:45",
        type: "Medicine Reference",
        summary: "Looked up standard 5mg daily morning dosage for hypertension.",
    },
];

function PatientReportGeneratorModal({ doctorName = "Dr. Smith", onClose, onSendReport }) {
    const [selectedSearches, setSelectedSearches] = useState(["SRCH-001", "SRCH-002"]);
    const [includeMedications, setIncludeMedications] = useState(true);
    const [includeHistory, setIncludeHistory] = useState(true);
    const [patientNotes, setPatientNotes] = useState("Sharing my recent drug interaction search and daily adherence log for clinical research review.");
    const [generatedReport, setGeneratedReport] = useState(null);
    const [isSending, setIsSending] = useState(false);
    const [sentSuccess, setSentSuccess] = useState(false);

    const toggleSearch = (id) => {
        setSelectedSearches((prev) =>
            prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
        );
    };

    const handleGenerate = () => {
        const selectedItems = mockSearchHistory.filter((item) =>
            selectedSearches.includes(item.id)
        );

        const reportData = {
            reportId: `NG-RPT-${Math.floor(100000 + Math.random() * 900000)}`,
            generatedAt: new Date().toLocaleString(),
            doctorName,
            patientName: "Ramesh Kumar (PAT-DEMO-001)",
            conditions: ["Type 2 Diabetes", "Hypertension"],
            selectedSearches: selectedItems,
            medications: includeMedications
                ? [
                      { name: "Metformin", dosage: "500mg", schedule: "Twice daily with meals" },
                      { name: "Acarbose", dosage: "50mg", schedule: "Three times daily before meals" },
                      { name: "Amlodipine", dosage: "5mg", schedule: "Once daily morning" },
                  ]
                : [],
            adherenceRate: includeHistory ? "94% (Last 30 Days)" : "N/A",
            notes: patientNotes,
        };

        setGeneratedReport(reportData);
    };

    const handlePrintOrPdf = () => {
        window.print();
    };

    const handleTransmit = async () => {
        setIsSending(true);
        setTimeout(() => {
            setIsSending(false);
            setSentSuccess(true);
            if (onSendReport) {
                onSendReport(generatedReport);
            }
        }, 1200);
    };

    return (
        <div className="report-modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
            <div className="report-modal">
                <header className="report-modal__header">
                    <div>
                        <span className="report-modal__badge">CLINICAL RESEARCH CONSENT</span>
                        <h2>Generate Research Report for Doctor</h2>
                        <p>Select your medicine search history and health records to compile into an automated report for <strong>{doctorName}</strong>.</p>
                    </div>
                    <button className="report-modal__close" onClick={onClose}>×</button>
                </header>

                {!generatedReport ? (
                    <div className="report-modal__body">
                        {/* Search Selection */}
                        <section className="report-section">
                            <h3>1. Select Search History to Include</h3>
                            <p className="report-section__desc">Choose which medicine lookups or voice queries you want to share for research:</p>

                            <div className="report-search-list">
                                {mockSearchHistory.map((item) => (
                                    <label key={item.id} className={`report-search-card ${selectedSearches.includes(item.id) ? "is-selected" : ""}`}>
                                        <input
                                            type="checkbox"
                                            checked={selectedSearches.includes(item.id)}
                                            onChange={() => toggleSearch(item.id)}
                                        />
                                        <div>
                                            <strong>{item.query}</strong>
                                            <div className="report-search-card__meta">
                                                <span>{item.type}</span> • <span>{item.date}</span>
                                            </div>
                                            <p className="report-search-card__summary">{item.summary}</p>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </section>

                        {/* Medical Data Options */}
                        <section className="report-section">
                            <h3>2. Include Active Records & Adherence</h3>
                            <div className="report-options">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={includeMedications}
                                        onChange={(e) => setIncludeMedications(e.target.checked)}
                                    />
                                    <span>Include Active Prescription List</span>
                                </label>

                                <label>
                                    <input
                                        type="checkbox"
                                        checked={includeHistory}
                                        onChange={(e) => setIncludeHistory(e.target.checked)}
                                    />
                                    <span>Include Medication Adherence History & Dose Logs</span>
                                </label>
                            </div>
                        </section>

                        {/* Notes */}
                        <section className="report-section">
                            <h3>3. Additional Patient Notes for Research Survey</h3>
                            <textarea
                                className="report-textarea"
                                rows="3"
                                value={patientNotes}
                                onChange={(e) => setPatientNotes(e.target.value)}
                                placeholder="Add any comments or observations for your doctor..."
                            />
                        </section>

                        <footer className="report-modal__footer">
                            <button className="report-btn report-btn--secondary" onClick={onClose}>Cancel</button>
                            <button className="report-btn report-btn--primary" onClick={handleGenerate}>
                                Generate Automated Report →
                            </button>
                        </footer>
                    </div>
                ) : (
                    <div className="report-modal__body">
                        {sentSuccess ? (
                            <div className="report-success">
                                <div className="report-success__icon">✓</div>
                                <h3>Report Sent to {doctorName} Successfully!</h3>
                                <p>Reference ID: <strong>{generatedReport.reportId}</strong></p>
                                <p>Your doctor can now review your selected search history, medication schedule, and research feedback in their Clinical Workspace.</p>
                                <div style={{ marginTop: "20px", display: "flex", gap: "10px", justifyContent: "center" }}>
                                    <button className="report-btn report-btn--secondary" onClick={handlePrintOrPdf}>📄 Download / Print PDF</button>
                                    <button className="report-btn report-btn--primary" onClick={onClose}>Close Window</button>
                                </div>
                            </div>
                        ) : (
                            <div className="report-preview printable-area">
                                <div className="report-preview__header">
                                    <div>
                                        <h1>NeoGraphMed Clinical Research Report</h1>
                                        <p>Automated Medication Safety & Search History Summary</p>
                                    </div>
                                    <div className="report-preview__id">
                                        <strong>{generatedReport.reportId}</strong>
                                        <span>{generatedReport.generatedAt}</span>
                                    </div>
                                </div>

                                <div className="report-preview__grid">
                                    <div>
                                        <strong>PATIENT:</strong> {generatedReport.patientName}<br />
                                        <strong>CONDITIONS:</strong> {generatedReport.conditions.join(", ")}
                                    </div>
                                    <div>
                                        <strong>RECIPIENT DOCTOR:</strong> {generatedReport.doctorName}<br />
                                        <strong>ADHERENCE RATE:</strong> {generatedReport.adherenceRate}
                                    </div>
                                </div>

                                <hr className="report-divider" />

                                <h3>Selected Patient Search History</h3>
                                <table className="report-table">
                                    <thead>
                                        <tr>
                                            <th>Query / Topic</th>
                                            <th>Search Type</th>
                                            <th>Timestamp</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {generatedReport.selectedSearches.map((s) => (
                                            <tr key={s.id}>
                                                <td><strong>{s.query}</strong><br /><small>{s.summary}</small></td>
                                                <td>{s.type}</td>
                                                <td>{s.date}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>

                                {generatedReport.medications.length > 0 && (
                                    <>
                                        <h3>Active Prescription List</h3>
                                        <table className="report-table">
                                            <thead>
                                                <tr>
                                                    <th>Medicine</th>
                                                    <th>Dosage</th>
                                                    <th>Prescribed Schedule</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {generatedReport.medications.map((m, i) => (
                                                    <tr key={i}>
                                                        <td><strong>{m.name}</strong></td>
                                                        <td>{m.dosage}</td>
                                                        <td>{m.schedule}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </>
                                )}

                                <h3>Patient Observations & Notes</h3>
                                <p className="report-preview__notes">"{generatedReport.notes}"</p>

                                <footer className="report-modal__footer non-printable">
                                    <button className="report-btn report-btn--secondary" onClick={() => setGeneratedReport(null)}>← Edit Selection</button>
                                    <button className="report-btn report-btn--secondary" onClick={handlePrintOrPdf}>🖨️ Download / Print PDF</button>
                                    <button className="report-btn report-btn--primary" onClick={handleTransmit} disabled={isSending}>
                                        {isSending ? "Sending to Doctor..." : "Send Report to Doctor →"}
                                    </button>
                                </footer>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default PatientReportGeneratorModal;
