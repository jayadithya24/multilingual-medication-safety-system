import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithPassword, requestDoctorAccount } from "../../services/authService";
import "./DoctorPortal.css";

function formatApiError(error) {
  if (!error?.response && error?.code === "ERR_NETWORK") {
    return "Unable to connect to the server. Please try again when the service is available. Your details have been kept in the form.";
  }

  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .filter(Boolean)
      .join("; ");
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return error?.message || "Request failed.";
}

function DoctorPortal() {
  const navigate = useNavigate();
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login");
  const [request, setRequest] = useState({
    name: "",
    email: "",
    phone: "",
    medicalRegistrationNo: "",
    specialization: "",
    hospital: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError("");
      await loginWithPassword(identity.trim(), password, false, "doctor");
      navigate("/doctor-dashboard", { replace: true });
    } catch (loginError) {
      console.error(loginError);
      setError(formatApiError(loginError) || "Doctor login failed.");
    } finally {
      setLoading(false);
    }
  };

  const updateRequest = (field) => (event) => {
    setRequest((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleRequest = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await requestDoctorAccount(request);
      setError(`Request submitted. Reference: ${response.request_id}`);
      setMode("login");
      setIdentity(request.email);
      setRequest({
        name: "", email: "", phone: "", medicalRegistrationNo: "",
        specialization: "", hospital: "", password: "", confirmPassword: "",
      });
    } catch (requestError) {
      console.error(requestError);
      setError(formatApiError(requestError) || "Doctor account request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portal-auth-page">
      <section className="portal-auth-shell">
        <div className="portal-auth-hero">
          <p className="portal-auth-kicker">Doctor Portal</p>
          <h1>{mode === "login" ? "Doctor sign in" : "Request a doctor account"}</h1>
          <p>{mode === "login" ? "Authenticate before opening interaction analysis and clinical review tools." : "Submit your professional details for administrator approval."}</p>
        </div>

        <div className="portal-auth-card">
          <div className="portal-auth-tabs">
            <button className={mode === "login" ? "is-active" : ""} onClick={() => { setMode("login"); setError(""); }}>
              Doctor Login
            </button>
            <button className={mode === "request" ? "is-active" : ""} onClick={() => { setMode("request"); setError(""); }}>
              Request Doctor Account
            </button>
          </div>

          {mode === "login" ? <div className="portal-auth-form">
            <label>
              <span>Doctor email or username</span>
              <input value={identity} onChange={(event) => setIdentity(event.target.value)} />
            </label>
            <label>
              <span>Password</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            <button onClick={handleLogin} disabled={loading}>
              {loading ? "Signing in..." : "Login"}
            </button>
          </div> : <div className="portal-auth-form">
            <label><span>Name</span><input value={request.name} onChange={updateRequest("name")} /></label>
            <label><span>Email</span><input type="email" value={request.email} onChange={updateRequest("email")} /></label>
            <label><span>Phone</span><input value={request.phone} onChange={updateRequest("phone")} /></label>
            <label><span>Medical Registration No.</span><input value={request.medicalRegistrationNo} onChange={updateRequest("medicalRegistrationNo")} /></label>
            <label><span>Specialization</span><input value={request.specialization} onChange={updateRequest("specialization")} /></label>
            <label><span>Hospital / Clinic</span><input value={request.hospital} onChange={updateRequest("hospital")} /></label>
            <label><span>Password</span><input type="password" value={request.password} onChange={updateRequest("password")} /></label>
            <label><span>Confirm Password</span><input type="password" value={request.confirmPassword} onChange={updateRequest("confirmPassword")} /></label>
            <button onClick={handleRequest} disabled={loading}>
              {loading ? "Submitting..." : "Submit Request"}
            </button>
          </div>}

          {error && <div className="portal-auth-error">{error}</div>}
        </div>
      </section>
    </div>
  );
}

export default DoctorPortal;
