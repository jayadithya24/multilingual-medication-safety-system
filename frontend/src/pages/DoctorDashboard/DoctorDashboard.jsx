import { Link, useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import "./DoctorDashboard.css";

function DoctorDashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/research", { replace: true });
  };

  return (
    <div className="dashboard-shell">
      <section className="dashboard-hero">
        <p className="dashboard-kicker">Doctor Dashboard</p>
        <h1>Clinical review workspace</h1>
        <p>
          Open interaction analysis and review tools from one place.
        </p>
      </section>

      <div className="dashboard-grid">
        <Link className="dashboard-card" to="/drug-interaction">
          <h2>Drug Interaction</h2>
          <p>Check pairwise and multi-drug interactions for clinical review.</p>
        </Link>
        <button className="dashboard-card dashboard-card--button" onClick={handleLogout}>
          <h2>Sign out</h2>
          <p>Return to the doctor login page.</p>
        </button>
      </div>
    </div>
  );
}

export default DoctorDashboard;