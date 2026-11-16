import { useState } from "react";
import api from "../services/api";

export default function DDInterPrediction({ drug1, drug2 }) {
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function predict() {
    setBusy(true); setError(""); setResult(null);
    try {
      const { data } = await api.post("/ml/ddinter/predict", { drug1, drug2 });
      setResult(data);
    } catch {
      setError("The DDInter research model is unavailable. Reference checking remains available.");
    } finally { setBusy(false); }
  }
  return <section className="experimental-risk" aria-label="DDInter ML prediction">
    <h2>ML prediction trained on DDInter</h2>
    <p>Logistic regression learns drug-associated severity patterns from documented interaction labels. It uses the two drug identities, without patient factors or interaction text. This research model has not been clinically validated.</p>
    <p>Source labels are Minor, Moderate and Major; they are separate from the older project ratings above. Unknown pairs and unsupported medicines receive no prediction.</p>
    <button className="interaction-button" onClick={predict} disabled={busy}>{busy ? "Predicting…" : "Predict with DDInter model"}</button>
    {error && <p role="alert">{error}</p>}
    {result && <div role="status">
      <h3>{result.status === "predicted" ? `Predicted severity: ${result.predicted_severity}` : "Insufficient evidence for a prediction"}</h3>
      {result.reason && <p>{result.reason}</p>}
      {result.documented_severity && <p>DDInter recorded label: <strong>{result.documented_severity}</strong>. {result.seen_during_training ? "This pair was used in training; this prediction is not an independent test." : `This pair belongs to the ${result.evaluation_partition} split and was excluded from training.`}</p>}
      {result.model_scores && <ul>{Object.entries(result.model_scores).map(([label, score]) => <li key={label}>{label}: {(score * 100).toFixed(1)}% model score</li>)}</ul>}
      <p>{result.interpretation} Model scores are not calibrated clinical probabilities.</p>
    </div>}
    <p><a href="https://ddinter.scbdd.com/" target="_blank" rel="noreferrer">DDInter</a> · Data: CC BY-NC-SA 4.0 · Noncommercial academic use.</p>
  </section>;
}
