import api from "./api";

export const sendVoiceSearchAudio = async (audioFile, lang = "en") => {
  const formData = new FormData();

  formData.append("file", audioFile);

  const response = await api.post("/voice-search", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    params: { lang },
  });

  return response.data;
};