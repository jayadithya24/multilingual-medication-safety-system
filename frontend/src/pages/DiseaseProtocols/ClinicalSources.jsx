function ClinicalSources({ entry }) {
    if (!entry) {
        return (
            <div className="disease-protocols__empty">
                No curated clinical sources are available for this disease.
            </div>
        );
    }

    const sources = entry.sources || [];

    if (sources.length === 0) {
        return (
            <div className="disease-protocols__empty">
                No curated clinical sources are available for this disease.
            </div>
        );
    }

    return (
        <div className="clinical-sources">
            <div className="clinical-sources__header">
                <h3>Sources &amp; Further Reading</h3>
                <p>
                    Curated references already used in the MMSS dataset
                    for this disease. Full article text is not shown here.
                </p>
            </div>

            <div className="clinical-sources__list">
                {sources.map((source, index) => (
                    <article
                        className="clinical-source-card"
                        key={`${source.title}-${index}`}
                    >
                        <p className="clinical-source-card__kicker">
                            REFERENCE
                        </p>

                        <h4>{source.title}</h4>

                        <div className="clinical-source-card__meta">
                            <div className="drug-info-card">
                                <span>Authors</span>
                                <strong>{source.authors || "Not listed"}</strong>
                            </div>
                            <div className="drug-info-card">
                                <span>Year</span>
                                <strong>{source.year ?? "Not listed"}</strong>
                            </div>
                            <div className="drug-info-card">
                                <span>Journal</span>
                                <strong>{source.journal || "Not listed"}</strong>
                            </div>
                        </div>

                        <p className="clinical-source-card__summary">
                            {source.summary}
                        </p>

                        {source.url ? (
                            <a
                                className="clinical-source-card__link"
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Read full article
                            </a>
                        ) : null}
                    </article>
                ))}
            </div>
        </div>
    );
}

export default ClinicalSources;
