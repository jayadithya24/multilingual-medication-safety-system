import { Link } from "react-router-dom";
import "./DemoPortal.css";

const PORTALS = {
  patient: {
    title: "Patient Portal",
    description: "Search the medicine catalog, review a sample medication schedule, and explore multilingual sample output.",
    destination: "/patient-dashboard",
    action: "Open Patient Dashboard",
  },
  doctor: {
    title: "Doctor Portal",
    description: "Explore the drug reference, interaction checker, disease protocols, graph, and synthetic patient examples.",
    destination: "/doctor-dashboard",
    action: "Open Doctor Dashboard",
  },
  admin: {
    title: "Administrator Portal",
    description: "View a predefined sample verification queue and download the catalog datasets.",
    destination: "/admin-dashboard",
    action: "Open Admin Dashboard",
  },
};

export default function DemoPortal({ role }) {
  const portal = PORTALS[role] || PORTALS.patient;
  return (
    <main className="demo-portal">
      <section className="demo-portal__card">
        <p className="demo-portal__eyebrow">PUBLIC STATIC DEMO</p>
        <h1>{portal.title}</h1>
        <p>{portal.description}</p>
        <div className="demo-portal__notice">
          No account or backend is required. All records are examples; files and audio are not uploaded, and changes are not saved.
        </div>
        <Link className="demo-portal__action" to={portal.destination}>{portal.action} <span aria-hidden="true">→</span></Link>
        <Link className="demo-portal__back" to="/">Back to home</Link>
      </section>
    </main>
  );
}
