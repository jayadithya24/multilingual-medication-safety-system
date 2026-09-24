import { Outlet, useMatch } from "react-router-dom";
import { useEffect } from "react";
import { listenForMedicationNotifications } from "../services/fcmService";

import Navbar from "../components/Navbar/Navbar";
import Footer from "../components/Footer/Footer";
import "./PatientConsistency.css";

function MainLayout() {
    const patientDashboard = useMatch("/patient-dashboard");
    const patientScan = useMatch("/scan-medicines");
    const patientVoice = useMatch("/voice-search");
    const patientProfile = useMatch("/patient-profile");
    const patientPrescription = useMatch("/prescription");
    const hasPatientSidebar = patientDashboard || patientScan || patientVoice || patientProfile || patientPrescription;
    useEffect(() => {
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

            {!hasPatientSidebar && <Navbar />}

            <Outlet />

            <Footer />

        </>

    );

}

export default MainLayout;
