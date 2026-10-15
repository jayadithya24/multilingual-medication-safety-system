import { Link, useLocation } from "react-router-dom";
import "./PatientNavigation.css";

const destinations = [
    ["Medicine Search", "/patient-dashboard", "text"],
    ["Scan & Add Medicines", "/scan-medicines"],
    ["Voice Search", "/patient-dashboard?tab=voice", "voice"],
    ["My Medicines", "/patient-dashboard?tab=medicines", "medicines"],
    ["My Profile", "/patient-profile"],
];

export default function PatientNavigation() {
    const { pathname, search } = useLocation();
    const tab = new URLSearchParams(search).get("tab") || "text";
    return (
        <nav className="patient-navigation" aria-label="Patient navigation">
            {(pathname !== "/patient-dashboard" || tab !== "text") && (
                <Link className="patient-navigation__back" to="/patient-dashboard">
                    ← Back to dashboard
                </Link>
            )}
            <div className="patient-navigation__links">
                {destinations.map(([label, to, section]) => {
                    const active = section
                        ? pathname === "/patient-dashboard" && tab === section
                        : pathname === to;
                    return (
                        <Link key={to} to={to} aria-current={active ? "page" : undefined}
                            className={`patient-navigation__link${active ? " is-active" : ""}`}>
                            {label}
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}
