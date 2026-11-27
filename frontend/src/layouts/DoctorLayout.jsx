import { Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import api, { IS_STATIC_DEMO } from "../services/api";

import DoctorSidebar from "../components/doctor/DoctorSidebar";
import DoctorTopbar from "../components/doctor/DoctorTopbar";

import "./DoctorLayout.css";

function DoctorLayout() {
    const [user, setUser] = useState(IS_STATIC_DEMO
        ? { username: "demo.doctor", full_name: "Demo Doctor", role: "doctor" }
        : null);
    const [graphStatus, setGraphStatus] = useState(IS_STATIC_DEMO
        ? { status: "available", message: "Static CSV reference data is loaded." }
        : null);
    useEffect(() => {
        if (IS_STATIC_DEMO) return undefined;
        let active = true;
        const check = () => api.get("/doctor/reference-status").then(({ data }) => { if (active) setGraphStatus(data.graph_check); }).catch(() => {});
        check();
        const timer = setInterval(check, 60000);
        return () => { active = false; clearInterval(timer); };
    }, []);
    useEffect(() => {
        if (IS_STATIC_DEMO) return undefined;
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
