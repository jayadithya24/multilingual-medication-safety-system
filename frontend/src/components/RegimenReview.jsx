import { useEffect, useState } from 'react';
import api from '../services/api';

export default function RegimenReview({ patientId }) {
  const [state, setState] = useState({});
  useEffect(() => {
    const controller = new AbortController();
    api.get(`/doctor/patients/${encodeURIComponent(patientId)}/regimen`, { signal: controller.signal })
      .then(({ data }) => setState({ data }))
      .catch(error => { if (!controller.signal.aborted) setState({ error: error.response?.data?.detail || 'Unable to load regimen review.' }); });
    return () => controller.abort();
  }, [patientId]);
  if (state.error) return <p role="alert">{state.error}</p>;
  if (!state.data) return <p role="status">Loading regimen review…</p>;
  const { coverage, interactions, adherence } = state.data;
  return <section className="patient-drug-lists__results" aria-label="Regimen review">
    <h2>Full regimen review</h2>
    <p><strong>{coverage.covered_medicines} of {coverage.total_medicines} medicines covered</strong></p>
    <p>{coverage.message}</p>
    {coverage.unsupported_medicines.length > 0 && <p>Not checked: {coverage.unsupported_medicines.join(', ')}. Brand names are not automatically converted.</p>}
    <p>Reference-pair lookup. Project severity labels are not clinically validated. This does not assess cumulative risk or drug–disease contraindications.</p>
    {interactions.length === 0 && <p>No matching interaction records. This does not establish safety.</p>}
    {interactions.map(row => <article className="regimen-interaction" key={`${row.drug1}-${row.drug2}`}>
      <h3>{row.drug1} + {row.drug2}: {row.severity}</h3>
      <p>{row.description}</p><p>{row.recommendation}</p>
      <p>{row.severity_basis}</p>
      {row.review_note && <p>{row.review_note}</p>}
      {row.evidence_sources?.length ? <ul>{row.evidence_sources.map((source, index) =>
        <li key={index}><a href={source.url} target="_blank" rel="noreferrer">{source.title || source.name || 'Prescribing reference'}</a></li>)}</ul>
        : <p>Source: project dataset, rows {row.source_rows.join(', ')}. Pair-specific external evidence needs review.</p>}
    </article>)}
    <h3>Last 28 days: taken records and unconfirmed days</h3>
    <p>{adherence.interpretation}</p>
    <p>From {adherence.from_date}; {adherence.timezone}.</p>
    <div style={{ overflowX: 'auto' }}><table className="regimen-table">
      <thead><tr><th>Medicine</th><th>Taken records</th><th>Scheduled days</th><th>Days with a record</th><th>Unconfirmed days</th></tr></thead>
      <tbody>{adherence.rows.map((row, index) => <tr key={row.schedule_id || index}>
        <th scope="row">{row.medicine_name}</th><td>{row.recorded_events}</td><td>{row.scheduled_days ?? 'Unknown'}</td>
        <td>{row.days_with_confirmation ?? 'Unknown'}</td><td>{row.unconfirmed_days ?? 'Unknown'}</td>
      </tr>)}</tbody>
    </table></div>
  </section>;
}
