import { NavLink, useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import "./DoctorSidebar.css";

function DoctorSidebar() {
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate("/research", { replace: true });
    };

    const navItems = [
        {
            path: "/doctor-dashboard",
            label: "Dashboard",
            icon: "⌂",
        },
        {
            path: "/drug-interaction",
            label: "Safety & DDI",
            icon: "⚡",
        },
       {
    path: "/drug-reference",
    label: "Drug Reference",
    icon: "💊",
},
        {
            path: "/disease-protocols",
            label: "Disease Protocols",
            icon: "🏥",
        },
        {
            path: "/doctor-patients",
            label: "Patient Drug Lists",
            icon: "👤",
        },
        {
            path: "/doctor-history",
            label: "Analysis History",
            icon: "📋",
        },
        {
            path: "/doctor-settings",
            label: "Settings",
            icon: "⚙",
        },
    ];

    return (
        <aside className="doctor-sidebar">

            <div className="doctor-sidebar__brand">
                <div className="doctor-sidebar__logo">
                    NG
                </div>

                <div>
                    <h2>NeoGraphMed</h2>
                    <span>Clinical Workspace</span>
                </div>
            </div>

            <div className="doctor-sidebar__profile">
                <div className="doctor-sidebar__avatar">
                    Dr
                </div>

                <div>
                    <strong>Doctor</strong>
                    <span>Clinical User</span>
                </div>
            </div>

            <nav className="doctor-sidebar__nav">

                <p className="doctor-sidebar__section-title">
                    WORKSPACE
                </p>

                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `doctor-sidebar__link ${
                                isActive
                                    ? "is-active"
                                    : ""
                            }`
                        }
                    >
                        <span className="doctor-sidebar__icon">
                            {item.icon}
                        </span>

                        <span>
                            {item.label}
                        </span>
                    </NavLink>
                ))}

            </nav>

            <div className="doctor-sidebar__bottom">

                <div className="doctor-sidebar__language">
                    <button className="is-active">
                        EN
                    </button>

                    <button>
                        ಕನ್ನಡ
                    </button>
                </div>

                <button
                    type="button"
                    className="doctor-sidebar__logout"
                    onClick={handleLogout}
                >
                    <span>↪</span>
                    Logout
                </button>

            </div>

        </aside>
    );
}

export default DoctorSidebar;