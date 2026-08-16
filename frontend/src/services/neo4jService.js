import api from "./api";

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
    const token =
        localStorage.getItem("token") ||
        localStorage.getItem("access_token");

    const response = await fetch(
        "http://127.0.0.1:8000/doctor/patients",
        {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        }
    );

    if (!response.ok) {
        throw new Error("Failed to load doctor patients");
    }

    return response.json();
};


// ⭐ ADD THIS
export const fetchKnowledgeGraph = async () => {
    const response = await api.get("/neo4j/graph");
    return response.data;
};

