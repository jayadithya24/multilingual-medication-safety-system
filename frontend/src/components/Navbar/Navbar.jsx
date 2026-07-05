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
                            Research Dashboard
                        </NavLink>
                    </li>

                    <li>
                        <NavLink to="/public">
                            Public Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/scanner">
                             OCR Scanner
                        </NavLink>
                    </li>
                </ul>

            </nav>

        </header>

    );

}

export default Navbar;