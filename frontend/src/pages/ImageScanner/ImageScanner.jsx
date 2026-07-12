import { useState } from "react";
import { scanMedicine } from "../../services/ocrService";
import Loading from "../../components/Loading/Loading";
import "./ImageScanner.css";

function ImageScanner() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

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

      const response = await scanMedicine(image);

      setResult(response);
    } catch (err) {
      console.error(err);
      setError("Unable to scan the medicine image.");
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
        >
          Scan Medicine
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
              {result.ocr_result.medicine ?? "Not Detected"}
            </p>

            <h3>Detected Text</h3>

            <ul>
              {(result.ocr_result.all_text ||
                result.ocr_result.detected_text ||
                []).map((text, index) => (
                <li key={index}>{text}</li>
              ))}
            </ul>

          </div>
        )}

      </div>
    </div>
  );
}

export default ImageScanner;