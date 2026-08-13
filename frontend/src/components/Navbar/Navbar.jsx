import { NavLink } from "react-router-dom";
import "./Navbar.css";

function Navbar() {

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

                    <li>
                        <NavLink to="/research">
                            Doctor Portal
                        </NavLink>
                    </li>

                    <li>
                        <NavLink to="/public">
                            Patient Portal
                        </NavLink>
                    </li>

                    <li>
                        <NavLink to="/admin">
                            Admin Portal
                        </NavLink>
                    </li>
                </ul>

            </nav>

        </header>

    );

}

export default Navbar;