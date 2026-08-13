import { Routes, Route } from "react-router-dom";

import MainLayout from "../layouts/MainLayout";

import Home from "../pages/Home/Home";
import PublicDashboard from "../pages/PublicDashboard/PublicDashboard";
import ImageScanner from "../pages/ImageScanner/ImageScanner";
import DrugInteraction from "../pages/DrugInteraction/DrugInteraction";
import VoiceSearch from "../pages/VoiceSearch/VoiceSearch";
import PatientPortal from "../pages/PatientPortal/PatientPortal";
import DoctorPortal from "../pages/DoctorPortal/DoctorPortal";
import AdminPortal from "../pages/AdminPortal/AdminPortal";
import DoctorDashboard from "../pages/DoctorDashboard/DoctorDashboard";
import AdminDashboard from "../pages/AdminDashboard/AdminDashboard";
import RequireRole from "../components/RequireRole/RequireRole";
function AppRoutes() {
    return (
        <Routes>

            <Route path="/" element={<MainLayout />}>

                <Route index element={<Home />} />

                <Route
                    path="research"
                    element={<DoctorPortal />}
                />

                <Route
                    path="public"
                    element={<PatientPortal />}
                />

                <Route
                    path="admin"
                    element={<AdminPortal />}
                />

                <Route element={<RequireRole allowedRoles={['patient']} />}>
                    <Route path="patient-dashboard" element={<PublicDashboard />} />
                    <Route path="scanner" element={<ImageScanner />} />
                    <Route path="voice-search" element={<VoiceSearch />} />
                </Route>

                <Route element={<RequireRole allowedRoles={['doctor']} />}>
                    <Route path="doctor-dashboard" element={<DoctorDashboard />} />
                    <Route path="drug-interaction" element={<DrugInteraction />} />
                </Route>

                <Route element={<RequireRole allowedRoles={['admin']} />}>
                    <Route path="admin-dashboard" element={<AdminDashboard />} />
                </Route>
            </Route>

        </Routes>
    );
}

export default AppRoutes;