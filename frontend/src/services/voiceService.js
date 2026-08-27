import api from "./api";

export const sendVoiceSearchAudio = async (audioFile, lang = "auto", medicineName = "") => {
  const formData = new FormData();

  formData.append("file", audioFile);
  console.debug("Upload started", {
    fileSize: audioFile?.size || 0,
    fileType: audioFile?.type || "unknown",
  });

  const response = await api.post("/voice-search", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    params: { lang, ...(medicineName ? { medicine_name: medicineName } : {}) },
    timeout: 120000,
  });

  console.debug("Upload completed", { status: response.status });
  return response.data;
};