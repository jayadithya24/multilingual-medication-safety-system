import { useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import "./AdminDashboard.css";

function AdminDashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/admin", { replace: true });
  };

  return (
    <div className="dashboard-shell">
      <section className="dashboard-hero">
        <p className="dashboard-kicker">Admin Dashboard</p>
        <h1>Administration workspace</h1>
        <p>Placeholder dashboard for user, doctor, patient, medicine, and system management.</p>
      </section>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h2>Manage users</h2>
          <p>Reserved for future user and role administration tools.</p>
        </div>
        <div className="dashboard-card">
          <h2>System settings</h2>
          <p>Reserved for future configuration and operational controls.</p>
        </div>
        <button className="dashboard-card dashboard-card--button" onClick={handleLogout}>
          <h2>Sign out</h2>
          <p>Return to the admin login page.</p>
        </button>
      </div>
    </div>
  );
}

export default AdminDashboard;