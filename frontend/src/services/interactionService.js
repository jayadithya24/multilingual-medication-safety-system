import api from "./api";

export const checkDrugInteraction = async (drug1, drug2) => {
  const response = await api.get("/interaction", {
    params: {
      drug1,
      drug2,
    },
  });

  return response.data;
};