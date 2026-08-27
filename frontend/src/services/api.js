import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

export function getStoredToken() {
  const token = localStorage.getItem("mmss_token") || "";
  return token.replace(/^Bearer\s+/i, "").trim();
}

export function getStoredRole() {
  return localStorage.getItem("mmss_role") || "";
}

export function setStoredToken(token) {
  localStorage.setItem("mmss_token", token);
}

export function setStoredRole(role) {
  localStorage.setItem("mmss_role", role);
}

export function clearStoredToken() {
  localStorage.removeItem("mmss_token");
  localStorage.removeItem("mmss_role");
}

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();

  config.headers = config.headers || {};

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (import.meta.env.DEV) {
    console.debug("API request", {
      method: config.method?.toUpperCase(),
      url: `${config.baseURL || ""}${config.url || ""}`,
      tokenPresent: Boolean(token),
    });
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV && error.response) {
      console.debug("API error", {
        method: error.config?.method?.toUpperCase(),
        url: `${error.config?.baseURL || ""}${error.config?.url || ""}`,
        status: error.response.status,
        detail: error.response.data?.detail,
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
