
import { Link } from "react-router-dom";

function Home() {
  const highlights = [
    "OCR-powered prescription intake",
    "Multilingual drug information lookup",
    "Interaction and safety monitoring",
  ];

  return (
    <div className="page-shell">
      <section className="hero">
        <div className="hero__copy">
          <span className="hero__kicker">Safer decisions, clearer communication</span>
          <h1>Multilingual Medication Safety System</h1>
          <p className="hero__lede">
            A clinical support platform for drug search, interaction analysis,
            and multilingual safety guidance across research and public-facing workflows.
          </p>

          <div className="hero__actions">
            <Link className="btn btn--primary" to="/research">
              Open Research Dashboard
            </Link>

            <Link className="btn btn--ghost" to="/user">
              Open Public Dashboard
            </Link>
          </div>

          <div className="hero__stats">
            <div>
              <strong>3</strong>
              <span>Core workflows</span>
            </div>
            <div>
              <strong>Multilingual</strong>
              <span>Accessible drug guidance</span>
            </div>
            <div>
              <strong>Fast</strong>
              <span>Search and review in one place</span>
            </div>
          </div>
        </div>

        <div className="hero__panel">
          <div className="panel-card panel-card--accent">
            <p className="panel-card__label">Current focus</p>
            <h2>Drug intelligence, translated for real-world use</h2>
            <p>
              Streamline medication review with a layout built for clinicians,
              researchers, and public users.
            </p>
          </div>

          <div className="panel-card">
            <p className="panel-card__label">Highlights</p>
            <ul className="checklist">
              {highlights.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;