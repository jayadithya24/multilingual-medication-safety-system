import api from "./api";

export const uploadMedicineImage = async (imageFile) => {

    const formData = new FormData();

    formData.append("file", imageFile);

    const response = await api.post(
        "/upload-image",
        formData
    );

    return response.data;
};