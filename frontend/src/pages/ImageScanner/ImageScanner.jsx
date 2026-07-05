import { useState } from "react";
import { uploadMedicineImage } from "../../services/ocrService";
import Loading from "../../components/Loading/Loading";
import "./ImageScanner.css";

function ImageScanner() {
    const [selectedImage, setSelectedImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleImageChange = (e) => {
        const file = e.target.files[0];

        if (!file) return;

        setSelectedImage(file);
        setPreview(URL.createObjectURL(file));
        setResult(null);
    };

    const handleScan = async () => {

        if (!selectedImage) {
            alert("Please select an image.");
            return;
        }

        try {

            setLoading(true);

            const response = await uploadMedicineImage(selectedImage);

            setResult(response);

        } catch (error) {

            console.error(error);

            alert("Failed to scan image.");

        } finally {

            setLoading(false);

        }

    };

    return (

        <div className="scanner-page">

            <h1>OCR Medicine Scanner</h1>

            <p>
                Upload a medicine strip or tablet image to detect the medicine.
            </p>

            <div className="scanner-card">

                <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                />

                {preview && (
                    <img
                        src={preview}
                        alt="Preview"
                        className="preview-image"
                    />
                )}

                <button onClick={handleScan}>
                    Scan Medicine
                </button>

                {loading && <Loading />}

                {result && (

                    <div className="result-card">

                        <h2>Medicine Detected</h2>

                        <p>

                            <strong>Name :</strong>{" "}
                            {result.ocr_result.medicine}

                        </p>

                        <p>

                            <strong>Confidence :</strong>{" "}
                            {(result.ocr_result.confidence * 100).toFixed(0)}%

                        </p>

                    </div>

                )}

            </div>

        </div>

    );
}

export default ImageScanner;