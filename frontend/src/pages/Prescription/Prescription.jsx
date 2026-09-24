import { useState, useRef, useEffect } from "react";
import api from "../../services/api";
import { getStoredToken } from "../../services/api";
import { registerMedicationNotifications } from "../../services/fcmService";
import { Link } from "react-router-dom";
import MedicineCard from "../../components/MedicineCard/MedicineCard";
import VoicePlayback from "../../components/VoicePlayback";
import "./Prescription.css";

function Prescription() {
    const [lang, setLang] = useState("en");
    const [medicineDetails, setMedicineDetails] = useState(null);
    const [notificationMessage, setNotificationMessage] = useState("");
    const [spokenScan, setSpokenScan] = useState("");
    const [speechRun, setSpeechRun] = useState(0);
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
        setMedicineDetails(null);
        setSpokenScan("");
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
            setSpokenScan("");
            setMedicineDetails(null);

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
useEffect(() => () => {
    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
}, []);
useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
}, [preview]);
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
            setSpokenScan("");
            setMedicineDetails(null);
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
                formData,
                {
                    timeout: 300000,
                    params: { lang },
                }
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
            setMedicineDetails(ocrResult.medicine_details || null);
            const detectedSummary = [ocrResult.medicine, ocrResult.dosage, ocrResult.instructions].filter(Boolean).join(". ");
            const reviewNotice = {
                en: "These are detected details. Check them against your prescription before saving.",
                kn: "ಬಳಸುವ ಮೊದಲು ಈ ವಿವರಗಳನ್ನು ನಿಮ್ಮ ಔಷಧ ಚೀಟಿಯೊಂದಿಗೆ ಪರಿಶೀಲಿಸಿ.",
                tulu: "ಬಳಕೆ ಮಲ್ಪುನ ದುಂಬು ಈ ವಿವರಣ್ ಈರ್ನ ಔಷಧ ಚೀಟಿ ದ ಒಟ್ಟು ಪರಿಶೀಲನೆ ಮಲ್ಪುಲೆ.",
            };
            setSpokenScan(detectedSummary ? `${detectedSummary}. ${reviewNotice[lang]}` : "");
            setSpeechRun((value) => value + 1);
            setMedicineName(ocrResult.medicine || "");
            setDosage(ocrResult.dosage || "");
            setInstructions(ocrResult.instructions || "");

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
                    `${ocrResult.message || "Some details could not be detected. Please enter the missing information manually."}${ocrResult.raw_text ? ` Detected text: ${ocrResult.raw_text}` : ""}`
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
            (scheduledTimes.length === 0 || scheduledTimes.some((time) => !/^\d{2}:\d{2}$/.test(time)))
        ) {
            setError(
                "Please add at least one dosing time."
            );
            return;
        }

        try {
            setSaving(true);

            if (!getStoredToken()) {
                throw new Error("Please log in again before adding a medication to your schedule.");
            }

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

            setNotificationMessage("");
            if (reminderEnabled) {
                try {
                    const result = await registerMedicationNotifications();
                    if (!result.registered) setNotificationMessage("Schedule saved. Browser reminders are unavailable on this device.");
                } catch {
                    setNotificationMessage("Schedule saved. Browser reminders could not be enabled. You can retry from My Medicines.");
                }
            }

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
                (Array.isArray(detail) ? detail.map((item) => item.msg).join(". ") : detail) || err.message ||
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
                    Scan &amp; Add Medicines
                </h1>

                <p>
                    Scan a medicine label or prescription, view medicine information,
                    or enter details manually. Review everything before adding a schedule.
                </p>

            </section>



            {/* OCR */}

            <section className="prescription-card">

                <div className="prescription-card__header">

                    <span>
                        PRESCRIPTION OCR
                    </span>

                    <h2>
                        Scan a Label or Prescription
                    </h2>

                    <p>
                        OCR will automatically fill
                        the information it can detect.
                        You can edit everything before
                        saving.
                    </p>

                </div>


                <div className="prescription-ocr">
                    <label className="prescription-field">
                        <span>Language</span>
                        <select aria-label="Language" value={lang} onChange={(event) => { setLang(event.target.value); setMedicineDetails(null); setSpokenScan(""); }} disabled={ocrLoading}>
                            <option value="en">English</option>
                            <option value="kn">Kannada</option>
                            <option value="tulu">Tulu</option>
                        </select>
                    </label>

                    <div className="prescription-image-options">

    {/* Upload Prescription */}

    <label className="prescription-image-option">

        <div className="prescription-image-option__icon">
            📁
        </div>

        <div>
            <strong>
                Upload Image
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
                Take Photo
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
                            : "Scan Image"}
                    </button>


                    {ocrMessage && (

                        <div className="prescription-ocr-message">
                            {ocrMessage}
                        </div>

                    )}
                    {spokenScan && (
                        <div aria-label="Prescription read aloud">
                            <VoicePlayback key={speechRun} text={spokenScan} language={lang} />
                            <button type="button" className="prescription-add-time" onClick={() => setSpeechRun((value) => value + 1)}>Read scan aloud again</button>
                            <button type="button" className="prescription-add-time" onClick={() => setSpokenScan("")}>Stop reading</button>
                        </div>
                    )}

                </div>

            </section>


            {/* Manual / OCR Details */}
            {medicineDetails && <MedicineCard medicine={medicineDetails} />}
            {cameraError && !cameraOpen && <div className="prescription-error">{cameraError}</div>}
            {notificationMessage && <p role="status">{notificationMessage}</p>}

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


                <form onSubmit={handleSubmit} onChange={() => setSaved(false)}>
                    <fieldset disabled={ocrLoading || saving} style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}>

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

                            <p className="prescription-reminder-note">
                                Allow browser notifications when asked. Reminders appear as browser popups and are not a guaranteed alarm if notifications, the browser, or the device blocks background activity.
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
                        disabled={saving || saved || !getStoredToken()}
                    >
                        {saving
                            ? "Adding to Schedule..."
                            : "Add to Schedule"}
                    </button>
                    {!getStoredToken() && <p><Link to="/public">Log in as a patient</Link> to save a medication schedule.</p>}
                    </fieldset>

                </form>

            </section>

        </div>
    );
}

export default Prescription;
