import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { getStoredRole, getStoredToken } from "../../services/api";
import { logout } from "../../services/authService";
import "./PatientSidebar.css";

function PatientSidebar() {
    const navigate = useNavigate();
    const [lang, setLang] = useState("en");
    const isPatient = getStoredRole() === "patient" && Boolean(getStoredToken());

    const handleLogout = async () => {
        await logout();
        navigate("/public", { replace: true });
    };

    const navItems = [
        {
            path: "/patient-dashboard",
            label: "Dashboard",
            icon: "⌂",
        },
        {
            path: "/scan-medicines",
            label: "Scan Medicines",
            icon: "📷",
        },
        {
            path: "/voice-search",
            label: "Voice Search",
            icon: "🎙️",
        },
        {
            path: "/knowledge-graph",
            label: "Knowledge Graph",
            icon: "🕸️",
        },
        {
            path: "/patient-profile",
            label: "Patient Profile",
            icon: "👤",
        },
    ];

    return (
        <aside className="patient-sidebar">

            <div className="patient-sidebar__brand">
                <div className="patient-sidebar__logo">
                    NG
                </div>

                <div>
                    <h2>NeoGraphMed</h2>
                    <span>Patient Workspace</span>
                </div>
            </div>

            <div className="patient-sidebar__profile">
                <div className="patient-sidebar__avatar">
                    PT
                </div>

                <div>
                    <strong>Patient User</strong>
                    <span>Personal Health</span>
                </div>
            </div>

            <nav className="patient-sidebar__nav">
                <p className="patient-sidebar__section-title">
                    NAVIGATION
                </p>

                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `patient-sidebar__link ${isActive ? "is-active" : ""}`
                        }
                    >
                        <span className="patient-sidebar__icon">
                            {item.icon}
                        </span>

                        <span>
                            {item.label}
                        </span>
                    </NavLink>
                ))}
            </nav>

            <div className="patient-sidebar__bottom">

                <div className="patient-sidebar__language">
                    <button
                        className={lang === "en" ? "is-active" : ""}
                        onClick={() => setLang("en")}
                    >
                        EN
                    </button>

                    <button
                        className={lang === "kn" ? "is-active" : ""}
                        onClick={() => setLang("kn")}
                    >
                        ಕನ್ನಡ
                    </button>
                </div>

                <button
                    type="button"
                    className="patient-sidebar__logout"
                    onClick={handleLogout}
                >
                    <span>↪</span>
                    Logout
                </button>

            </div>

        </aside>
    );
}

export default PatientSidebar;
