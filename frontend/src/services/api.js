import axios from "axios";
import { staticDemoAdapter } from "./demoApi";

export const IS_STATIC_DEMO = true;

// The demo does not authenticate or contact a backend.
localStorage.removeItem("mmss_token");
localStorage.removeItem("mmss_role");
sessionStorage.removeItem("mmss_session");
sessionStorage.removeItem("mmss_role");
export function hasStoredSession() { return sessionStorage.getItem("mmss_session") === "active"; }
export function getStoredRole() { return sessionStorage.getItem("mmss_role") || ""; }
export function setStoredSession() { sessionStorage.setItem("mmss_session", "active"); }
export function setStoredRole(role) { sessionStorage.setItem("mmss_role", role); }
export function clearStoredToken() {
  sessionStorage.removeItem("mmss_session");
  sessionStorage.removeItem("mmss_role");
}
export const api = axios.create({
  baseURL: "",
  timeout: 300000,
  withCredentials: false,
  adapter: staticDemoAdapter,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const patientPage = ["/patient-dashboard", "/patient-profile", "/scan-medicines", "/prescription", "/voice-search"].includes(window.location.pathname);
    const role = getStoredRole();
    const loginRequest = ["/auth/session", "/auth/google-session", "/auth/register-session"].includes(error.config?.url);
    if (error.response?.status === 401 && role === "admin" && !loginRequest) {
      clearStoredToken();
      window.location.replace("/admin?session=expired");
    }
    if (error.response?.status === 401 && role === "doctor" && !loginRequest) {
      clearStoredToken();
      window.location.replace("/research?session=expired");
    }
    if (error.response?.status === 401 && getStoredRole() === "patient" && patientPage && !loginRequest) {
      clearStoredToken();
      window.location.replace("/public?session=expired");
    }
    if (import.meta.env.DEV && error.response) {
      console.debug("API error", {
        method: error.config?.method?.toUpperCase(),
        url: (error.config?.url || "").split("?")[0],
        status: error.response.status,
      });
    }

    return Promise.reject(error);
  }
);

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function uploadPrescription(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload-image", formData);
  return response.data;
}

export async function searchDrug(term) {
  const response = await api.get("/neo4j/search", { params: { term } });
  return response.data;
}

export default api;
