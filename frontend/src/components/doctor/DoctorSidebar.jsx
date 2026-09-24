import { NavLink, useNavigate } from "react-router-dom";
import { logout } from "../../services/authService";
import "./DoctorSidebar.css";

function DoctorSidebar({ user }) {
    const navigate = useNavigate();
    const name = user?.full_name || user?.username || "Loading account…";
    const initials = user ? name.split(/\s+/).map(part => part[0]).slice(0, 2).join("").toUpperCase() : "…";

    const handleLogout = async () => {
        await logout();
        navigate("/research", { replace: true });
    };

    const navItems = [
        { path: "/reports", label: "Reports", icon: "▤" },
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
            path: "/clinical-insights",
            label: "Clinical Insights",
            icon: "📖",
        },
        {
            path: "/doctor-patients",
            label: "Patient Drug Lists",
            icon: "👤",
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
                    {initials}
                </div>

                <div>
                    <strong>{name}</strong>
                    <span>{user?.username || ""}</span>
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
