import api from "./api";

export const fetchMedicines = async (lang = "en") => {
  const response = await api.get("/medicines", { params: { lang } });
  return response.data;
};

export const searchMedicine = async (name, lang = "en") => {
    const response = await api.get("/neo4j/search", {
        params: {
            term: name,
            limit: 10,
        },
    });

    return response.data;
};
