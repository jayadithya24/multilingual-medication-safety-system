import { useState, useRef, useEffect } from "react";
import api from "../../services/api";
import "./Prescription.css";

function Prescription() {
    const [medicineName, setMedicineName] = useState("");
    const [dosage, setDosage] = useState("");
    const [instructions, setInstructions] = useState("");

    const [frequency, setFrequency] = useState("Once Daily");
    const [scheduledTimes, setScheduledTimes] = useState(["08:00"]);
    const [reminderEnabled, setReminderEnabled] = useState(true);

    // OCR
    const [prescriptionImage, setPrescriptionImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [ocrLoading, setOcrLoading] = useState(false);
    const [ocrMessage, setOcrMessage] = useState("");
    // Camera
const [cameraOpen, setCameraOpen] = useState(false);
const [cameraError, setCameraError] = useState("");

const videoRef = useRef(null);
const cameraStreamRef = useRef(null);

    // Schedule
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState("");

    // --------------------------------------------------
    // OCR image selection
    // --------------------------------------------------

    const handlePrescriptionImage = (event) => {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setPrescriptionImage(file);
        setPreview(URL.createObjectURL(file));

        setOcrMessage("");
        setError("");
        setSaved(false);
    };
// --------------------------------------------------
// Camera
// --------------------------------------------------

const openCamera = async () => {
    try {
        setCameraError("");

        if (!navigator.mediaDevices?.getUserMedia) {
            setCameraError(
                "Camera access is not supported by this browser."
            );
            return;
        }

        const stream =
            await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: {
                        ideal: "environment",
                    },
                },
                audio: false,
            });

        cameraStreamRef.current = stream;

        setCameraOpen(true);

    } catch (err) {
        console.error("Camera error:", err);

        if (err.name === "NotAllowedError") {
            setCameraError(
                "Camera permission was denied. Please allow camera access."
            );
        } else if (err.name === "NotFoundError") {
            setCameraError(
                "No camera was found on this device."
            );
        } else {
            setCameraError(
                "Unable to open the camera."
            );
        }
    }
};


const closeCamera = () => {
    if (cameraStreamRef.current) {
        cameraStreamRef.current
            .getTracks()
            .forEach((track) => track.stop());

        cameraStreamRef.current = null;
    }

    if (videoRef.current) {
        videoRef.current.srcObject = null;
    }

    setCameraOpen(false);
};


const capturePhoto = () => {
    if (!videoRef.current) {
        return;
    }

    const video = videoRef.current;

    if (!video.videoWidth || !video.videoHeight) {
        setCameraError(
            "Camera is not ready yet. Please wait a moment and try again."
        );
        return;
    }

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    canvas.toBlob(
        (blob) => {
            if (!blob) {
                setCameraError(
                    "Unable to capture the prescription photo."
                );
                return;
            }

            const capturedFile = new File(
                [blob],
                "prescription-camera.jpg",
                {
                    type: "image/jpeg",
                }
            );

            setPrescriptionImage(capturedFile);

            setPreview(
                URL.createObjectURL(blob)
            );

            setOcrMessage("");
            setError("");
            setSaved(false);

            closeCamera();
        },
        "image/jpeg",
        0.95
    );
};
useEffect(() => {
    if (cameraOpen && videoRef.current && cameraStreamRef.current) {
        videoRef.current.srcObject = cameraStreamRef.current;
    }
}, [cameraOpen]);
    // --------------------------------------------------
    // OCR scan
    // --------------------------------------------------

    const handlePrescriptionOCR = async () => {
        if (!prescriptionImage) {
            setOcrMessage(
                "Please select a prescription image first."
            );
            return;
        }

        try {
            setOcrLoading(true);
            setOcrMessage("");
            setError("");
            setSaved(false);

            const formData = new FormData();

            formData.append(
                "file",
                prescriptionImage
            );

            const response = await api.post(
                "/prescription-ocr",
                formData
            );

            console.log(
                "Prescription OCR response:",
                response.data
            );

            const ocrResult =
                response.data?.ocr_result;

            if (!ocrResult) {
                setOcrMessage(
                    "No OCR result was returned."
                );
                return;
            }

            // --------------------------------------------------
            // Fill only fields detected by OCR
            // --------------------------------------------------

            if (ocrResult.medicine) {
                setMedicineName(
                    ocrResult.medicine
                );
            }

            if (ocrResult.dosage) {
                setDosage(
                    ocrResult.dosage
                );
            }

            if (ocrResult.instructions) {
                setInstructions(
                    ocrResult.instructions
                );
            }

            if (ocrResult.status === "success") {
                setOcrMessage(
                    "Prescription details detected. Please verify them before scheduling."
                );
            } else {
                setOcrMessage(
                    ocrResult.message ||
                    "Some details could not be detected. Please enter the missing information manually."
                );
            }

        } catch (err) {
            console.error(
                "Prescription OCR error:",
                err
            );

            const detail =
                err?.response?.data?.detail;

            setOcrMessage(
                detail ||
                "Unable to read the prescription. Please enter the details manually."
            );

        } finally {
            setOcrLoading(false);
        }
    };

    // --------------------------------------------------
    // Frequency
    // --------------------------------------------------

    const handleFrequencyChange = (event) => {
        const value = event.target.value;

        setFrequency(value);

        if (value === "Once Daily") {
            setScheduledTimes(["08:00"]);
        }

        else if (value === "Twice Daily") {
            setScheduledTimes([
                "08:00",
                "20:00",
            ]);
        }

        else if (value === "Three Times Daily") {
            setScheduledTimes([
                "08:00",
                "14:00",
                "20:00",
            ]);
        }

        else if (value === "Four Times Daily") {
            setScheduledTimes([
                "08:00",
                "12:00",
                "16:00",
                "20:00",
            ]);
        }

        else if (value === "As Needed") {
            setScheduledTimes([]);
        }

        else if (value === "Custom") {
            setScheduledTimes([
                "08:00",
            ]);
        }

        setSaved(false);
    };

    // --------------------------------------------------
    // Dosing time
    // --------------------------------------------------

    const handleTimeChange = (
        index,
        value
    ) => {
        setScheduledTimes(
            (previous) =>
                previous.map(
                    (time, i) =>
                        i === index
                            ? value
                            : time
                )
        );

        setSaved(false);
    };

    const addTime = () => {
        setScheduledTimes(
            (previous) => [
                ...previous,
                "08:00",
            ]
        );

        setSaved(false);
    };

    const removeTime = (index) => {
        setScheduledTimes(
            (previous) =>
                previous.filter(
                    (_, i) =>
                        i !== index
                )
        );

        setSaved(false);
    };

    // --------------------------------------------------
    // Save schedule
    // --------------------------------------------------

    const handleSubmit = async (event) => {
        event.preventDefault();

        setError("");
        setSaved(false);

        if (!medicineName.trim()) {
            setError(
                "Please enter the medicine name."
            );
            return;
        }

        if (!dosage.trim()) {
            setError(
                "Please enter the dosage."
            );
            return;
        }

        if (
            frequency !== "As Needed" &&
            scheduledTimes.length === 0
        ) {
            setError(
                "Please add at least one dosing time."
            );
            return;
        }

        try {
            setSaving(true);

            const response =
                await api.post(
                    "/patient-schedule",
                    {
                        medicine_name:
                            medicineName.trim(),

                        dosage:
                            dosage.trim(),

                        instructions:
                            instructions.trim(),

                        frequency,

                        scheduled_times:
                            scheduledTimes,

                        reminder_enabled:
                            reminderEnabled,
                    }
                );

            console.log(
                "Medication schedule created:",
                response.data
            );

            setSaved(true);

            // Clear form
            setMedicineName("");
            setDosage("");
            setInstructions("");
            setFrequency(
                "Once Daily"
            );
            setScheduledTimes([
                "08:00",
            ]);
            setReminderEnabled(true);

            setPrescriptionImage(null);
            setPreview(null);
            setOcrMessage("");

        } catch (err) {
            console.error(
                "Medication schedule error:",
                err
            );

            const detail =
                err?.response?.data?.detail;

            setError(
                detail ||
                "Unable to add medication to your schedule."
            );

        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="prescription-page">

            {/* Header */}

            <section className="prescription-page__hero">

                <p className="prescription-page__kicker">
                    MEDICATION SCHEDULE
                </p>

                <h1>
                    Add Medication
                </h1>

                <p>
                    Upload a prescription for
                    automatic extraction or enter
                    the medication details manually.
                </p>

            </section>


            {/* OCR */}

            <section className="prescription-card">

                <div className="prescription-card__header">

                    <span>
                        PRESCRIPTION OCR
                    </span>

                    <h2>
                        Scan Your Prescription
                    </h2>

                    <p>
                        OCR will automatically fill
                        the information it can detect.
                        You can edit everything before
                        saving.
                    </p>

                </div>


                <div className="prescription-ocr">

                    <div className="prescription-image-options">

    {/* Upload Prescription */}

    <label className="prescription-image-option">

        <div className="prescription-image-option__icon">
            📁
        </div>

        <div>
            <strong>
                Upload Prescription
            </strong>

            <span>
                Choose an image from your device
            </span>
        </div>

        <input
            type="file"
            accept="image/*"
            onChange={handlePrescriptionImage}
            hidden
        />

    </label>


    {/* Take Prescription Photo */}

    <button
        type="button"
        className="prescription-image-option"
        onClick={openCamera}
    >

        <div className="prescription-image-option__icon">
            📷
        </div>

        <div>
            <strong>
                Take Prescription Photo
            </strong>

            <span>
                Use your device camera
            </span>
        </div>

    </button>

</div>
{/* Camera */}

{cameraOpen && (
    <div className="prescription-camera">

        <div className="prescription-camera__header">

            <h3>
                Take Prescription Photo
            </h3>

            <button
                type="button"
                className="prescription-camera__close"
                onClick={closeCamera}
            >
                ✕
            </button>

        </div>

        <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="prescription-camera__video"
        />

        {cameraError && (
            <div className="prescription-error">
                {cameraError}
            </div>
        )}

        <div className="prescription-camera__controls">

            <button
                type="button"
                className="prescription-camera__capture"
                onClick={capturePhoto}
            >
                📷 Capture Photo
            </button>

            <button
                type="button"
                className="prescription-camera__cancel"
                onClick={closeCamera}
            >
                Cancel
            </button>

        </div>

    </div>
)}



                    {preview && (

                        <div className="prescription-preview">

                            <img
                                src={preview}
                                alt="Prescription preview"
                            />

                        </div>

                    )}


                    <button
                        type="button"
                        className="prescription-submit"
                        onClick={
                            handlePrescriptionOCR
                        }
                        disabled={
                            ocrLoading ||
                            !prescriptionImage
                        }
                    >
                        {ocrLoading
                            ? "Scanning Prescription..."
                            : "Scan Prescription"}
                    </button>


                    {ocrMessage && (

                        <div className="prescription-ocr-message">
                            {ocrMessage}
                        </div>

                    )}

                </div>

            </section>


            {/* Manual / OCR Details */}

            <section className="prescription-card">

                <div className="prescription-card__header">

                    <span>
                        PRESCRIPTION DETAILS
                    </span>

                    <h2>
                        Medication Information
                    </h2>

                    <p>
                        Review the OCR results and
                        manually complete anything
                        that was not detected.
                    </p>

                </div>


                <form onSubmit={handleSubmit}>

                    {/* Medicine */}

                    <label className="prescription-field">

                        <span>
                            Medicine
                        </span>

                        <input
                            type="text"
                            value={medicineName}
                            onChange={(event) =>
                                setMedicineName(
                                    event.target.value
                                )
                            }
                            placeholder="e.g. Metformin"
                        />

                    </label>


                    {/* Dosage */}

                    <label className="prescription-field">

                        <span>
                            Dosage
                        </span>

                        <input
                            type="text"
                            value={dosage}
                            onChange={(event) =>
                                setDosage(
                                    event.target.value
                                )
                            }
                            placeholder="e.g. 500 mg"
                        />

                    </label>


                    {/* Instructions */}

                    <label className="prescription-field">

                        <span>
                            Instructions
                        </span>

                        <textarea
                            value={instructions}
                            onChange={(event) =>
                                setInstructions(
                                    event.target.value
                                )
                            }
                            placeholder="e.g. Take after breakfast"
                            rows="3"
                        />

                    </label>


                    {/* Frequency */}

                    <label className="prescription-field">

                        <span>
                            Frequency
                        </span>

                        <select
                            value={frequency}
                            onChange={
                                handleFrequencyChange
                            }
                        >

                            <option>
                                Once Daily
                            </option>

                            <option>
                                Twice Daily
                            </option>

                            <option>
                                Three Times Daily
                            </option>

                            <option>
                                Four Times Daily
                            </option>

                            <option>
                                As Needed
                            </option>

                            <option>
                                Custom
                            </option>

                        </select>

                    </label>


                    {/* Dosing Times */}

                    {frequency !== "As Needed" && (

                        <div className="prescription-times">

                            <div className="prescription-times__header">

                                <div>

                                    <span>
                                        DOSING TIMES
                                    </span>

                                    <h3>
                                        When should you take it?
                                    </h3>

                                </div>


                                {frequency === "Custom" && (

                                    <button
                                        type="button"
                                        onClick={addTime}
                                        className="prescription-add-time"
                                    >
                                        + Add Time
                                    </button>

                                )}

                            </div>


                            <div className="prescription-times__list">

                                {scheduledTimes.map(
                                    (time, index) => (

                                        <div
                                            className="prescription-time"
                                            key={index}
                                        >

                                            <span>
                                                Dose {index + 1}
                                            </span>

                                            <input
                                                type="time"
                                                value={time}
                                                onChange={
                                                    (event) =>
                                                        handleTimeChange(
                                                            index,
                                                            event.target.value
                                                        )
                                                }
                                            />


                                            {frequency === "Custom" &&
                                                scheduledTimes.length > 1 && (

                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            removeTime(index)
                                                        }
                                                        className="prescription-remove-time"
                                                    >
                                                        Remove
                                                    </button>

                                                )}

                                        </div>

                                    )
                                )}

                            </div>

                        </div>

                    )}


                    {/* Reminder */}

                    <div className="prescription-reminder">

                        <div>

                            <strong>
                                🔔 Medication Reminder
                            </strong>

                            <p>
                                Receive a reminder at the
                                scheduled dosing times.
                            </p>

                        </div>


                        <label className="prescription-switch">

                            <input
                                type="checkbox"
                                checked={
                                    reminderEnabled
                                }
                                onChange={(event) =>
                                    setReminderEnabled(
                                        event.target.checked
                                    )
                                }
                            />

                            <span></span>

                        </label>

                    </div>


                    {/* Notice */}

                    <div className="prescription-notice">

                        <strong>
                            ⚠ Please verify your prescription
                        </strong>

                        <p>
                            OCR may not detect every
                            prescription detail. Check the
                            medicine, dosage, instructions,
                            frequency, and dosing times before
                            adding it to your schedule.
                        </p>

                    </div>


                    {/* Error */}

                    {error && (

                        <div className="prescription-error">
                            {error}
                        </div>

                    )}


                    {/* Success */}

                    {saved && (

                        <div className="prescription-success">
                            ✓ Medication added to your
                            schedule successfully.
                        </div>

                    )}


                    {/* Save */}

                    <button
                        type="submit"
                        className="prescription-submit"
                        disabled={saving}
                    >
                        {saving
                            ? "Adding to Schedule..."
                            : "Add to Schedule"}
                    </button>

                </form>

            </section>

        </div>
    );
}

export default Prescription;