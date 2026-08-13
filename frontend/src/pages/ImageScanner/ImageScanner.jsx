import { useState } from "react";
import { scanMedicine } from "../../services/ocrService";
import Loading from "../../components/Loading/Loading";
import MedicineCard from "../../components/MedicineCard/MedicineCard";
import "./ImageScanner.css";

function ImageScanner() {
  const [lang, setLang] = useState("en");
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const medicineDetails = result?.ocr_result?.medicine_details ?? null;
  const scanStatus = result?.ocr_result?.status;
  const notFoundMessage = result?.ocr_result?.message;

  const handleImageChange = (event) => {
    const selectedFile = event.target.files[0];

    if (!selectedFile) return;

    setImage(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError("");
  };

  const handleScan = async () => {
    if (!image) {
      setError("Please select a medicine image.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await scanMedicine(image, lang);

      setResult(response);
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to scan the medicine image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scanner-page">
      <div className="scanner-card">

        <h1>OCR Medicine Scanner</h1>

        <p>
          Upload a medicine strip or tablet image to identify the medicine.
        </p>

        <label className="scanner-language-selector">
          <span>Language</span>
          <select value={lang} onChange={(event) => setLang(event.target.value)}>
            <option value="en">English</option>
            <option value="kn">Kannada</option>
            <option value="tulu">Tulu</option>
          </select>
        </label>

        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
        />

        {preview && (
          <div className="preview-section">
            <img
              src={preview}
              alt="Medicine Preview"
              className="preview-image"
            />
          </div>
        )}

        <button
          className="scan-btn"
          onClick={handleScan}
          disabled={loading}
        >
          {loading ? "Scanning..." : "Scan Medicine"}
        </button>

        {loading && <Loading />}

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {result && (
          <div className="result-box">

            <h2>Scan Result</h2>

            <p>
              <strong>File :</strong> {result.filename}
            </p>

            <p>
              <strong>Medicine :</strong>{" "}
              {scanStatus === "success"
                ? result.ocr_result.detected_medicine
                : "Not Detected"}
            </p>

            {scanStatus === "success" && medicineDetails && (
              <MedicineCard medicine={medicineDetails} />
            )}

            {scanStatus !== "success" && (
              <MedicineCard medicine={null} />
            )}

            {scanStatus === "not_found" && notFoundMessage && (
              <p className="scan-not-found-message">{notFoundMessage}</p>
            )}

          </div>
        )}

      </div>
    </div>
  );
}

export default ImageScanner;