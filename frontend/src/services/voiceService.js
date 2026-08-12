import api from "./api";

export const sendVoiceSearchAudio = async (audioFile) => {
  const formData = new FormData();

  formData.append("file", audioFile);

  const response = await api.post("/voice-search", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};