import { Routes, Route } from "react-router-dom";

import MainLayout from "../layouts/MainLayout";

import Home from "../pages/Home/Home";
import ResearchDashboard from "../pages/ResearchDashboard/ResearchDashboard";
import PublicDashboard from "../pages/PublicDashboard/PublicDashboard";
import ImageScanner from "../pages/ImageScanner/ImageScanner";
function AppRoutes() {
    return (
        <Routes>

            <Route path="/" element={<MainLayout />}>

                <Route index element={<Home />} />

                <Route
                    path="research"
                    element={<ResearchDashboard />}
                />

                <Route
                    path="public"
                    element={<PublicDashboard />}
                />

                <Route 
                    path="/scanner" 
                    element={<ImageScanner />}
                />
            </Route>

        </Routes>
    );
}

export default AppRoutes;