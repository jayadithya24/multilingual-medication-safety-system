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

export async function fetchRemovedPatientSchedules() {
    const response = await api.get("/patient-schedule/removed");
    return response.data;
}

export async function deletePatientSchedule(scheduleId) {
    const response = await api.delete(
        `/patient-schedule/${encodeURIComponent(scheduleId)}`
    );
    return response.data;
}
