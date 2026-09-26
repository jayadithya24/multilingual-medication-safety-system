import api from "./api";

export async function getPatientProfile() {
    const response = await api.get("/patient/profile");
    return response.data;
}

export async function updatePatientProfile(profile) {
    const response = await api.put("/patient/profile", {
        full_name: profile.name,
        age: Number(profile.age),
        gender: profile.gender,
        medical_condition: profile.condition,
    });

    return response.data;
}