import { Link } from "react-router-dom";

function DiseaseProtocolSummary({
    selectedDisease,
    drugs,
    loadingDrugs,
    compact = false,
}) {
    return (
        <section className={`disease-protocols__results${compact ? " disease-protocols__results--compact" : ""}`}>
            <div className="disease-protocols__results-header">
                <div>
                    <p>{compact ? "PROTOCOL SUMMARY" : "MEDICATION OPTIONS"}</p>
                    <h2>{selectedDisease}</h2>
                </div>
                <span>{drugs.length} medicines</span>
            </div>

            {loadingDrugs ? (
                <div className="disease-protocols__loading">
                    Loading medicines...
                </div>
            ) : drugs.length === 0 ? (
                <div className="disease-protocols__empty">
                    No medicines found for this disease.
                </div>
            ) : compact ? (
                <div className="clinical-protocol-summary">
                    <p>
                        Medicines currently linked to this disease in the
                        knowledge graph. Full descriptions stay on Disease
                        Protocols so this page can focus on sources.
                    </p>
                    <ul className="clinical-protocol-summary__chips">
                        {drugs.map((drug) => (
                            <li key={drug.drug_id || drug.drug_name}>
                                {drug.drug_name}
                            </li>
                        ))}
                    </ul>
                    <Link
                        className="clinical-source-card__link"
                        to="/disease-protocols"
                    >
                        View full protocol
                    </Link>
                </div>
            ) : (
                <div className="disease-protocols__grid">
                    {drugs.map((drug) => (
                        <article
                            className="disease-drug-card"
                            key={drug.drug_id || drug.drug_name}
                        >
                            <div className="disease-drug-card__icon">
                                💊
                            </div>

                            <div className="disease-drug-card__content">
                                <h3>{drug.drug_name}</h3>
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
    );
}

export default DiseaseProtocolSummary;
