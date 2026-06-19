function DrugSearch() {
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
          <input type="text" placeholder="Enter drug name" />

          <button type="button">Search</button>
        </div>

        <div className="result-card">
          <div className="result-card__header">
            <div>
              <span className="feature-card__badge">Example result</span>
              <h2>Metformin</h2>
            </div>

            <span className="status-pill">Common antidiabetic</span>
          </div>

          <div className="result-grid">
            <div>
              <p className="result-label">Treats</p>
              <p>Type 2 diabetes</p>
            </div>

            <div>
              <p className="result-label">Side effects</p>
              <p>Nausea, fatigue, stomach upset</p>
            </div>

            <div>
              <p className="result-label">Interactions</p>
              <p>Alcohol, contrast dye, selected kidney-risk medicines</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DrugSearch;