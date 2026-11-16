import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../services/api";

import DoctorSidebar from "../components/doctor/DoctorSidebar";
import DoctorTopbar from "../components/doctor/DoctorTopbar";

import "./DoctorLayout.css";

function DoctorLayout() {
    const [user, setUser] = useState(null);
    const [graphStatus, setGraphStatus] = useState(null);
    useEffect(() => {
        let active = true;
        const check = () => api.get("/doctor/reference-status").then(({ data }) => { if (active) setGraphStatus(data.graph_check); }).catch(() => {});
        check();
        const timer = setInterval(check, 60000);
        return () => { active = false; clearInterval(timer); };
    }, []);
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
                    {["drift", "unavailable"].includes(graphStatus?.status) && <p role="status" className="graph-health-notice">{graphStatus.message} Local reference checks remain available.</p>}
                    <Outlet />
                </main>

            </div>

        </div>
    );
}

export default DoctorLayout;
