import api from "./api";

export const checkDrugInteraction = async (drug1, drug2, lang = "en") => {
  const response = await api.get("/interaction", {
    params: {
      drug1,
      drug2,
      lang,
    },
  });

  return response.data;
};

export const checkMultiDrugInteraction = async (drugs, lang = "en") => {
  const response = await api.post("/interaction/multi", { drugs }, { params: { lang } });
  return response.data;
};
