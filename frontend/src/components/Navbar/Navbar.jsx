import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { getStoredRole, getStoredToken } from "../../services/api";
import { logout } from "../../services/authService";
import "./Navbar.css";

function Navbar() {
    useLocation();
    const navigate = useNavigate();
    const isPatient = getStoredRole() === "patient" && Boolean(getStoredToken());

    return (

        <header className="navbar">

            <div className="logo">

                MMSS

            </div>

            <nav>

                <ul>

                    <li>
                        <NavLink to="/">
                            Home
                        </NavLink>
                    </li>

                    {!isPatient && <li>
                        <NavLink to="/research">
                            Doctor Portal
                        </NavLink>
                    </li>}

                    <li>
                        {isPatient ? <NavLink to="/patient-dashboard">My Dashboard</NavLink> :
                        <NavLink to="/public">
                            Patient Portal
                        </NavLink>}
                    </li>
                    {isPatient && <li><button className="navbar-signout" onClick={() => { logout(); navigate("/public", { replace: true }); }}>Sign out</button></li>}

                    {!isPatient && <li>
                        <NavLink to="/admin">
                            Admin Portal
                        </NavLink>
                    </li>}
                </ul>

            </nav>

        </header>

    );

}

export default Navbar;
