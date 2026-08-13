import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getStoredRole, getStoredToken } from "../../services/api";

function RequireRole({ allowedRoles }) {
  const location = useLocation();
  const token = getStoredToken();
  const role = getStoredRole();

  if (!token) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default RequireRole;