import { Outlet } from "react-router-dom";

import DoctorSidebar from "../components/doctor/DoctorSidebar";
import DoctorTopbar from "../components/doctor/DoctorTopbar";

import "./DoctorLayout.css";

function DoctorLayout() {
    return (
        <div className="doctor-layout">

            <DoctorSidebar />

            <div className="doctor-layout__main">

                <DoctorTopbar />

                <main className="doctor-layout__content">
                    <Outlet />
                </main>

            </div>

        </div>
    );
}

export default DoctorLayout;