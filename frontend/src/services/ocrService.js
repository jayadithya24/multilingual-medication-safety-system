import api from "./api";

async function prepareOcrImage(imageFile) {
  if (!imageFile?.type?.startsWith("image/") || imageFile.size <= 2_000_000) {
    return imageFile;
  }

  const bitmap = await createImageBitmap(imageFile);
  const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();

  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", 0.82)
  );
  return new File([blob], "ocr-image.jpg", { type: "image/jpeg" });
}

/**
 * Upload medicine image to FastAPI OCR endpoint
 * @param {File} imageFile
 * @returns OCR response
 */
export const scanMedicine = async (imageFile, lang = "en") => {
  const formData = new FormData();

  formData.append("file", await prepareOcrImage(imageFile));
  try {
    const response = await api.post("/upload-image", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      params: { lang },
      // OCR can be slow on large images; increase timeout for this request
      timeout: 300000,
    });

    return response.data;
  } catch (err) {
    // Surface a clearer error for the UI
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      throw new Error('OCR request timed out. Try a smaller image or try again.', { cause: err });
    }
    throw err;
  }
};

export const uploadMedicineImage = scanMedicine;
