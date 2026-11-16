import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import "./PatientSidebar.css";

function PatientSidebar() {
    const navigate = useNavigate();
    const { pathname, search } = useLocation();
    const tab = new URLSearchParams(search).get("tab") || "text";
    const [lang, setLang] = useState("en");

    const handleLogout = async () => {
        await logout();
        navigate("/public", { replace: true });
    };

    const navItems = [
        {
            path: "/patient-dashboard",
            label: "Dashboard",
            tab: "text",
            icon: "⌂",
        },
        {
            path: "/scan-medicines",
            label: "Scan & Add Medicines",
            icon: "📷",
        },
        {
            path: "/patient-dashboard?tab=voice",
            tab: "voice",
            label: "Voice Search",
            icon: "🎙️",
        },
        {
            path: "/patient-dashboard?tab=medicines",
            label: "My Medicines",
            icon: "▤",
            tab: "medicines",
        },
        {
            path: "/patient-profile",
            label: "My Profile",
            icon: "👤",
        },
    ];

    const isActive = (item) => item.tab
        ? (pathname === "/patient-dashboard" && tab === item.tab) || (item.tab === "voice" && pathname === "/voice-search")
        : pathname === item.path;

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

            <nav className="patient-sidebar__nav" aria-label="Patient navigation">
                <p className="patient-sidebar__section-title">
                    NAVIGATION
                </p>

                {navItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        aria-current={isActive(item) ? "page" : undefined}
                        className={`patient-sidebar__link ${isActive(item) ? "is-active" : ""}`}
                    >
                        <span className="patient-sidebar__icon" aria-hidden="true">
                            {item.icon}
                        </span>

                        <span>
                            {item.label}
                        </span>
                    </Link>
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
