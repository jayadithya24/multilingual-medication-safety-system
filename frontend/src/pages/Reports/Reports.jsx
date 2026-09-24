import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../services/api";
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
  useEffect(() => {
    const controller = new AbortController();
    api.get("/doctor/medication-history", { signal: controller.signal })
      .then(response => { if (!controller.signal.aborted) setHistory(response.data?.history || []); })
      .catch(err => { if (!controller.signal.aborted) setError(err.response?.data?.detail || "Unable to load medication history. Please retry."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [refresh]);

  const patients = [...new Set(history.map(item => item.patient_username).filter(Boolean))].sort();
  const records = patient ? history.filter(item => item.patient_username === patient) : history;
  const medicines = new Set(records.map(item => item.medicine_name).filter(Boolean));
  const reload = () => { setLoading(true); setError(""); setRefresh(value => value + 1); };

  return <div className="doctor-reports">
    <header className="doctor-reports__header">
      <div><p className="doctor-reports__kicker">PATIENT MEDICATION HISTORY</p><h1>Reports</h1><p>Review medication-taking records shared by patients who have approved your access.</p></div>
      <button type="button" onClick={reload} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
    </header>
    {loading ? <p role="status" className="doctor-reports__empty">Loading medication history…</p> : error ? <div role="alert" className="doctor-reports__error"><h2>History could not be loaded</h2><p>{error}</p><button onClick={reload}>Retry</button></div> : <>
      <section className="doctor-reports__summary" aria-label="Medication history summary">
        <article><span>Recorded doses</span><strong>{records.length}</strong><p>Medication-taking entries</p></article>
        <article><span>Medicines recorded</span><strong>{medicines.size}</strong><p>Distinct medicines in this view</p></article>
        <article><span>Patients with history</span><strong>{new Set(records.map(item => item.patient_username).filter(Boolean)).size}</strong><p>Within your approved access</p></article>
      </section>
      <section className="doctor-reports__history">
        <div className="doctor-reports__toolbar"><div><h2>Medication history</h2><p>Patient-recorded activity. Times are shown in your local timezone.</p></div>
          {patients.length > 0 && <label>Patient<select aria-label="Filter history by patient" value={patient} onChange={event => setPatient(event.target.value)}><option value="">All accessible patients</option>{patients.map(name => <option key={name}>{name}</option>)}</select></label>}
        </div>
        {records.length ? <div className="doctor-reports__table"><table><thead><tr><th>Medicine</th><th>Patient</th><th>Dosage</th><th>Scheduled time</th><th>Recorded as taken</th></tr></thead><tbody>{records.map((record, index) => <tr key={record.history_id || index}><td><strong>{record.medicine_name || "Not recorded"}</strong></td><td>{record.patient_username || "Not recorded"}</td><td>{record.dosage || "Not recorded"}</td><td>{record.scheduled_time || "Not recorded"}</td><td>{formatDate(record.taken_at)}</td></tr>)}</tbody></table></div> : <div className="doctor-reports__empty"><span className="doctor-reports__empty-icon" aria-hidden="true">☷</span><h3>No medication history to display</h3><p>Records appear after a patient grants access and marks a scheduled medicine as taken.</p><Link to="/doctor-patients">View patients and access requests →</Link></div>}
      </section>
    </>}
  </div>;
}
