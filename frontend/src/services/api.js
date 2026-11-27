import axios from "axios";

function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_URL;

  if (configured && typeof window !== "undefined") {
    try {
      const apiUrl = new URL(configured, window.location.origin);
      const pageHost = window.location.hostname;
      const loopbackSwap =
        (apiUrl.hostname === "127.0.0.1" && pageHost === "localhost") ||
        (apiUrl.hostname === "localhost" && pageHost === "127.0.0.1");

      if (loopbackSwap) {
        apiUrl.hostname = pageHost;
      }

      return apiUrl.origin;
    } catch {
      return configured;
    }
  }

  if (configured) {
    return configured;
  }

  if (import.meta.env.DEV) {
    return "";
  }

  return "";
}

const BASE_URL = resolveApiBaseUrl();

// UI hints only. The credential is an HttpOnly cookie owned by the server.
localStorage.removeItem("mmss_token");
localStorage.removeItem("mmss_role");
export function hasStoredSession() { return sessionStorage.getItem("mmss_session") === "active"; }
export function getStoredRole() { return sessionStorage.getItem("mmss_role") || ""; }
export function setStoredSession() { sessionStorage.setItem("mmss_session", "active"); }
export function setStoredRole(role) { sessionStorage.setItem("mmss_role", role); }
export function clearStoredToken() {
  sessionStorage.removeItem("mmss_session");
  sessionStorage.removeItem("mmss_role");
}
export const api = axios.create({ baseURL: BASE_URL, timeout: 300000, withCredentials: true });

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
  const response = await fetch(`${BASE_URL}/health`);
  return response.json();
}

export async function uploadPrescription(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload-image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload prescription");
  }

  return response.json();
}

export async function searchDrug(term) {
  const response = await fetch(`${BASE_URL}/neo4j/search?term=${encodeURIComponent(term)}`);
  if (!response.ok) {
    throw new Error("Drug search failed");
  }
  return response.json();
}

export default api;
