import { useEffect, useMemo, useState } from "react";
import Loading from "../../components/Loading/Loading";
import {
  checkDrugInteraction,
  predictRisk,
} from "../../services/interactionService";
import { fetchMedicines } from "../../services/medicineService";
import { loginWithPassword } from "../../services/authService";
import { getStoredToken } from "../../services/api";
import "./DrugInteraction.css";
import InteractionGraph from "../../components/KnowledgeGraph/InteractionGraph";


function DrugInteraction() {
  const [lang] = useState("en");
  const [drug1, setDrug1] = useState("");
  const [drug2, setDrug2] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("Male");
  const [conditions, setConditions] = useState("Hypertension");
  const [kidneyFunction, setKidneyFunction] = useState("Normal");
  const [liverFunction, setLiverFunction] = useState("Normal");
  const [bmiCategory, setBmiCategory] = useState("Normal");
  const [nDrugs, setNDrugs] = useState(2);
  const [mlResult, setMlResult] = useState(null);
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

  const formatPercent = (value) => {
    const numericValue = Number(value);

    if (Number.isNaN(numericValue)) return "N/A";

    return `${(numericValue * 100).toFixed(1)}%`;
  };

  const handleCheckInteraction = async () => {
    if (!isAuthenticated) {
      setError("Please sign in as a doctor before checking interactions.");
      return;
    }

    const trimmedDrug1 = drug1.trim();
    const trimmedDrug2 = drug2.trim();
    const patientAge = Number(age);
    const currentMedicineCount = Number(nDrugs);

    if (!trimmedDrug1 || !trimmedDrug2) {
      setError("Please select or enter two medicines.");
      return;
    }

    if (!age || !Number.isFinite(patientAge) || patientAge < 0 || patientAge > 120) {
      setError("Please enter a valid patient age.");
      return;
    }

    if (
      !nDrugs ||
      !Number.isFinite(currentMedicineCount) ||
      currentMedicineCount < 1
    ) {
      setError("Please enter a valid number of current medicines.");
      return;
    }

    try {
      setChecking(true);
      setError("");
      setResult(null);
      setMlResult(null);

      const response = await checkDrugInteraction(
        trimmedDrug1,
        trimmedDrug2,
        lang
      );

      setResult(response);

      try {
        const riskResponse = await predictRisk({
          age: patientAge,
          gender,
          conditions,
          kidney_function: kidneyFunction,
          liver_function: liverFunction,
          bmi_category: bmiCategory,
          n_drugs: currentMedicineCount,
          drug_1: trimmedDrug1,
          drug_2: trimmedDrug2,
        });

        setMlResult(riskResponse);
      } catch (riskError) {
        console.error(riskError);
        setError("Interaction checked, but ML risk prediction is unavailable right now.");
      }
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
  <span>Age</span>
  <input
    type="number"
    value={age}
    onChange={(event) => setAge(event.target.value)}
    placeholder="Enter patient age"
  />
</label>

<label className="interaction-field">
  <span>Gender</span>
  <select value={gender} onChange={(event) => setGender(event.target.value)}>
    <option value="Male">Male</option>
    <option value="Female">Female</option>
  </select>
</label>

<label className="interaction-field">
  <span>Condition</span>
  <select value={conditions} onChange={(event) => setConditions(event.target.value)}>
    <option value="Hypertension">Hypertension</option>
    <option value="Arthritis">Arthritis</option>
    <option value="Diabetes">Diabetes</option>
  </select>
</label>

<label className="interaction-field">
  <span>Kidney Function</span>
  <select
    value={kidneyFunction}
    onChange={(event) => setKidneyFunction(event.target.value)}
  >
    <option value="Normal">Normal</option>
    <option value="Mild Impairment">Mild Impairment</option>
    <option value="Moderate Impairment">Moderate Impairment</option>
    <option value="Severe Impairment">Severe Impairment</option>
  </select>
</label>

<label className="interaction-field">
  <span>Liver Function</span>
  <select
    value={liverFunction}
    onChange={(event) => setLiverFunction(event.target.value)}
  >
    <option value="Normal">Normal</option>
    <option value="Impaired">Impaired</option>
  </select>
</label>

<label className="interaction-field">
  <span>BMI Category</span>
  <select
    value={bmiCategory}
    onChange={(event) => setBmiCategory(event.target.value)}
  >
    <option value="Normal">Normal</option>
    <option value="Underweight">Underweight</option>
    <option value="Overweight">Overweight</option>
    <option value="Obese">Obese</option>
  </select>
</label>

<label className="interaction-field">
  <span>Number of Current Medicines</span>
  <input
    type="number"
    min="1"
    value={nDrugs}
    onChange={(event) => setNDrugs(event.target.value)}
  />
</label>
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

          {mlResult && (
            <div className="interaction-card">
              <div className="interaction-card__header">
                <div>
                  <p className="interaction-card__label">Personalized ML Risk Prediction</p>
                  <h2>{mlResult.risk_level}</h2>
                </div>
              </div>

              <div className="interaction-card__body">
                <div className="interaction-card__block">
                  <h3>Risk Level</h3>
                  <p>{mlResult.risk_level}</p>
                </div>

                <div className="interaction-card__block">
                  <h3>Confidence</h3>
                  <p>{formatPercent(mlResult.confidence)}</p>
                </div>

                <div className="interaction-card__block">
                  <h3>Mild Probability</h3>
                  <p>{formatPercent(mlResult.probabilities?.Mild)}</p>
                </div>

                <div className="interaction-card__block">
                  <h3>Moderate Probability</h3>
                  <p>{formatPercent(mlResult.probabilities?.Moderate)}</p>
                </div>

                <div className="interaction-card__block">
                  <h3>Severe Probability</h3>
                  <p>{formatPercent(mlResult.probabilities?.Severe)}</p>
                </div>
              </div>
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
