import api from "./api";

/**
 * Upload medicine image to FastAPI OCR endpoint
 * @param {File} imageFile
 * @returns OCR response
 */
export const scanMedicine = async (imageFile, lang = "en") => {
  const formData = new FormData();

  formData.append("file", imageFile);
  try {
    const response = await api.post("/upload-image", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      params: { lang },
      // OCR can be slow on large images; increase timeout for this request
      timeout: 120000,
    });

    return response.data;
  } catch (err) {
    // Surface a clearer error for the UI
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      throw new Error('OCR request timed out. Try a smaller image or try again.');
    }
    throw err;
  }
};

export const uploadMedicineImage = scanMedicine;