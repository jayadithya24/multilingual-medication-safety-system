import "./Settings.css";

export default function Settings() {
  return <div className="doctor-settings">
    <section className="doctor-settings__hero"><h1>Account information</h1>
      <p>{localStorage.getItem("name") || "Doctor"}</p>
      <p>Role: {localStorage.getItem("mmss_role") || "doctor"}</p>
    </section>
    <section className="doctor-settings__panel"><h2>Workspace</h2>
      <p>Patient access requires a sharing code and explicit patient approval. Use the patient access page to request access and view approved patients.</p>
      <p>Medication reference information and research evaluations are not a substitute for professional clinical review.</p>
    </section>
  </div>;
}
