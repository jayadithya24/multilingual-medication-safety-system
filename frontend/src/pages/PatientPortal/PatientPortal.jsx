import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithPassword, registerPatient } from "../../services/authService";
import { clearStoredToken } from "../../services/api";
import "./PatientPortal.css";
import GoogleSignIn from "../../components/GoogleSignIn/GoogleSignIn";

function PatientPortal() {
  const navigate = useNavigate();
  const [tab, setTab] = useState(() => new URLSearchParams(window.location.search).get("session") === "expired" ? "login" : "register");
  const [loginIdentity, setLoginIdentity] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState(() => new URLSearchParams(window.location.search).get("session") === "expired" ? "Your session expired. Please sign in again." : "");

 const handleLogin = async () => {
  try {
    setLoading(true);
    setError("");
    setNotice("");

    await loginWithPassword(
      loginIdentity.trim(),
      loginPassword,
      true
    );

    // Patients complete their profile before using the dashboard.
    navigate("/patient-profile", { replace: true });

  } catch (loginError) {
    console.error("Login error:", loginError);

    const detail = loginError?.response?.data?.detail;

    if (Array.isArray(detail)) {
      setError(
        detail
          .map((item) => item.msg)
          .filter(Boolean)
          .join(", ")
      );
    } else {
      setError(detail || "Patient login failed.");
    }

  } finally {
    setLoading(false);
  }
};

  const handleRegister = async () => {
  try {
    setLoading(true);
    setError("");

    await registerPatient(
      registerName.trim(),
      registerEmail.trim(),
      registerPassword,
      confirmPassword
    );

    // Registration should NOT automatically log the patient in
    clearStoredToken();

    // Switch back to Login tab
    setTab("login");
    setNotice("Account created successfully. Sign in with your email and password.");

    // Put the registered email into the login field
    setLoginIdentity(registerEmail.trim());

    // Clear registration fields
    setRegisterName("");
    setRegisterEmail("");
    setRegisterPassword("");
    setConfirmPassword("");

    setError("");

  } catch (registerError) {
    console.error("Registration error:", registerError);

    const detail = registerError?.response?.data?.detail;

    if (Array.isArray(detail)) {
      setError(
        detail
          .map((item) => item.msg)
          .filter(Boolean)
          .join(", ")
      );
    } else {
      setError(detail || "Patient registration failed.");
    }

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
          {notice && <p className="portal-auth-success" role="status">{notice}</p>}
          <div className="portal-auth-tabs">
            <button disabled={loading} aria-pressed={tab === "login"} className={tab === "login" ? "is-active" : ""} onClick={() => { setTab("login"); setError(""); }}>
              Login
            </button>
            <button disabled={loading} aria-pressed={tab === "register"} className={tab === "register" ? "is-active" : ""} onClick={() => { setTab("register"); setError(""); setNotice(""); }}>
              Register
            </button>
          </div>

          <GoogleSignIn key={tab} mode={tab} />

          {tab === "login" ? (
            <form className="portal-auth-form" onSubmit={(event) => { event.preventDefault(); if (!loading) handleLogin(); }}>
              <label>
                <span>Email or username</span>
                <input required autoComplete="username" value={loginIdentity} onChange={(event) => setLoginIdentity(event.target.value)} />
              </label>
              <label>
                <span>Password</span>
                <input required autoComplete="current-password" type={showPassword ? "text" : "password"} value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} />
              </label>
              <button type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Login"}
              </button>
            </form>
          ) : (
            <form className="portal-auth-form" onSubmit={(event) => { event.preventDefault(); if (!loading) handleRegister(); }}>
              <label>
                <span>Name</span>
                <input required autoComplete="name" value={registerName} onChange={(event) => setRegisterName(event.target.value)} />
              </label>
              <label>
                <span>Email</span>
                <input required type="email" autoComplete="email" value={registerEmail} onChange={(event) => setRegisterEmail(event.target.value)} />
              </label>
              <label>
                <span>Password</span>
                <input required minLength={8} autoComplete="new-password" type={showPassword ? "text" : "password"} value={registerPassword} onChange={(event) => setRegisterPassword(event.target.value)} />
              </label>
              <label>
                <span>Confirm Password</span>
                <input required minLength={8} autoComplete="new-password" type={showPassword ? "text" : "password"} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
              </label>
              <small>Use at least 8 characters.</small>
              <button type="submit" disabled={loading}>
                {loading ? "Creating account..." : "Register"}
              </button>
            </form>
          )}

          <label className="portal-password-toggle"><input type="checkbox" checked={showPassword} onChange={(event) => setShowPassword(event.target.checked)} /> Show password</label>
          {error && <div className="portal-auth-error" role="alert">{error}</div>}

        </div>
      </section>
    </div>
  );
}

export default PatientPortal;
