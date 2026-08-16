import { useEffect, useState } from "react";
import {
    fetchDiseases,
    fetchDrugsForDisease,
} from "../../services/neo4jService";

import "./DiseaseProtocols.css";

function DiseaseProtocols() {

    const [diseases, setDiseases] = useState([]);
    const [selectedDisease, setSelectedDisease] = useState("");
    const [drugs, setDrugs] = useState([]);

    const [loadingDiseases, setLoadingDiseases] = useState(true);
    const [loadingDrugs, setLoadingDrugs] = useState(false);

    const [error, setError] = useState("");

    useEffect(() => {

        const loadDiseases = async () => {
            try {
                setLoadingDiseases(true);
                setError("");

                const data = await fetchDiseases();

                setDiseases(data.diseases || []);

            } catch (err) {
                console.error(err);
                setError("Unable to load disease list.");
            } finally {
                setLoadingDiseases(false);
            }
        };

        loadDiseases();

    }, []);


    const handleDiseaseChange = async (event) => {

        const disease = event.target.value;

        setSelectedDisease(disease);
        setDrugs([]);
        setError("");

        if (!disease) {
            return;
        }

        try {
            setLoadingDrugs(true);

            const data = await fetchDrugsForDisease(disease);

            setDrugs(data.drugs || []);

        } catch (err) {
            console.error(err);
            setError(
                "Unable to load medicines for this disease."
            );
        } finally {
            setLoadingDrugs(false);
        }
    };


    return (
        <div className="disease-protocols">

            {/* Hero */}

            <section className="disease-protocols__hero">

                <p className="disease-protocols__kicker">
                    CLINICAL REFERENCE
                </p>

                <h1>
                    Disease Protocols
                </h1>

                <p>
                    Review medicines associated with specific diseases
                    from the medication safety knowledge graph.
                </p>

            </section>


            {/* Disease Selector */}

            <section className="disease-protocols__panel">

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


            {/* Error */}

            {error && (
                <div className="disease-protocols__error">
                    {error}
                </div>
            )}


            {/* Results */}

            {selectedDisease && (

                <section className="disease-protocols__results">

                    <div className="disease-protocols__results-header">

                        <div>

                            <p>
                                MEDICATION OPTIONS
                            </p>

                            <h2>
                                {selectedDisease}
                            </h2>

                        </div>

                        <span>
                            {drugs.length} medicines
                        </span>

                    </div>


                    {/* Loading */}

                    {loadingDrugs ? (

                        <div className="disease-protocols__loading">
                            Loading medicines...
                        </div>

                    ) : drugs.length === 0 ? (

                        <div className="disease-protocols__empty">
                            No medicines found for this disease.
                        </div>

                    ) : (

                        <div className="disease-protocols__grid">

                            {drugs.map((drug) => (

                                <article
                                    className="disease-drug-card"
                                    key={
                                        drug.drug_id ||
                                        drug.drug_name
                                    }
                                >

                                    <div className="disease-drug-card__icon">
                                        💊
                                    </div>

                                    <div className="disease-drug-card__content">

                                        <h3>
                                            {drug.drug_name}
                                        </h3>

                                        <p className="disease-drug-card__generic">
                                            {drug.generic_name}
                                        </p>

                                        {drug.drug_class && (
                                            <span className="disease-drug-card__class">
                                                {drug.drug_class}
                                            </span>
                                        )}

                                    </div>


                                    {drug.description_en && (
                                        <p className="disease-drug-card__description">
                                            {drug.description_en}
                                        </p>
                                    )}

                                </article>

                            ))}

                        </div>

                    )}

                </section>

            )}

        </div>
    );
}

export default DiseaseProtocols;