import { Outlet } from "react-router-dom";
import PatientSidebar from "../components/patient/PatientSidebar";
import "./PatientLayout.css";

function PatientLayout() {
    return (
        <div className="patient-layout">
            <PatientSidebar />
            <div className="patient-layout__main">
                <main className="patient-layout__content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

export default PatientLayout;
