import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getPatientProfile } from "../../services/patientService";

function hasCompleteProfile(profile) {
    return Boolean(
        profile?.full_name?.trim() &&
        profile?.age &&
        profile?.gender?.trim() &&
        profile?.medical_condition?.trim(),
    );
}

function RequirePatientProfile() {
    const location = useLocation();
    const [checking, setChecking] = useState(true);
    const [complete, setComplete] = useState(false);

    useEffect(() => {
        let active = true;

        getPatientProfile()
            .then((response) => {
                if (active) setComplete(hasCompleteProfile(response.profile));
            })
            .catch(() => {
                if (active) setComplete(false);
            })
            .finally(() => {
                if (active) setChecking(false);
            });

        return () => {
            active = false;
        };
    }, []);

    if (checking) return null;

    if (!complete) {
        return <Navigate to="/patient-profile" replace state={{ from: location }} />;
    }

    return <Outlet />;
}

export default RequirePatientProfile;