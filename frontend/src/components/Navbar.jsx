import { NavLink } from "react-router-dom";

function Navbar() {
  return (
    <nav className="topbar">
      <div>
        <p className="topbar__eyebrow">Medication Safety System</p>
        <p className="topbar__title">Multilingual support for safer care</p>
      </div>

      <div className="topbar__links">
        <NavLink className={({ isActive }) => `topbar__link${isActive ? " topbar__link--active" : ""}`} to="/">
          Home
        </NavLink>

        <NavLink className={({ isActive }) => `topbar__link${isActive ? " topbar__link--active" : ""}`} to="/research">
          Research Dashboard
        </NavLink>

        <NavLink className={({ isActive }) => `topbar__link${isActive ? " topbar__link--active" : ""}`} to="/user">
          Public Dashboard
        </NavLink>
      </div>
    </nav>
  );
}

export default Navbar;