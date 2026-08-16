import { useState } from "react";
import { searchMedicine } from "../../services/medicineService";
import "./DrugReference.css";

function DrugReference() {
    const [searchTerm, setSearchTerm] = useState("");
    const [results, setResults] = useState([]);
    const [selectedDrug, setSelectedDrug] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSearch = async (event) => {
        event.preventDefault();

        if (!searchTerm.trim()) {
            setError("Please enter a medicine name.");
            return;
        }

        try {
            setLoading(true);
            setError("");
            setSelectedDrug(null);

            const response = await searchMedicine(searchTerm.trim());

            // Your backend returns { results: [...] }
            setResults(response.results || []);
        } catch (err) {
            console.error(err);
            setError("Unable to search medicines.");
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectDrug = (drug) => {
        setSelectedDrug(drug);
    };

    return (
        <div className="drug-reference-page">

            {/* Header */}
            <section className="drug-reference-hero">
                <p className="drug-reference-kicker">
                    MEDICATION REFERENCE
                </p>

                <h1>
                    Drug Reference
                </h1>

                <p>
                    Search medicine information, warnings,
                    contraindications, and safety details.
                </p>
            </section>


            {/* Search */}
            <section className="drug-reference-search">

                <form onSubmit={handleSearch}>

                    <div className="drug-reference-search-box">
                        <span>⌕</span>

                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(event) =>
                                setSearchTerm(event.target.value)
                            }
                            placeholder="Search medicine name..."
                        />

                        <button
                            type="submit"
                            disabled={loading}
                        >
                            {loading ? "Searching..." : "Search"}
                        </button>
                    </div>

                </form>

                {error && (
                    <div className="drug-reference-error">
                        {error}
                    </div>
                )}

            </section>


            {/* Search Results */}
            {results.length > 0 && (
                <section className="drug-reference-section">

                    <div className="drug-reference-section-header">
                        <div>
                            <h2>Search Results</h2>
                            <p>
                                Medicines matching your search.
                            </p>
                        </div>
                    </div>


                    <div className="drug-reference-results">

                        {results.map((drug, index) => (
                            <button
                                key={
                                    drug.drug_id ||
                                    drug.drug_name ||
                                    index
                                }
                                className="drug-result-card"
                                onClick={() =>
                                    handleSelectDrug(drug)
                                }
                            >

                                <div className="drug-result-icon">
                                    💊
                                </div>

                                <div className="drug-result-content">

                                    <h3>
                                        {drug.drug_name}
                                    </h3>

                                    <p>
                                        Generic:{" "}
                                        {drug.generic_name || "Not available"}
                                    </p>

                                    <span>
                                        {drug.drug_class || "Medicine"}
                                    </span>

                                </div>

                                <div className="drug-result-arrow">
                                    →
                                </div>

                            </button>
                        ))}

                    </div>

                </section>
            )}


            {/* Drug Details */}
            {selectedDrug && (
                <section className="drug-details">

                    <div className="drug-details-header">

                        <div>
                            <p className="drug-details-kicker">
                                DRUG INFORMATION
                            </p>

                            <h2>
                                {selectedDrug.drug_name}
                            </h2>

                            <p>
                                {selectedDrug.generic_name}
                            </p>
                        </div>

                        <button
                            className="drug-details-close"
                            onClick={() =>
                                setSelectedDrug(null)
                            }
                        >
                            ×
                        </button>

                    </div>


                    <div className="drug-details-grid">

                        <div className="drug-info-card">
                            <span>Drug Class</span>
                            <strong>
                                {selectedDrug.drug_class ||
                                    "Not available"}
                            </strong>
                        </div>


                        <div className="drug-info-card">
                            <span>Active Ingredient</span>
                            <strong>
                                {selectedDrug.active_ingredient ||
                                    "Not available"}
                            </strong>
                        </div>

                    </div>


                    {/* Description */}
                    <div className="drug-details-block">
                        <h3>Description</h3>

                        <p>
                            {selectedDrug.description_en ||
                                "No description available."}
                        </p>
                    </div>


                    {/* Warnings */}
                    <div className="drug-details-block drug-details-block--warning">

                        <h3>
                            ⚠ Warnings
                        </h3>

                        <p>
                            {selectedDrug.warnings_en ||
                                "No warnings available."}
                        </p>

                    </div>


                    {/* Contraindications */}
                    <div className="drug-details-block">

                        <h3>
                            Contraindications
                        </h3>

                        <p>
                            {selectedDrug.contraindications_en ||
                                "No contraindications available."}
                        </p>

                    </div>


                    {/* Interactions */}
                    <div className="drug-details-block">

                        <h3>
                            Drug Interactions
                        </h3>

                        {selectedDrug.interactions?.length > 0 ? (

                            <div className="drug-interactions-list">

                                {selectedDrug.interactions.map(
                                    (interaction, index) => (
                                        <div
                                            key={index}
                                            className="drug-interaction-item"
                                        >
                                            <strong>
                                                {interaction.drug_name}
                                            </strong>

                                            {interaction.severity && (
                                                <span>
                                                    {interaction.severity}
                                                </span>
                                            )}

                                            {interaction.description && (
                                                <p>
                                                    {interaction.description}
                                                </p>
                                            )}
                                        </div>
                                    )
                                )}

                            </div>

                        ) : (

                            <p>
                                No known interactions found
                                in the current dataset.
                            </p>

                        )}

                    </div>

                </section>
            )}

        </div>
    );
}

export default DrugReference;