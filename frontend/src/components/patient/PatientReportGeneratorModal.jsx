import { useEffect, useState } from "react";
import { getPatientProfile } from "../../services/patientService";
import { fetchPatientSchedule, fetchRemovedPatientSchedules, fetchMedicationHistory } from "../../services/patientScheduleService";
import { PrescriptionReport } from "../../pages/Reports/PrescriptionReport";
import { downloadReport, printReport } from "../../pages/Reports/reportExport";
import "./PatientReportGeneratorModal.css";

export default function PatientReportGeneratorModal({ onClose }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([getPatientProfile(), fetchPatientSchedule(), fetchRemovedPatientSchedules(), fetchMedicationHistory()])
      .then(([profile, current, removed, history]) => {
        if (active) setReport({ generated_at: new Date().toISOString(), doctor: "Patient copy", patient: profile.profile,
          prescriptions: [...(current.schedules || []), ...(removed.schedules || [])], history: history.history || [] });
      }).catch(() => { if (active) setError("Your saved records could not be loaded. Close this report and retry."); });
    return () => { active = false; };
  }, []);
  return <div className="report-modal-backdrop" onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="report-modal" role="dialog" aria-modal="true" aria-labelledby="patient-report-title">
      <header className="report-modal__header"><h2 id="patient-report-title">My medication report</h2><button type="button" onClick={onClose} aria-label="Close report">Close</button></header>
      <div className="report-modal__body">
        <p>This report uses your saved profile, prescriptions and dose logs. Download it or print it to share. Doctors can access your saved records only after you approve their access request.</p>
        {error && <p role="alert">{error}</p>}
        {!error && !report && <p role="status">Loading saved records…</p>}
        {report && <><PrescriptionReport report={report} /><footer className="report-modal__footer">
          <button type="button" className="report-btn" onClick={() => downloadReport(report)}>Download report (HTML)</button>
          <button type="button" className="report-btn" onClick={() => printReport(report)}>Print / Save as PDF</button>
        </footer></>}
      </div>
    </section>
  </div>;
}
