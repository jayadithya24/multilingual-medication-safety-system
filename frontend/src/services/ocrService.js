import api from "./api";

/**
 * Upload medicine image to FastAPI OCR endpoint
 * @param {File} imageFile
 * @returns OCR response
 */
export const scanMedicine = async (imageFile) => {
  const formData = new FormData();

  formData.append("file", imageFile);

  const response = await api.post("/upload-image", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const uploadMedicineImage = scanMedicine;