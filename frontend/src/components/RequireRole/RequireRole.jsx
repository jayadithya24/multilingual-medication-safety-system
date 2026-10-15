import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getStoredRole, getStoredToken } from "../../services/api";

function RequireRole({ allowedRoles }) {
  const location = useLocation();
  const token = getStoredToken();
  const role = getStoredRole();

  const localDoctorPreview = import.meta.env.DEV
    && ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname)
    && allowedRoles.includes("doctor")
    && location.pathname === "/doctor-dashboard"
    && new URLSearchParams(location.search).get("preview") === "1";

  if (localDoctorPreview) {
    return <><p role="status">Doctor dashboard preview — sign in to use protected clinical tools and patient records.</p><Outlet /></>;
  }

  if (!token) {
    return <Navigate to={allowedRoles.includes("patient") ? "/public" : "/"} replace state={{ from: location }} />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default RequireRole;
