import api, { getStoredToken } from "./api";

export const fetchDiseases = async () => {
    const response = await api.get("/neo4j/diseases");
    return response.data;
};

export const fetchDrugsForDisease = async (diseaseName) => {
    const response = await api.get(
        `/neo4j/diseases/${encodeURIComponent(diseaseName)}/drugs`
    );

    return response.data;
};

export const fetchInteractionGraph = async (
    drug1,
    drug2
) => {

    const response = await api.get(
        "/neo4j/interaction-graph",
        {
            params: {
                drug1,
                drug2,
            },
        }
    );

    return response.data;
};

export async function fetchDoctorPatients() {
    const token = getStoredToken();

    if (!token) {
        throw new Error("Doctor authentication required.");
    }

    const response = await api.get("/doctor/patients");
    return response.data;
}

export const fetchKnowledgeGraph = async () => {
    const response = await api.get("/neo4j/graph");
    return response.data;
};

