import { useState } from "react";
import { searchDrug } from "../services/api";

function DrugSearch() {
  const [term, setTerm] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!term.trim()) {
      setError("Please enter a drug name.");
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const data = await searchDrug(term.trim());
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell">
      <section className="section-header">
        <span className="hero__kicker">Quick lookup</span>
        <h1>Drug Search</h1>
        <p>
          Search for medicine details, side effects, and interaction risks in a
          clean review panel.
        </p>
      </section>

      <div className="search-card">
        <div className="search-card__bar">
          <input
            type="text"
            placeholder="Enter drug name"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
          />

          <button type="button" onClick={handleSearch} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {error && <p className="error-text">{error}</p>}

        {results.length > 0 ? (
          results.map((result) => (
            <div key={result.drug_id} className="result-card">
              <div className="result-card__header">
                <div>
                  <span className="feature-card__badge">Result</span>
                  <h2>{result.drug_name}</h2>
                </div>
                <span className="status-pill">{result.drug_class || "Drug"}</span>
              </div>

              <div className="result-grid">
                <div>
                  <p className="result-label">Generic</p>
                  <p>{result.generic_name || "N/A"}</p>
                </div>
                <div>
                  <p className="result-label">Description</p>
                  <p>{result.description_en || "No description available."}</p>
                </div>
                <div>
                  <p className="result-label">Interactions</p>
                  <p>
                    {result.interactions && result.interactions.length > 0
                      ? result.interactions.map((i) => i.drug_name).join(", ")
                      : "None found."}
                  </p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="result-card">
            <div className="result-card__header">
              <div>
                <span className="feature-card__badge">Info</span>
                <h2>Search results appear here</h2>
              </div>
            </div>
            <p>Type a drug name and click Search to query the Neo4j knowledge graph.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DrugSearch;
