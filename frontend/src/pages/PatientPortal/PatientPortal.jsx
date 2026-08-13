import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithPassword, registerPatient } from "../../services/authService";
import { fetchMedicines } from "../../services/medicineService";
import "./PatientPortal.css";

function PatientPortal() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("login");
  const [loginIdentity, setLoginIdentity] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError("");
      await loginWithPassword(loginIdentity.trim(), loginPassword);
      navigate("/patient-dashboard", { replace: true });
    } catch (loginError) {
      console.error(loginError);
      setError(loginError?.response?.data?.detail || "Patient login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    try {
      setLoading(true);
      setError("");
      await registerPatient(registerName.trim(), registerEmail.trim(), registerPassword, confirmPassword);
      navigate("/patient-dashboard", { replace: true });
    } catch (registerError) {
      console.error(registerError);
      setError(registerError?.response?.data?.detail || "Patient registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portal-auth-page">
      <section className="portal-auth-shell">
        <div className="portal-auth-hero">
          <p className="portal-auth-kicker">Patient Portal</p>
          <h1>Sign in or create a patient account</h1>
          <p>
            Use the patient portal to access medicine lookup, OCR, and voice search after authentication.
          </p>
        </div>

        <div className="portal-auth-card">
          <div className="portal-auth-tabs">
            <button className={tab === "login" ? "is-active" : ""} onClick={() => setTab("login")}>
              Login
            </button>
            <button className={tab === "register" ? "is-active" : ""} onClick={() => setTab("register")}>
              Register
            </button>
          </div>

          {tab === "login" ? (
            <div className="portal-auth-form">
              <label>
                <span>Email or username</span>
                <input value={loginIdentity} onChange={(event) => setLoginIdentity(event.target.value)} />
              </label>
              <label>
                <span>Password</span>
                <input type="password" value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} />
              </label>
              <button onClick={handleLogin} disabled={loading}>
                {loading ? "Signing in..." : "Login"}
              </button>
            </div>
          ) : (
            <div className="portal-auth-form">
              <label>
                <span>Name</span>
                <input value={registerName} onChange={(event) => setRegisterName(event.target.value)} />
              </label>
              <label>
                <span>Email</span>
                <input value={registerEmail} onChange={(event) => setRegisterEmail(event.target.value)} />
              </label>
              <label>
                <span>Password</span>
                <input type="password" value={registerPassword} onChange={(event) => setRegisterPassword(event.target.value)} />
              </label>
              <label>
                <span>Confirm Password</span>
                <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
              </label>
              <button onClick={handleRegister} disabled={loading}>
                {loading ? "Creating account..." : "Register"}
              </button>
            </div>
          )}

          {error && <div className="portal-auth-error">{error}</div>}

        </div>
      </section>
    </div>
  );
}

export default PatientPortal;