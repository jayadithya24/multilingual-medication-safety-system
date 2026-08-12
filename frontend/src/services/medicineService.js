import api from "./api";

export const fetchMedicines = async (lang = "en") => {
  const response = await api.get("/medicines", { params: { lang } });
  return response.data;
};

export const searchMedicine = async (name, lang = "en") => {
  const response = await api.get(`/medicine/${encodeURIComponent(name)}`, { params: { lang } });
  return response.data;
};