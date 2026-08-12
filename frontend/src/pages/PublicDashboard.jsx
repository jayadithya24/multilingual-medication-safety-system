import { useState } from "react";
import DashboardCard from "../components/DashboardCard";
import { uploadPrescription, searchDrug } from "../services/api";

function PublicDashboard() {
  const [file, setFile] = useState(null);
  const [ocrResult, setOcrResult] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files?.[0] || null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a prescription image to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setOcrResult(null);
    setSearchResults([]);

    try {
      const uploadResponse = await uploadPrescription(file);
      setOcrResult(uploadResponse.ocr_result);

      if (uploadResponse.ocr_result?.medicine) {
        const term = uploadResponse.ocr_result.medicine;
        const searchData = await searchDrug(term);
        setSearchResults(searchData.results || []);
      }
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell">
      <section className="section-header">
        <span className="hero__kicker">Public access</span>
        <h1>Public Dashboard</h1>
        <p>
          A friendly entry point for medicine lookup, prescription upload, and
          simple drug guidance.
        </p>
      </section>

      <div className="dashboard-grid">
        <DashboardCard title="Medicine Search" badge="Search" description="Look up drug names and basic safety information." />

        <DashboardCard title="Upload Prescription" badge="OCR" description="Capture prescription details from an image or file." />

        <DashboardCard title="Voice Search" badge="Assistive" description="Search by speaking for hands-free access." />

        <DashboardCard title="Drug Information" badge="Guide" description="Review usage, warnings, and interaction notes." />
      </div>

      <div className="upload-panel">
        <h2>Upload Prescription</h2>
        <input type="file" accept="image/*" onChange={handleFileChange} />
        <button type="button" onClick={handleUpload} disabled={loading}>
          {loading ? "Scanning..." : "Scan prescription"}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {ocrResult && (
        <div className="upload-summary">
          <h2>OCR Result</h2>
          <p>Detected medicine: {ocrResult.medicine}</p>
          <p>Confidence: {(ocrResult.confidence * 100).toFixed(0)}%</p>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="search-results">
          <h2>Search Results</h2>
          {searchResults.map((result) => (
            <div key={result.drug_id} className="result-card">
              <div className="result-card__header">
                <div>
                  <span className="feature-card__badge">Found</span>
                  <h3>{result.drug_name}</h3>
                </div>
                <span className="status-pill">{result.drug_class || "Drug"}</span>
              </div>
              <p>{result.description_en || "No description available."}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PublicDashboard;
