import { useEffect, useMemo, useState } from "react";
import Loading from "../../components/Loading/Loading";
import { checkDrugInteraction } from "../../services/interactionService";
import { fetchMedicines } from "../../services/medicineService";
import "./DrugInteraction.css";

function DrugInteraction() {
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

    if (severity === "low") return "interaction-card--low";
    if (severity === "moderate") return "interaction-card--moderate";
    if (severity === "high") return "interaction-card--high";
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

      const response = await checkDrugInteraction(drug1.trim(), drug2.trim());
      setResult(response);
    } catch (checkError) {
      console.error(checkError);
      setError("Unable to check drug interaction right now.");
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
            Select medicines from the dataset or type to search, then compare them in one click.
          </p>
        </div>

        <div className="interaction-panel">
          <div className="interaction-form">
            <label className="interaction-field">
              <span>Medicine 1</span>
              <input
                type="text"
                list="medicine-options"
                value={drug1}
                onChange={(event) => setDrug1(event.target.value)}
                placeholder="Start typing a medicine name"
              />
            </label>

            <label className="interaction-field">
              <span>Medicine 2</span>
              <input
                type="text"
                list="medicine-options"
                value={drug2}
                onChange={(event) => setDrug2(event.target.value)}
                placeholder="Start typing another medicine"
              />
            </label>

            <button
              className="interaction-button"
              onClick={handleCheckInteraction}
              disabled={checking || loadingMedicines}
            >
              {checking ? "Checking..." : "Check Interaction"}
            </button>
          </div>

          {loadingMedicines && <Loading />}

          {error && <div className="interaction-error">{error}</div>}

          <datalist id="medicine-options">
            {medicineNames.map((medicine) => (
              <option key={medicine} value={medicine} />
            ))}
          </datalist>

          {result && (
            <div className={`interaction-card ${severityClass}`.trim()}>
              {interaction ? (
                <>
                  <div className="interaction-card__header">
                    <div>
                      <p className="interaction-card__label">Interaction Severity</p>
                      <h2>{interaction.severity}</h2>
                    </div>
                    <span className={`interaction-pill interaction-pill--${interaction.severity.toLowerCase()}`}>
                      {interaction.severity}
                    </span>
                  </div>

                  <div className="interaction-card__body">
                    <div className="interaction-card__block">
                      <h3>Description</h3>
                      <p>{interaction.description}</p>
                    </div>

                    <div className="interaction-card__block">
                      <h3>Recommendation</h3>
                      <p>{interaction.recommendation}</p>
                    </div>
                  </div>
                </>
              ) : isNotFound ? (
                <div className="interaction-card__empty">
                  <h2>No known interaction found</h2>
                  <p>
                    The selected medicines are not listed as interacting in the current dataset.
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default DrugInteraction;