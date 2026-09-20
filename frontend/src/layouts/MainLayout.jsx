import { Outlet } from "react-router-dom";
import { useEffect } from "react";
import { listenForMedicationNotifications } from "../services/fcmService";

import Navbar from "../components/Navbar/Navbar";
import Footer from "../components/Footer/Footer";
import "./PatientConsistency.css";

function MainLayout() {
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

            <Navbar />

            <Outlet />

            <Footer />

        </>

    );

}

export default MainLayout;
