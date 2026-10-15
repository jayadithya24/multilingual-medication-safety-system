import { useState } from "react";
import { searchMedicine } from "../../services/medicineService";
import { fetchDiseases } from "../../services/neo4jService";
import "./DoctorTopbar.css";

function DoctorTopbar({ user }) {
    const name = user?.full_name || user?.username || "Loading account…";
    const initials = user ? name.split(/\s+/).map(part => part[0]).slice(0, 2).join("").toUpperCase() : "…";
    const [searchQuery, setSearchQuery] = useState("");
    const [results, setResults] = useState({ medicines: [], diseases: [] });
    const [loading, setLoading] = useState(false);

    const handleSearch = async (value) => {
        const trimmed = value.trim();
        setSearchQuery(value);

        if (!trimmed) {
            setResults({ medicines: [], diseases: [] });
            return;
        }

        try {
            setLoading(true);
            const [medicineResponse, diseaseResponse] = await Promise.all([
                searchMedicine(trimmed, "en").catch(() => ({ results: [] })),
                fetchDiseases().catch(() => ({ diseases: [] })),
            ]);

            const medicines = Array.isArray(medicineResponse?.results) ? medicineResponse.results : [];
            const diseaseOptions = Array.isArray(diseaseResponse?.diseases) ? diseaseResponse.diseases : [];
            const normalizedQuery = trimmed.toLowerCase();
            const diseases = diseaseOptions.filter(
                (disease) => typeof disease === "string" && disease.toLowerCase().includes(normalizedQuery)
            );

            setResults({
                medicines,
                diseases: diseases.map((disease) => ({
                    disease_name: disease,
                    disease_id: String(disease).toLowerCase().replace(/[^a-z0-9]+/g, "-"),
                })),
            });
        } catch (error) {
            console.error("Doctor dashboard search failed:", error);
            setResults({ medicines: [], diseases: [] });
        } finally {
            setLoading(false);
        }
    };

    return (
        <header className="doctor-topbar">

            <div>
                <p className="doctor-topbar__eyebrow">
                    Clinical Safety Workspace
                </p>

                <h1>
                    Doctor Dashboard
                </h1>
            </div>

            <div className="doctor-topbar__right">

                <div className="doctor-topbar__search-wrap">
                    <div className="doctor-topbar__search">
                        <span>⌕</span>

                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(event) => handleSearch(event.target.value)}
                            placeholder="Search drugs, diseases..."
                        />
                    </div>

                    {(searchQuery.trim() || loading) && (
                        <div className="doctor-topbar__search-results" role="listbox" aria-live="polite">
                            {loading ? (
                                <div className="doctor-topbar__search-status">Searching...</div>
                            ) : (
                                <>
                                    {results.medicines.length === 0 && results.diseases.length === 0 ? (
                                        <div className="doctor-topbar__search-status">No matching results</div>
                                    ) : (
                                        <>
                                            {results.medicines.map((medicine, index) => (
                                                <div key={medicine.drug_id || medicine.drug_name || index} className="doctor-topbar__search-item">
                                                    <span className="doctor-topbar__search-tag">Drug</span>
                                                    <span>{medicine.drug_name || medicine.name || "Medicine"}</span>
                                                </div>
                                            ))}
                                            {results.diseases.map((disease) => (
                                                <div key={disease.disease_id} className="doctor-topbar__search-item">
                                                    <span className="doctor-topbar__search-tag doctor-topbar__search-tag--disease">Disease</span>
                                                    <span>{disease.disease_name}</span>
                                                </div>
                                            ))}
                                        </>
                                    )}
                                </>
                            )}
                        </div>
                    )}
                </div>

                <div className="doctor-topbar__user">
                    <div className="doctor-topbar__avatar">
                        {initials}
                    </div>

                    <div>
                        <strong>
                            {name}
                        </strong>

                        <span>
                            {user?.username || ""}
                        </span>
                    </div>
                </div>

            </div>

        </header>
    );
}

export default DoctorTopbar;
