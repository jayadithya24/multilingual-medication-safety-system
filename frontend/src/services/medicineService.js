import api from "./api";

export const fetchMedicines = async () => {
  const response = await api.get("/medicines");
  return response.data;
};