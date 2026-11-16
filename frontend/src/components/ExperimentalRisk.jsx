import { useEffect, useState } from "react";
import api from "../services/api";

const labels = { gender: "Gender", conditions: "Condition", kidney_function: "Kidney function", liver_function: "Liver function", bmi_category: "BMI category" };

export default function ExperimentalRisk({ drug1, drug2 }) {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");
  const [values, setValues] = useState({ age: "", n_drugs: "" });
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    api.get("/ml/model-info", { timeout: 15000 }).then(({ data }) => {
      if (active) setInfo(data);
    }).catch(() => { if (active) setError("The experimental model is unavailable. Reference checking still works."); });
    return () => { active = false; };
  }, []);
  const options = info?.categorical_options || {};
  const supported = options.drug_1?.includes(drug1.toLowerCase()) && options.drug_2?.includes(drug2.toLowerCase());
  async function predict(event) {
    event.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try {
      const { data } = await api.post("/ml/risk-predict", { ...values, age: Number(values.age), n_drugs: Number(values.n_drugs), drug_1: drug1, drug_2: drug2 }, { timeout: 20000 });
      setResult(data);
    } catch (failure) {
      const detail = failure.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "The model could not evaluate these inputs.");
    } finally { setBusy(false); }
  }
  return <details className="experimental-risk">
    <summary>Experimental ML comparison</summary>
    <p>This research model learns severity labels from synthetic patient records. It does not establish clinical risk or replace the interaction evidence above.</p>
    {info && <>
      <p><strong>{info.algorithm}, {info.trees} trees.</strong> {info.preprocessing}</p>
      {!supported ? <p role="status">This pair is outside the model's training vocabulary. The 100-medicine reference catalog is larger than the ML training scope.</p> :
        <form className="interaction-form" onSubmit={predict}>
          <label className="interaction-field">Age<input aria-label="ML age" type="number" min="0" max="120" required value={values.age} onChange={e => { setValues({ ...values, age: e.target.value }); setResult(null); }} /></label>
          <label className="interaction-field">Number of medicines<input aria-label="ML medicine count" type="number" min="2" required value={values.n_drugs} onChange={e => { setValues({ ...values, n_drugs: e.target.value }); setResult(null); }} /></label>
          {Object.entries(labels).map(([field, label]) => <label className="interaction-field" key={field}>{label}<select aria-label={`ML ${label}`} required value={values[field] || ""} onChange={e => { setValues({ ...values, [field]: e.target.value }); setResult(null); }}><option value="">Select {label.toLowerCase()}</option>{options[field]?.map(value => <option key={value}>{value}</option>)}</select></label>)}
          <button className="interaction-button" disabled={busy} type="submit">{busy ? "Evaluating…" : "Run experimental model"}</button>
        </form>}
    </>}
    {error && <p role="alert">{error}</p>}
    {result && <div role="status"><h3>Experimental label: {result.risk_level}</h3><p>{result.interpretation}</p><ul>{Object.entries(result.probabilities).map(([label, probability]) => <li key={label}>{label}: {(probability * 100).toFixed(1)}% model probability</li>)}</ul></div>}
  </details>;
}
