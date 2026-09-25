import { useEffect, useMemo, useState } from "react";
import Loading from "../../components/Loading/Loading";
import { checkDrugInteraction } from "../../services/interactionService";
import { fetchMedicines } from "../../services/medicineService";
import "./DrugInteraction.css";
import InteractionGraph from "../../components/KnowledgeGraph/InteractionGraph";


function DrugInteraction() {
  const [lang] = useState("en");
  const [drug1, setDrug1] = useState("");
  const [drug2, setDrug2] = useState("");
  const [medicineNames, setMedicineNames] = useState([]);
  const [loadingMedicines, setLoadingMedicines] = useState(true);
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let isMounted = true;

    const loadMedicines = async () => {
      try {
        setLoadingMedicines(true);
        const response = await fetchMedicines();

        if (isMounted) {
          setMedicineNames(response.medicines || []);
        }
      } catch (fetchError) {
        console.error(fetchError);
        if (isMounted) {
          setError("Unable to load medicine list.");
        }
      } finally {
        if (isMounted) {
          setLoadingMedicines(false);
        }
      }
    };

    loadMedicines();

    return () => {
      isMounted = false;
    };
  }, []);

  const severityClass = useMemo(() => {
    const severity = result?.interaction?.severity?.toLowerCase();

    if (severity === "low" || severity === "mild") return "interaction-card--low";
    if (severity === "moderate") return "interaction-card--moderate";
    if (severity === "high" || severity === "severe") return "interaction-card--high";
    if (severity === "review required") return "interaction-card--moderate";
    return "";
  }, [result]);

  const handleCheckInteraction = async () => {
    if (!drug1.trim() || !drug2.trim()) {
      setError("Please select or enter two medicines.");
      return;
    }

    try {
      setChecking(true);
      setError("");
      setResult(null);

      const response = await checkDrugInteraction(drug1.trim(), drug2.trim(), lang);
      setResult(response);
    } catch (checkError) {
      console.error(checkError);
      const detail = checkError?.response?.data?.detail;
      setError(detail || "Unable to check drug interaction right now.");
    } finally {
      setChecking(false);
    }
  };

  const interaction = result?.interaction ?? null;
  const isNotFound = result?.status === "not_found";

  return (
    <div className="drug-interaction-page">
      <section className="interaction-shell">
        <div className="interaction-hero">
          <p className="interaction-kicker">Drug Interaction Checker</p>
          <h1>Check how two medicines may interact</h1>
          <p>
            Review possible effects on the body when two medicines are taken together,
            including medicines prescribed for different conditions.
          </p>
        </div>

        <div className="interaction-panel">
          <div className="interaction-form">
            <label className="interaction-field">
              <span>Medicine 1</span>
              <select
                aria-label="Medicine 1"
                disabled={checking || loadingMedicines}
                value={drug1}
                onChange={(event) => { setDrug1(event.target.value); setResult(null); }}
              ><option value="">Select a medicine</option>{medicineNames.map(name => <option key={name} disabled={name === drug2}>{name}</option>)}</select>
            </label>

            <label className="interaction-field">
              <span>Medicine 2</span>
              <select
                aria-label="Medicine 2"
                disabled={checking || loadingMedicines}
                value={drug2}
                onChange={(event) => { setDrug2(event.target.value); setResult(null); }}
              ><option value="">Select a medicine</option>{medicineNames.map(name => <option key={name} disabled={name === drug1}>{name}</option>)}</select>
            </label>

            <button
              className="interaction-button"
              onClick={handleCheckInteraction}
              disabled={checking || loadingMedicines || !drug1 || !drug2}
            >
              {checking ? "Checking..." : "Check Interaction"}
            </button>
          </div>

          {loadingMedicines && <Loading />}

          {error && <div className="interaction-error">{error}</div>}

          {result && (
            <div className={`interaction-card ${severityClass}`.trim()}>
              {interaction ? (
                <>
                  <div className="interaction-card__header">
                    <div>
                      <p className="interaction-card__label">{interaction.drug1} + {interaction.drug2}</p>
                      <h2>{interaction.severity}</h2>
                    </div>
                    <span className={`interaction-pill interaction-pill--${interaction.severity.toLowerCase().replaceAll(" ", "-")}`}>
                      {interaction.severity}
                    </span>
                  </div>

                  <div className="interaction-card__body">
                    <div className="interaction-card__block">
                      <h3>Possible effect when taken together</h3>
                      <p>{interaction.description}</p>
                    </div>
                    <div className="interaction-card__block">
                      <h3>What needs monitoring or review</h3>
                      <p>{interaction.recommendation}</p>
                    </div>
                    <div className="interaction-card__block">
                      <h3>Severity and evidence</h3>
                      <p>{interaction.severity_basis || "Severity is a project dataset label and has not been independently clinically validated."}</p>
                      {interaction.source_severities?.length > 0 && <p>Recorded dataset ratings: {interaction.source_severities.join(", ")}.</p>}
                      {interaction.review_note && <p><strong>{interaction.review_note}</strong></p>}
                      <p>{interaction.evidence_basis || interaction.match_basis}</p>
                      {interaction.evidence_sources?.length > 0 ? <ul>{interaction.evidence_sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a></li>)}</ul> : <p>No pair-specific prescribing reference has been added for this record.</p>}
                      <p>Record source: {interaction.source === "neo4j" ? "Neo4j medication dataset" : "Local medication dataset"}.</p>
                    </div>
                  </div>
                </>
              ) : isNotFound ? (
                <div className="interaction-card__empty">
                  <h2>No interaction record found</h2>
                  <p>
                    The selected medicines are not listed as interacting in the current dataset.
                    This does not establish that taking them together is safe. Individual
                    side effects in the graph do not establish a reaction between this pair.
                  </p>
                </div>
              ) : null}
            </div>
          )}
          {/* Interaction Knowledge Graph */}

{result && drug1 && drug2 && (
    <InteractionGraph
        drug1={drug1.trim()}
        drug2={drug2.trim()}
    />
)}
        </div>
      </section>
    </div>
  );
}

export default DrugInteraction;
