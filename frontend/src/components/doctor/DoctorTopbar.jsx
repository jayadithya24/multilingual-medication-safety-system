import { getStoredRole } from "../../services/api";
import "./DoctorTopbar.css";

function DoctorTopbar() {
    const role = getStoredRole();

    return (
        <header className="doctor-topbar">

            <div>
                <p className="doctor-topbar__eyebrow">
                    Clinical Safety Workspace
                </p>

                <h1>
                    Doctor Dashboard
                </h1>
            </div>

            <div className="doctor-topbar__right">

                <div className="doctor-topbar__search">
                    <span>⌕</span>

                    <input
                        type="text"
                        placeholder="Search drugs, diseases..."
                    />
                </div>

                <div className="doctor-topbar__user">
                    <div className="doctor-topbar__avatar">
                        Dr
                    </div>

                    <div>
                        <strong>
                            {role || "doctor"}
                        </strong>

                        <span>
                            Medical Professional
                        </span>
                    </div>
                </div>

            </div>

        </header>
    );
}

export default DoctorTopbar;