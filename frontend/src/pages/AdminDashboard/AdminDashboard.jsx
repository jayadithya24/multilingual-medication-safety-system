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
  const [reviewing, setReviewing] = useState("");

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
    if (reviewing) return;
    setReviewing(requestId);
    try {
      await api.put(`/admin/doctor-requests/${requestId}/${decision}`);
      await loadRequests();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || `Unable to ${decision} request.`);
    } finally {
      setReviewing("");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/admin", { replace: true });
  };

  const pendingCount = requests.length;
  const refreshClassName = loading
    ? "admin-dashboard__refresh is-spinning"
    : "admin-dashboard__refresh";

  return (
    <main className="admin-dashboard">
      <div className="admin-dashboard__shell">
        <section className="admin-dashboard__hero">
          <div className="admin-dashboard__hero-copy">
            <p className="admin-dashboard__eyebrow">MMSS Administration</p>
            <h1>Admin Dashboard</h1>
            <p className="admin-dashboard__intro">
              Review doctor account requests, monitor platform health, and keep the MMSS clinical network ready for verified professionals.
            </p>
          </div>
          <div className="admin-dashboard__toolbar">
            <button
              type="button"
              className={refreshClassName}
              onClick={loadRequests}
              disabled={loading}
            >
              <span className="admin-dashboard__refresh-icon" aria-hidden="true">↻</span>
              {loading ? "Refreshing…" : "Refresh"}
            </button>
            <button type="button" className="admin-dashboard__sign-out" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </section>

        <section className="admin-dashboard__summary" aria-label="Dashboard summary">
          <div className="admin-stat admin-stat--accent">
            <span className="admin-stat__label">Pending Doctor Requests</span>
            <strong>{pendingCount}</strong>
            <span className="admin-stat__hint">Awaiting administrator review</span>
          </div>
          <div className="admin-stat">
            <span className="admin-stat__label">Approved Doctors</span>
            <strong className="admin-stat__muted" title="User directory metrics are not exposed by the current API">—</strong>
            <span className="admin-stat__hint">Verified doctor portal accounts</span>
          </div>
          <div className="admin-stat">
            <span className="admin-stat__label">Total Patients</span>
            <strong className="admin-stat__muted" title="User directory metrics are not exposed by the current API">—</strong>
            <span className="admin-stat__hint">Registered patient portal users</span>
          </div>
          <div className="admin-stat admin-stat--status">
            <span className="admin-stat__label">Review Queue</span>
            <strong className="admin-stat__online">
              <i aria-hidden="true" />
              {loading ? "Loading" : error ? "Needs attention" : "Ready"}
            </strong>
            <span className="admin-stat__hint">Doctor request review status</span>
          </div>
        </section>

        <section className="admin-panel" aria-labelledby="admin-doctor-requests-heading">
          <div className="admin-panel__header">
            <div>
              <p className="admin-panel__eyebrow">Verification queue</p>
              <h2 id="admin-doctor-requests-heading">Doctor Account Requests</h2>
              <p>Review professional credentials before granting access to the Doctor Portal.</p>
            </div>
            <span className="admin-panel__count">{pendingCount} pending</span>
          </div>

          <div className="admin-panel__body">
            {loading && <p className="admin-panel__loading">Loading doctor requests…</p>}

            {!loading && requests.length === 0 && (
              <div className="admin-empty">
                <span aria-hidden="true">✓</span>
                <strong>Queue is clear</strong>
                <p>No pending doctor requests require attention right now.</p>
              </div>
            )}

            {!loading && requests.length > 0 && (
              <>
                <div className="admin-requests-table-wrap">
                  <table className="admin-requests-table">
                    <thead>
                      <tr>
                        <th scope="col">Name</th>
                        <th scope="col">Email</th>
                        <th scope="col">Medical Registration No.</th>
                        <th scope="col">Specialization</th>
                        <th scope="col">Hospital / Clinic</th>
                        <th scope="col">Status</th>
                        <th scope="col">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {requests.map((request) => (
                        <tr key={request.request_id}>
                          <td>
                            <div className="admin-requests-table__name">
                              <div className="doctor-request__avatar" aria-hidden="true">
                                {request.full_name?.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <h3>{request.full_name}</h3>
                              </div>
                            </div>
                          </td>
                          <td className="admin-requests-table__cell-muted">{request.email}</td>
                          <td>{request.medical_registration_no}</td>
                          <td>{request.specialization}</td>
                          <td>{request.hospital || "Not provided"}</td>
                          <td>
                            <span className="admin-status-badge">
                              {request.status || "pending"}
                            </span>
                          </td>
                          <td>
                            <div className="admin-requests-table__actions">
                              <button
                                type="button"
                                className="admin-btn admin-btn--approve"
                                onClick={() => decideRequest(request.request_id, "approve")}
                                disabled={Boolean(reviewing)}
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                className="admin-btn admin-btn--reject"
                                onClick={() => decideRequest(request.request_id, "reject")}
                                disabled={Boolean(reviewing)}
                              >
                                Reject
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="admin-requests-cards" aria-label="Doctor account requests">
                  {requests.map((request) => (
                    <article className="doctor-request" key={`card-${request.request_id}`}>
                      <div className="doctor-request__identity">
                        <div className="doctor-request__avatar" aria-hidden="true">
                          {request.full_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h3>{request.full_name}</h3>
                          <p>{request.email}</p>
                        </div>
                      </div>
                      <div className="doctor-request__details">
                        <span>
                          <b>Medical Registration No.</b>
                          {request.medical_registration_no}
                        </span>
                        <span>
                          <b>Specialization</b>
                          {request.specialization}
                        </span>
                        <span>
                          <b>Hospital / Clinic</b>
                          {request.hospital || "Not provided"}
                        </span>
                        <span>
                          <b>Status</b>
                          <span className="admin-status-badge">{request.status || "pending"}</span>
                        </span>
                      </div>
                      <div className="doctor-request__actions">
                        <button
                          type="button"
                          className="admin-btn admin-btn--approve"
                          onClick={() => decideRequest(request.request_id, "approve")}
                          disabled={Boolean(reviewing)}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="admin-btn admin-btn--reject"
                          onClick={() => decideRequest(request.request_id, "reject")}
                          disabled={Boolean(reviewing)}
                        >
                          Reject
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}

            {error && <div className="portal-auth-error">{error}</div>}
          </div>
        </section>

        <footer className="admin-dashboard__footer">
          <span>MMSS Administration · Secure access management</span>
        </footer>
      </div>
    </main>
  );
}

export default AdminDashboard;
