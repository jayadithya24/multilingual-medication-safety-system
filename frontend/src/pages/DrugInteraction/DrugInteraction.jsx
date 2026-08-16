import { useEffect, useMemo, useState } from "react";
import Loading from "../../components/Loading/Loading";
import { checkDrugInteraction } from "../../services/interactionService";
import { fetchMedicines } from "../../services/medicineService";
import { loginWithPassword } from "../../services/authService";
import { getStoredToken } from "../../services/api";
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
  const [username, setUsername] = useState("doctor");
  const [password, setPassword] = useState("secret");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getStoredToken()));

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

  useEffect(() => {
    setIsAuthenticated(Boolean(getStoredToken()));
  }, []);

  const severityClass = useMemo(() => {
    const severity = result?.interaction?.severity?.toLowerCase();

    if (severity === "low") return "interaction-card--low";
    if (severity === "moderate") return "interaction-card--moderate";
    if (severity === "high") return "interaction-card--high";
    return "";
  }, [result]);

  const handleCheckInteraction = async () => {
    if (!isAuthenticated) {
      setError("Please sign in as a doctor before checking interactions.");
      return;
    }

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

  const handleLogin = async () => {
    try {
      setAuthLoading(true);
      setAuthError("");
      await loginWithPassword(username.trim(), password);
      setIsAuthenticated(true);
    } catch (loginError) {
      console.error(loginError);
      setAuthError(loginError?.response?.data?.detail || "Doctor login failed.");
    } finally {
      setAuthLoading(false);
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
          {!isAuthenticated ? (
            <div className="interaction-auth">
              <h2>Doctor Sign In</h2>
              <p>Sign in to enable interaction checking.</p>

              <label className="interaction-field">
                <span>Username</span>
                <input
                  type="text"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="doctor"
                />
              </label>

              <label className="interaction-field">
                <span>Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="secret"
                />
              </label>

              <button className="interaction-button" onClick={handleLogin} disabled={authLoading}>
                {authLoading ? "Signing in..." : "Sign in"}
              </button>

              {authError && <div className="interaction-error">{authError}</div>}
            </div>
          ) : (
            <div className="interaction-auth interaction-auth--signed-in">
  <div>
    <h2>Signed in as doctor</h2>
    <p>You can now check drug interactions.</p>
  </div>
</div>
          )}

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
              disabled={checking || loadingMedicines || !isAuthenticated}
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