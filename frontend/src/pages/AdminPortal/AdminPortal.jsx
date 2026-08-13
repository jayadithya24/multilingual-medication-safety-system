import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithPassword } from "../../services/authService";
import "./AdminPortal.css";

function AdminPortal() {
  const navigate = useNavigate();
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError("");
      await loginWithPassword(identity.trim(), password);
      navigate("/admin-dashboard", { replace: true });
    } catch (loginError) {
      console.error(loginError);
      setError(loginError?.response?.data?.detail || "Admin login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portal-auth-page">
      <section className="portal-auth-shell">
        <div className="portal-auth-hero">
          <p className="portal-auth-kicker">Admin Portal</p>
          <h1>Admin sign in</h1>
          <p>Enter the administration area to manage users, datasets, and system settings later.</p>
        </div>

        <div className="portal-auth-card">
          <div className="portal-auth-form">
            <label>
              <span>Admin email or username</span>
              <input value={identity} onChange={(event) => setIdentity(event.target.value)} />
            </label>
            <label>
              <span>Password</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            <button onClick={handleLogin} disabled={loading}>
              {loading ? "Signing in..." : "Login"}
            </button>
          </div>

          {error && <div className="portal-auth-error">{error}</div>}
        </div>
      </section>
    </div>
  );
}

export default AdminPortal;