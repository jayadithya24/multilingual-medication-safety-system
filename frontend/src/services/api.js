import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

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
