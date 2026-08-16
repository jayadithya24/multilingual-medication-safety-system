import { Routes, Route } from "react-router-dom";

import MainLayout from "../layouts/MainLayout";
import DoctorLayout from "../layouts/DoctorLayout";

import Home from "../pages/Home/Home";
import PublicDashboard from "../pages/PublicDashboard/PublicDashboard";

import PatientPortal from "../pages/PatientPortal/PatientPortal";

import DoctorPortal from "../pages/DoctorPortal/DoctorPortal";
import DoctorDashboard from "../pages/DoctorDashboard/DoctorDashboard";
import DrugInteraction from "../pages/DrugInteraction/DrugInteraction";
import DrugReference from "../pages/DrugReference/DrugReference";

import AdminPortal from "../pages/AdminPortal/AdminPortal";
import AdminDashboard from "../pages/AdminDashboard/AdminDashboard";

import RequireRole from "../components/RequireRole/RequireRole";
import DiseaseProtocols from "../pages/DiseaseProtocols/DiseaseProtocols";
import PatientDrugLists from "../pages/PatientDrugLists/PatientDrugLists";
import AnalysisHistory from "../pages/AnalysisHistory/AnalysisHistory";
import Settings from "../pages/Settings/Settings";
import KnowledgeGraph from "../pages/KnowledgeGraph/KnowledgeGraph";
import PatientProfile from "../pages/PatientProfile/PatientProfile";
import Prescription from "../pages/Prescription/Prescription";


function AppRoutes() {
    return (
        <Routes>

            {/* =========================================
                MAIN APPLICATION LAYOUT
            ========================================= */}
            <Route path="/" element={<MainLayout />}>

                {/* Home */}
                <Route
                    index
                    element={<Home />}
                />


                {/* =====================================
                    PATIENT PORTAL LOGIN
                ===================================== */}
                <Route
                    path="public"
                    element={<PatientPortal />}
                />


                {/* =====================================
                    DOCTOR PORTAL LOGIN
                ===================================== */}
                <Route
                    path="research"
                    element={<DoctorPortal />}
                />


                {/* =====================================
                    ADMIN PORTAL LOGIN
                ===================================== */}
                <Route
                    path="admin"
                    element={<AdminPortal />}
                />


                {/* =====================================
                    PATIENT ROUTES
                ===================================== */}
                <Route
                    element={
                        <RequireRole allowedRoles={["patient"]} />
                    }
                >
                    <Route
                        path="patient-dashboard"
                        element={<PublicDashboard />}
                    />
                    <Route
        path="patient-profile"
        element={<PatientProfile />}
    />
    <Route
    path="prescription"
    element={<Prescription />}
/>
                </Route>


                {/* =====================================
    DOCTOR ROUTES
===================================== */}
<Route
    element={
        <RequireRole allowedRoles={["doctor"]} />
    }
>

    {/* Doctor Layout */}
    <Route element={<DoctorLayout />}>

        {/* Doctor Dashboard */}
        <Route
            path="doctor-dashboard"
            element={<DoctorDashboard />}
        />

        {/* Safety & DDI */}
        <Route
            path="drug-interaction"
            element={<DrugInteraction />}
        />

        {/* Drug Reference */}
        <Route
            path="drug-reference"
            element={<DrugReference />}
        />

        {/* Disease Protocols */}
        <Route
            path="disease-protocols"
            element={<DiseaseProtocols />}
        />

        {/* Patient Drug Lists */}
        <Route
            path="doctor-patients"
            element={<PatientDrugLists />}
        />

        {/* Analysis History */}
        <Route
           path="analysis-history"
            element={<AnalysisHistory />}
        />
        <Route
    path="doctor-settings"
    element={<Settings />}
/>
<Route
    path="knowledge-graph"
    element={<KnowledgeGraph />}
/>

    </Route>

</Route>


                {/* =====================================
                    ADMIN ROUTES
                ===================================== */}
                <Route
                    element={
                        <RequireRole allowedRoles={["admin"]} />
                    }
                >
                    <Route
                        path="admin-dashboard"
                        element={<AdminDashboard />}
                    />
                </Route>

            </Route>

        </Routes>
    );
}

export default AppRoutes;