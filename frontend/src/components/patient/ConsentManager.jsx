import { useEffect, useState } from "react";
import api from "../../services/api";

export default function ConsentManager() {
  const [requests, setRequests] = useState([]);
  const [events, setEvents] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [logCategory, setLogCategory] = useState('all');
  const [code, setCode] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function refresh() {
    const [consents, log] = await Promise.all([api.get("/patient/access-requests"), api.get("/patient/access-log", { params: { category: logCategory } })]);
    setRequests(consents.data.requests || []);
    setEvents(log.data.events || []);
    setCursor(log.data.next_cursor);
  }
  useEffect(() => {
    let active = true;
    Promise.all([api.get("/patient/access-requests"), api.get("/patient/access-log")])
      .then(([consents, log]) => { if (active) { setRequests(consents.data.requests || []); setEvents(log.data.events || []); setCursor(log.data.next_cursor); } })
      .catch(() => { if (active) setError("Unable to load sharing records. Please refresh."); });
    return () => { active = false; };
  }, []);
  async function readLog(category, next = null) {
    setBusy(true); setError('');
    try {
      const { data } = await api.get('/patient/access-log', { params: { category, cursor: next } });
      setEvents(previous => next ? [...previous, ...data.events] : data.events);
      setCursor(data.next_cursor); setLogCategory(category);
    } catch { setError('Unable to load access log. Please retry.'); }
    finally { setBusy(false); }
  }
  async function act(action, requestId) {
    setBusy(true); setError("");
    try {
      if (action === "code") setCode((await api.post("/patient/share-code")).data);
      else if (requestId) await api.put(`/patient/access-request/${requestId}/${action}`);
      await refresh();
    } catch (err) { setError(err.response?.data?.detail || "Unable to update sharing. Please retry."); }
    finally { setBusy(false); }
  }
  return <section aria-label="Doctor access and privacy">
    <h3>Doctor access and privacy</h3>
    <p>Your profile, saved medicines and dose history are stored to provide medication management. Sharing is optional. A code lets a signed-in doctor request access; it does not grant access automatically.</p>
    <p>Approval shares your identity, medication report, schedules and dose history for seven days. You can reject or revoke access here. Revocation blocks future access but cannot retrieve copies already downloaded or printed. Requests expire after 24 hours.</p>
    <button disabled={busy} onClick={() => act("code")}>Create sharing code</button>{" "}
    <button disabled={busy} onClick={() => act("refresh")}>Refresh access and log</button>
    {code && <p role="status">Single-use code: <strong>{code.share_code}</strong>. Expires {new Date(code.expires_at).toLocaleString()}. Share privately with your doctor; a new code replaces the old one.</p>}
    {error && <p role="alert">{error}</p>}
    {!requests.length && <p>No access requests.</p>}
    {requests.map(request => <article key={request.requestId}>
      <p><strong>{request.doctorName || request.doctorId}</strong> — {request.status}. {request.expiresAt && <>Expires {new Date(request.expiresAt).toLocaleString()}.</>}</p>
      {request.status === "PENDING" && <><button disabled={busy} onClick={() => act("accept", request.requestId)}>Grant access for 7 days</button>{" "}<button disabled={busy} onClick={() => act("reject", request.requestId)}>Reject</button></>}
      {request.status === "ACCEPTED" && <><button disabled={busy} onClick={() => act("renew", request.requestId)}>Renew for 7 days</button>{" "}<button disabled={busy} onClick={() => act("revoke", request.requestId)}>Revoke access</button></>}
    </article>)}
    <details><summary>Access log</summary>
      <label>Event type <select value={logCategory} disabled={busy} onChange={event => readLog(event.target.value)}>
        <option value="all">All events</option><option value="security">Consent and denied access</option><option value="read">Record views</option>
      </select></label>
      <p>Repeated views and identical denied attempts within five minutes are combined. Each consent decision is kept separately.</p>
      {events.length ? <ul>{events.map((event, index) => <li key={index}>{new Date(event.createdAt).toLocaleString()} — {event.doctorId}: {event.action.replaceAll("_", " ")}</li>)}</ul> : <p>No access events recorded.</p>}
      {cursor && <button disabled={busy} onClick={() => readLog(logCategory, cursor)}>Load older events</button>}
    </details>
  </section>;
}
