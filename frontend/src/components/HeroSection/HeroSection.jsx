import { Link } from "react-router-dom";
import "./HeroSection.css";

function HeroSection() {
  return (
    <section className="hero">

      <div className="hero-content">

        <span className="hero-tag">
          🩺 Static Medication Safety Demo
        </span>

        <h1>
          Multilingual Medication
          <br />
          Information &
          <br />
          Safety Monitoring System
        </h1>

        <p>
          Search the bundled medicine catalog, review sample interaction records,
          and explore multilingual reference data and a predefined knowledge graph.
          OCR and voice results are examples only.
        </p>

        <div className="hero-buttons">

          <Link to="/research" className="btn-primary">
            Doctor Portal
          </Link>

          <Link to="/public" className="btn-secondary">
            Patient Portal
          </Link>

          <Link to="/admin" className="btn-tertiary">
            Admin Portal
          </Link>

        </div>

      </div>

      <div className="hero-image">

        <div className="hero-illustration" role="img" aria-label="Medicine and health symbols">
          <span>💊</span>
          <span>🩺</span>
          <span>📋</span>
        </div>

      </div>

    </section>
  );
}

export default HeroSection;