import { Outlet, useMatch, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { listenForMedicationNotifications } from "../services/fcmService";
import { IS_STATIC_DEMO } from "../services/api";

import Navbar from "../components/Navbar/Navbar";
import Footer from "../components/Footer/Footer";
import "./PatientConsistency.css";

function MainLayout() {
    const { pathname } = useLocation();
    const hasDoctorSidebar = ["/doctor-dashboard", "/drug-interaction", "/drug-reference", "/disease-protocols", "/clinical-insights", "/doctor-patients", "/reports", "/settings", "/analysis-history"].includes(pathname);
    const patientDashboard = useMatch("/patient-dashboard");
    const patientScan = useMatch("/scan-medicines");
    const patientVoice = useMatch("/voice-search");
    const patientProfile = useMatch("/patient-profile");
    const patientPrescription = useMatch("/prescription");
    const hasPatientSidebar = patientDashboard || patientScan || patientVoice || patientProfile || patientPrescription;
    useEffect(() => {
        if (IS_STATIC_DEMO) return undefined;
        let disposed = false;
        let unsubscribe;
        listenForMedicationNotifications().then((cleanup) => {
            if (disposed) cleanup();
            else unsubscribe = cleanup;
        }).catch(() => console.warn("Notification listener unavailable; use Enable reminders to retry."));
        return () => { disposed = true; unsubscribe?.(); };
    }, []);

    return (

        <>

            {!hasPatientSidebar && !hasDoctorSidebar && <Navbar />}

            <div className="static-demo-banner" role="status">
                Public static demo · sample data only · uploads and audio are not processed · changes are not saved · no backend connected
            </div>

            <Outlet />

            <Footer />

        </>

    );

}

export default MainLayout;
