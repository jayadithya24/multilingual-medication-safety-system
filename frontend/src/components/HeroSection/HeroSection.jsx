import { Link } from "react-router-dom";
import "./HeroSection.css";

function HeroSection() {
  return (
    <section className="hero">

      <div className="hero-content">

        <span className="hero-tag">
          🩺 AI Powered Healthcare Platform
        </span>

        <h1>
          Multilingual Medication
          <br />
          Information &
          <br />
          Safety Monitoring System
        </h1>

        <p>
          Search medicines, identify tablets using OCR,
          analyze drug interactions, explore knowledge graphs,
          and assist patients with multilingual voice support.
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

        <img
          src="https://cdn-icons-png.flaticon.com/512/2966/2966488.png"
          alt="Medical"
        />

      </div>

    </section>
  );
}

export default HeroSection;