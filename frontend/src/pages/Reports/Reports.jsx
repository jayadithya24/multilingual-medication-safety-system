import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
import { PrescriptionReport, downloadReport, printReport } from "./PrescriptionReport";
import "./Reports.css";

function formatDate(value) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not recorded" : date.toLocaleString();
}

export default function Reports() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [patient, setPatient] = useState("");
  const [accessiblePatients, setAccessiblePatients] = useState([]);
  const [report, setReport] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [reportError, setReportError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      api.get("/doctor/medication-history", { signal: controller.signal }),
      api.get("/doctor/patients", { signal: controller.signal }),
    ])
      .then(([response, patientsResponse]) => { if (!controller.signal.aborted) {
        setHistory(response.data?.history || []);
        setAccessiblePatients((patientsResponse.data?.patients || []).filter(item => item.status === "ACCEPTED"));
      } })
      .catch(err => { if (!controller.signal.aborted) setError(err.response?.data?.detail || "Unable to load medication history. Please retry."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [refresh]);

  const patients = [...new Set([...accessiblePatients.map(item => item.username), ...history.map(item => item.patient_username)].filter(Boolean))].sort();
  const records = patient ? history.filter(item => item.patient_username === patient) : history;
  const medicines = new Set(records.map(item => item.medicine_name).filter(Boolean));
  const reload = () => { setLoading(true); setError(""); setReport(null); setRefresh(value => value + 1); };
  const generateReport = async () => {
    setGenerating(true); setReportError(""); setReport(null);
    try {
      const response = await api.get(`/doctor/patients/${encodeURIComponent(patient)}/report`);
      setReport(response.data);
    } catch (err) {
      setReportError(err.response?.data?.detail || "Unable to generate report. Please retry.");
    } finally { setGenerating(false); }
  };

  return <div className="doctor-reports">
    <header className="doctor-reports__header">
      <div><p className="doctor-reports__kicker">PATIENT PRESCRIPTIONS & HISTORY</p><h1>Reports</h1><p>Generate prescription reports for patients who have approved your access, including instructions, schedules, and medication-taking history.</p></div>
      <button type="button" onClick={reload} disabled={loading || generating}>{loading ? "Loading…" : "Refresh"}</button>
    </header>
    {loading ? <p role="status" className="doctor-reports__empty">Loading medication history…</p> : error ? <div role="alert" className="doctor-reports__error"><h2>History could not be loaded</h2><p>{error}</p><button onClick={reload}>Retry</button></div> : <>
      <section className="doctor-reports__history doctor-reports__generator">
        <div className="doctor-reports__toolbar"><div><h2>Generate prescription report</h2><p>Select one patient to preview, download, or print their complete saved prescription information.</p></div>
          <label>Patient<select aria-label="Report patient" value={patient} disabled={generating} onChange={event => { setPatient(event.target.value); setReport(null); setReportError(""); }}><option value="">Select a patient</option>{patients.map(name => <option key={name}>{name}</option>)}</select></label>
          <button onClick={generateReport} disabled={!patient || generating}>{generating ? "Generating…" : "Generate report"}</button>
        </div>
        {!patients.length && <p className="doctor-reports__notice">No approved patients available. <Link to="/doctor-patients">View access requests</Link></p>}
        {reportError && <p role="alert" className="doctor-reports__error">{reportError}</p>}
        {report && <><div className="doctor-reports__actions"><button onClick={() => downloadReport(report)}>Download report (HTML)</button><button onClick={() => printReport(report)}>Print / Save as PDF</button></div><PrescriptionReport report={report} /></>}
      </section>
      <section className="doctor-reports__summary" aria-label="Medication history summary">
        <article><span>Recorded doses</span><strong>{records.length}</strong><p>Medication-taking entries</p></article>
        <article><span>Medicines recorded</span><strong>{medicines.size}</strong><p>Distinct medicines in this view</p></article>
        <article><span>Patients with history</span><strong>{new Set(records.map(item => item.patient_username).filter(Boolean)).size}</strong><p>Within your approved access</p></article>
      </section>
      <section className="doctor-reports__history">
        <div className="doctor-reports__toolbar"><div><h2>Medication history</h2><p>Patient-recorded activity. Times are shown in your local timezone.</p></div>
          {patients.length > 0 && <label>Patient<select aria-label="Filter history by patient" value={patient} disabled={generating} onChange={event => { setPatient(event.target.value); setReport(null); setReportError(""); }}><option value="">All accessible patients</option>{patients.map(name => <option key={name}>{name}</option>)}</select></label>}
        </div>
        {records.length ? <div className="doctor-reports__table"><table><thead><tr><th>Medicine</th><th>Patient</th><th>Dosage</th><th>Scheduled time</th><th>Recorded as taken</th></tr></thead><tbody>{records.map((record, index) => <tr key={record.history_id || index}><td><strong>{record.medicine_name || "Not recorded"}</strong></td><td>{record.patient_username || "Not recorded"}</td><td>{record.dosage || "Not recorded"}</td><td>{record.scheduled_time || "Not recorded"}</td><td>{formatDate(record.taken_at)}</td></tr>)}</tbody></table></div> : <div className="doctor-reports__empty"><span className="doctor-reports__empty-icon" aria-hidden="true">☷</span><h3>No medication history to display</h3><p>Records appear after a patient grants access and marks a scheduled medicine as taken.</p><Link to="/doctor-patients">View patients and access requests →</Link></div>}
      </section>
    </>}
  </div>;
}
