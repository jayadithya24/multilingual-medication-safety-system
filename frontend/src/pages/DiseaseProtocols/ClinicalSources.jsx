function SourceMeta({ label, value }) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    return (
        <div className="drug-info-card">
            <span>{label}</span>
            <strong>{value}</strong>
        </div>
    );
}

function ClinicalSources({ entry }) {
    if (!entry) {
        return (
            <div className="disease-protocols__empty">
                No curated academic sources are available for this disease.
            </div>
        );
    }

    const sources = entry.sources || [];

    if (sources.length === 0) {
        return (
            <div className="disease-protocols__empty">
                No curated academic sources are available for this disease.
            </div>
        );
    }

    return (
        <div className="clinical-sources">
            <div className="clinical-sources__header">
                <h3>Sources &amp; Further Reading</h3>
                <p>
                    Academic papers from the project reference list that
                    support this disease. Full article text is not shown here.
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
                            <SourceMeta label="Authors" value={source.authors} />
                            <SourceMeta label="Year" value={source.year} />
                            <SourceMeta label="Journal" value={source.journal} />
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
