import api from "./api";

export async function fetchPatientSchedule() {
    const response = await api.get("/patient-schedule");
    return response.data;
}

export async function createPatientSchedule(scheduleData) {
    const response = await api.post(
        "/patient-schedule",
        scheduleData
    );
    return response.data;
}

export async function markMedicineAsTaken(scheduleId) {
    const response = await api.post(
        `/patient-schedule/${scheduleId}/taken`
    );
    return response.data;
}

export async function fetchMedicationHistory() {
    const response = await api.get(
        "/patient/medication-history"
    );
    return response.data;
}