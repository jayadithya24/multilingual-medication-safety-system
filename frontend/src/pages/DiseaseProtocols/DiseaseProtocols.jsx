import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    fetchDiseases,
    fetchDrugsForDisease,
} from "../../services/neo4jService";
import clinicalSources from "../../data/clinicalSources.json";
import ClinicalSources from "./ClinicalSources";
import DiseaseProtocolSummary from "./DiseaseProtocolSummary";
import LanguageSelector from "../../components/LanguageSelector/LanguageSelector";

import "./DiseaseProtocols.css";

function matchClinicalEntry(diseaseName) {
    if (!diseaseName) {
        return null;
    }

    const selected = diseaseName.trim().toLowerCase();

    return clinicalSources.find(
        (entry) => entry.disease.trim().toLowerCase() === selected
    ) || null;
}

const SELECTED_DISEASE_KEY = "mmss-clinical-selected-disease";

function DiseaseProtocols() {
    const location = useLocation();
    const navigate = useNavigate();
    const [lang, setLang] = useState("en");

    const activeTab = location.pathname.includes("clinical-insights")
        ? "insights"
        : "protocols";

    const [diseases, setDiseases] = useState([]);
    const [selectedDisease, setSelectedDisease] = useState(
        () => sessionStorage.getItem(SELECTED_DISEASE_KEY) || ""
    );
    const [drugs, setDrugs] = useState([]);

    const [loadingDiseases, setLoadingDiseases] = useState(true);
    const [loadingDrugs, setLoadingDrugs] = useState(false);

    const [error, setError] = useState("");

    const clinicalEntry = useMemo(
        () => matchClinicalEntry(selectedDisease),
        [selectedDisease]
    );

    useEffect(() => {
        let active = true;
        const loadDiseases = async () => {
            try {
                setLoadingDiseases(true);
                setError("");

                const data = await fetchDiseases(lang);

                if (active) setDiseases(data.diseases || []);
            } catch (err) {
                console.error(err);
                if (active) setError("Unable to load disease list.");
            } finally {
                if (active) setLoadingDiseases(false);
            }
        };

        loadDiseases();
        return () => { active = false; };
    }, [lang]);

    useEffect(() => {
        if (!selectedDisease) {
            return undefined;
        }

        sessionStorage.setItem(SELECTED_DISEASE_KEY, selectedDisease);

        let active = true;

        const loadDrugs = async () => {
            try {
                setLoadingDrugs(true);
                const data = await fetchDrugsForDisease(selectedDisease, lang);
                if (active) {
                    setDrugs(data.drugs || []);
                }
            } catch (err) {
                console.error(err);
                if (active) {
                    setError("Unable to load medicines for this disease.");
                }
            } finally {
                if (active) {
                    setLoadingDrugs(false);
                }
            }
        };

        loadDrugs();

        return () => {
            active = false;
        };
    }, [selectedDisease, lang]);

    const handleDiseaseChange = (event) => {
        const disease = event.target.value;

        setSelectedDisease(disease);
        setDrugs([]);
        setLoadingDrugs(Boolean(disease));
        setError("");

        if (!disease) {
            sessionStorage.removeItem(SELECTED_DISEASE_KEY);
        }
    };

    return (
        <div className="disease-protocols">

            <section className="disease-protocols__hero">
                <p className="disease-protocols__kicker">
                    CLINICAL REFERENCE
                </p>

                <h1>
                    {activeTab === "insights"
                        ? "Clinical Insights"
                        : "Disease Protocols"}
                </h1>

                <p>
                    {activeTab === "insights"
                        ? "Review the disease protocol summary together with curated sources already used in the MMSS reference list."
                        : "Review 100 medicines across 10 diseases in English, Kannada or Tulu."}
                </p>
            </section>

            <div className="disease-protocols__tabs" role="tablist" aria-label="Clinical reference views">
                <button
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "protocols"}
                    className={activeTab === "protocols" ? "is-active" : ""}
                    onClick={() => navigate("/disease-protocols")}
                >
                    Disease Protocols
                </button>
                <button
                    type="button"
                    role="tab"
                    aria-selected={activeTab === "insights"}
                    className={activeTab === "insights" ? "is-active" : ""}
                    onClick={() => navigate("/clinical-insights")}
                >
                    Clinical Insights
                </button>
            </div>

            <section className="disease-protocols__panel">
                <LanguageSelector selectedLanguage={lang} onLanguageChange={(value) => {
                    setLang(value);
                    setSelectedDisease("");
                    setDiseases([]);
                    setDrugs([]);
                    setLoadingDrugs(false);
                    sessionStorage.removeItem(SELECTED_DISEASE_KEY);
                }} />
                <label htmlFor="disease-select">
                    Select Disease
                </label>

                <select
                    id="disease-select"
                    value={selectedDisease}
                    onChange={handleDiseaseChange}
                    disabled={loadingDiseases}
                >
                    <option value="">
                        {loadingDiseases
                            ? "Loading diseases..."
                            : "Select a disease"}
                    </option>

                    {diseases.map((disease) => (
                        <option
                            key={disease}
                            value={disease}
                        >
                            {disease}
                        </option>
                    ))}
                </select>
            </section>

            {error && (
                <div className="disease-protocols__error">
                    {error}
                </div>
            )}

            {selectedDisease && (
                <>
                    <DiseaseProtocolSummary
                        selectedDisease={selectedDisease}
                        drugs={drugs}
                        loadingDrugs={loadingDrugs}
                        compact={activeTab === "insights"}
                    />

                    {activeTab === "insights" && (
                        <ClinicalSources entry={clinicalEntry} />
                    )}
                </>
            )}

        </div>
    );
}

export default DiseaseProtocols;
