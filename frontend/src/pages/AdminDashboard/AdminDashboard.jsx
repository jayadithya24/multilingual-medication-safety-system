import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import api from "../../services/api";
import "./AdminDashboard.css";

function AdminDashboard() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadRequests = async () => {
    try {
      setLoading(true);
      const response = await api.get("/admin/doctor-requests");
      setRequests(response.data.requests || []);
      setError("");
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || "Unable to load doctor requests.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    api.get("/admin/doctor-requests")
      .then((response) => {
        if (active) {
          setRequests(response.data.requests || []);
          setError("");
        }
      })
      .catch((requestError) => {
        if (active) setError(requestError?.response?.data?.detail || "Unable to load doctor requests.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const decideRequest = async (requestId, decision) => {
    try {
      await api.put(`/admin/doctor-requests/${requestId}/${decision}`);
      await loadRequests();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || `Unable to ${decision} request.`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/admin", { replace: true });
  };

  return (
    <main className="admin-dashboard">
      <section className="admin-dashboard__hero">
        <div>
          <p className="admin-dashboard__eyebrow">Operations / Admin</p>
          <h1>Administration workspace</h1>
          <p className="admin-dashboard__intro">Review access requests and keep the MMSS clinical network ready for verified professionals.</p>
        </div>
        <button className="admin-dashboard__refresh" onClick={loadRequests} disabled={loading}>
          <span aria-hidden="true">↻</span> {loading ? "Refreshing" : "Refresh"}
        </button>
      </section>

      <section className="admin-dashboard__summary" aria-label="Dashboard summary">
        <div className="admin-stat admin-stat--accent"><span className="admin-stat__label">Pending review</span><strong>{requests.length}</strong><span className="admin-stat__hint">Doctor account requests</span></div>
        <div className="admin-stat"><span className="admin-stat__label">Access policy</span><strong>Manual</strong><span className="admin-stat__hint">Approval required before login</span></div>
        <div className="admin-stat"><span className="admin-stat__label">System status</span><strong className="admin-stat__online"><i /> Operational</strong><span className="admin-stat__hint">Authentication services active</span></div>
      </section>

      <section className="admin-panel">
        <div className="admin-panel__header">
          <div><p className="admin-panel__eyebrow">Verification queue</p><h2>Doctor Requests</h2><p>Review professional details before granting Doctor Portal access.</p></div>
          <span className="admin-panel__count">{requests.length} pending</span>
        </div>
        <div className="admin-panel__body">
          {loading && <p>Loading requests...</p>}
          {!loading && requests.length === 0 && <div className="admin-empty"><span aria-hidden="true">✓</span><strong>Queue is clear</strong><p>No pending doctor requests require attention.</p></div>}
          {requests.map((request) => (
            <article className="doctor-request" key={request.request_id}>
              <div className="doctor-request__identity"><div className="doctor-request__avatar">{request.full_name?.charAt(0).toUpperCase()}</div><div><h3>{request.full_name}</h3><p>{request.email}</p></div></div>
              <div className="doctor-request__details">
                <span><b>Specialization</b>{request.specialization}</span>
                <span><b>Registration</b>{request.medical_registration_no}</span>
                <span><b>Hospital / Clinic</b>{request.hospital || "Not provided"}</span>
              </div>
              <div className="doctor-request__actions">
                <button onClick={() => decideRequest(request.request_id, "approve")}>Approve</button>
                <button onClick={() => decideRequest(request.request_id, "reject")}>Reject</button>
              </div>
            </article>
          ))}
          {error && <div className="portal-auth-error">{error}</div>}
        </div>
      </section>

      <footer className="admin-dashboard__footer"><span>MMSS Administration</span><button onClick={handleLogout}>Sign out</button></footer>
    </main>
  );
}

export default AdminDashboard;
