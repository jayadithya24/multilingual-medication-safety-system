import { Navigate, Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";

import MainLayout from "../layouts/MainLayout";
import DoctorLayout from "../layouts/DoctorLayout";
import PatientLayout from "../layouts/PatientLayout";

import Home from "../pages/Home/Home";
import PublicDashboard from "../pages/PublicDashboard/PublicDashboard";

import PatientPortal from "../pages/PatientPortal/PatientPortal";

import DoctorPortal from "../pages/DoctorPortal/DoctorPortal";
const DoctorDashboard = lazy(() => import("../pages/DoctorDashboard/DoctorDashboard"));
const DrugInteraction = lazy(() => import("../pages/DrugInteraction/DrugInteraction"));
import DrugReference from "../pages/DrugReference/DrugReference";

import AdminPortal from "../pages/AdminPortal/AdminPortal";
const AdminDashboard = lazy(() => import("../pages/AdminDashboard/AdminDashboard"));

import RequireRole from "../components/RequireRole/RequireRole";
import RequirePatientProfile from "../components/RequirePatientProfile/RequirePatientProfile";
import DiseaseProtocols from "../pages/DiseaseProtocols/DiseaseProtocols";
import PatientDrugLists from "../pages/PatientDrugLists/PatientDrugLists";
const KnowledgeGraph = lazy(() => import("../pages/KnowledgeGraph/KnowledgeGraph"));
import PatientProfile from "../pages/PatientProfile/PatientProfile";
import Prescription from "../pages/Prescription/Prescription";
import VoiceSearch from "../pages/VoiceSearch/VoiceSearch";
import AnalysisHistory from "../pages/AnalysisHistory/AnalysisHistory";
import Settings from "../pages/Settings/Settings";


function AppRoutes() {
    return (
        <Suspense fallback={<p role="status">Loading page…</p>}><Routes>

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

                <Route
                    path="ocr"
                    element={<Navigate to="/scan-medicines" replace />}
                />

                <Route
                    path="knowledge-graph"
                    element={<KnowledgeGraph />}
                />


                {/* =====================================
                    PATIENT ROUTES
                ===================================== */}
                <Route element={<PatientLayout />}>
                    <Route
                        path="patient-dashboard"
                        element={<PublicDashboard />}
                    />
                    <Route
                        path="scan-medicines"
                        element={<Prescription />}
                    />
                    <Route
                        path="voice-search"
                        element={<VoiceSearch />}
                    />
                    <Route
                        path="patient-profile"
                        element={<PatientProfile />}
                    />
                    <Route
                        path="prescription"
                        element={<Navigate to="/scan-medicines" replace />}
                    />
                </Route>


                {/* =====================================
                    DOCTOR ROUTES
                ===================================== */}
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

                    {/* Clinical Insights (same disease selector + protocol summary) */}
                    <Route
                        path="clinical-insights"
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

        </Routes></Suspense>
    );
}

export default AppRoutes;
