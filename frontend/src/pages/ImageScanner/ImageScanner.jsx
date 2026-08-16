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

  const medicineDetails =
    result?.ocr_result?.medicine_details ?? null;

  const scanStatus = result?.ocr_result?.status;
  const notFoundMessage = result?.ocr_result?.message;

  const handleImageChange = (event) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    setImage(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError("");
  };

  const handleScan = async () => {
    if (!image) {
      setError("Please upload or take a prescription photo.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await scanMedicine(image, lang);

      setResult(response);
    } catch (err) {
      console.error("OCR error:", err);
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        "Unable to scan the prescription."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scanner-page">
      <div className="scanner-card">

        <p className="scanner-kicker">
          PRESCRIPTION OCR
        </p>

        <h1>Scan Your Prescription</h1>

        <p className="scanner-description">
          Upload a prescription image or take a photo.
          OCR will automatically detect available medicine information.
        </p>

        {/* Language */}

        <label className="scanner-language-selector">
          <span>Language</span>

          <select
            value={lang}
            onChange={(event) => setLang(event.target.value)}
          >
            <option value="en">English</option>
            <option value="kn">Kannada</option>
            <option value="tulu">Tulu</option>
          </select>
        </label>

        {/* Image options */}

        <div className="scanner-options">

          {/* Upload */}

          <label className="scanner-option">
            <div className="scanner-option-icon">
              📁
            </div>

            <div>
              <strong>Upload Prescription</strong>

              <span>
                Choose an image from your device
              </span>
            </div>

            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              hidden
            />
          </label>

          {/* Camera */}

          <label className="scanner-option">
            <div className="scanner-option-icon">
              📷
            </div>

            <div>
              <strong>Take Prescription Photo</strong>

              <span>
                Use your device camera
              </span>
            </div>

            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleImageChange}
              hidden
            />
          </label>

        </div>

        {/* Preview */}

        {preview && (
          <div className="preview-section">

            <p className="preview-label">
              Prescription Preview
            </p>

            <img
              src={preview}
              alt="Prescription Preview"
              className="preview-image"
            />

          </div>
        )}

        {/* Scan */}

        <button
          className="scan-btn"
          onClick={handleScan}
          disabled={loading || !image}
        >
          {loading
            ? "Scanning Prescription..."
            : "Scan Prescription"}
        </button>

        {loading && <Loading />}

        {/* Error */}

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {/* Result */}

        {result && (
          <div className="result-box">

            <h2>OCR Result</h2>

            <p>
              <strong>File:</strong>{" "}
              {result.filename}
            </p>

            <p>
              <strong>Medicine:</strong>{" "}
              {scanStatus === "success"
                ? result.ocr_result.detected_medicine
                : "Not Detected"}
            </p>

            {scanStatus === "success" && medicineDetails && (
              <MedicineCard
                medicine={medicineDetails}
              />
            )}

            {scanStatus !== "success" && (
              <MedicineCard medicine={null} />
            )}

            {scanStatus === "not_found" &&
              notFoundMessage && (
                <p className="scan-not-found-message">
                  {notFoundMessage}
                </p>
              )}

          </div>
        )}

      </div>
    </div>
  );
}

export default ImageScanner;