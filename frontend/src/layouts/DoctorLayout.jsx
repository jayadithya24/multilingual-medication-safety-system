import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../services/api";

import DoctorSidebar from "../components/doctor/DoctorSidebar";
import DoctorTopbar from "../components/doctor/DoctorTopbar";

import "./DoctorLayout.css";

function DoctorLayout() {
    const [user, setUser] = useState(null);
    useEffect(() => {
        const controller = new AbortController();
        api.get("/auth/me", { signal: controller.signal })
            .then(({ data }) => setUser(data))
            .catch(() => {}); // Authentication failures are handled by the API interceptor.
        return () => controller.abort();
    }, []);
    return (
        <div className="doctor-layout">

            <DoctorSidebar user={user} />

            <div className="doctor-layout__main">

                <DoctorTopbar user={user} />

                <main className="doctor-layout__content">
                    <Outlet />
                </main>

            </div>

        </div>
    );
}

export default DoctorLayout;
