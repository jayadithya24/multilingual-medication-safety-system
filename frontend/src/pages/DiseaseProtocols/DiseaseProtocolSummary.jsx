function DiseaseProtocolSummary({
    selectedDisease,
    drugs,
    loadingDrugs,
}) {
    return (
        <section className="disease-protocols__results">
            <div className="disease-protocols__results-header">
                <div>
                    <p>MEDICATION OPTIONS</p>
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
