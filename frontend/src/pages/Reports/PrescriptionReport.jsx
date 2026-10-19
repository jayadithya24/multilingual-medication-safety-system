
const value = item => item === null || item === undefined || item === "" ? "Not recorded" : String(item);
const date = item => item && !Number.isNaN(new Date(item).getTime()) ? new Date(item).toLocaleString() : "Not recorded";

export function PrescriptionReport({ report }) {
  const patient = report.patient;
  return <article className="prescription-report">
    <h2>Prescription report</h2>
    <p>Generated: {date(report.generated_at)} · Prepared for: {report.doctor || "Patient copy"}</p>
    <h3>{value(patient.full_name)} ({patient.username})</h3>
    <p>Patient ID: {value(patient.patient_id)} · Age: {value(patient.age)} · Gender: {value(patient.gender)}</p>
    <p><strong>Medical condition:</strong> {value(patient.medical_condition)}</p>
    <p>Patient-entered prescription information. Includes active and removed records. Original prescription documents are not stored in this report.</p>
    <h3>Prescription details ({report.prescriptions.length})</h3>
    {!report.prescriptions.length && <p>No saved prescription details.</p>}
    {report.prescriptions.map((medicine, index) => <section key={medicine.schedule_id || index} className="prescription-report__medicine">
      <h3>{value(medicine.medicine_name)}</h3>
      <dl>{[
        ["Record ID", medicine.schedule_id], ["Dosage", medicine.dosage],
        ["Frequency", medicine.frequency], ["Instructions", medicine.instructions],
        ["Scheduled times", medicine.scheduled_times?.join(", ") || medicine.scheduled_time],
        ["Status", medicine.status || (medicine.is_active === false ? "inactive" : null)],
        ["Reminders", medicine.reminder_enabled === undefined ? null : medicine.reminder_enabled ? "Enabled" : "Disabled"],
        ["Created", date(medicine.created_at)], ["Removed", date(medicine.removed_at)],
        ["Last taken", date(medicine.last_taken_at)],
      ].map(([label, content]) => <div key={label}><dt>{label}</dt><dd>{value(content)}</dd></div>)}</dl>
    </section>)}
    <h3>Medication-taking history ({report.history.length})</h3>
    {report.history.length ? <div className="doctor-reports__table"><table><thead><tr><th>Medicine</th><th>Dosage</th><th>Scheduled time</th><th>Recorded as taken</th></tr></thead><tbody>
      {report.history.map((record, index) => <tr key={record.history_id || index}><td>{value(record.medicine_name)}</td><td>{value(record.dosage)}</td><td>{value(record.scheduled_time)}</td><td>{date(record.taken_at)}</td></tr>)}
    </tbody></table></div> : <p>No doses recorded as taken.</p>}
  </article>;
}
