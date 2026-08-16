import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import Loading from "../../components/Loading/Loading";
import MedicineCard from "../../components/MedicineCard/MedicineCard";

import { searchMedicine, fetchMedicines } from "../../services/medicineService";
import { scanMedicine } from "../../services/ocrService";
import { sendVoiceSearchAudio } from "../../services/voiceService";


import {
    fetchPatientSchedule,
    markMedicineAsTaken,
    fetchMedicationHistory,
} from "../../services/patientScheduleService";

import "./PublicDashboard.css";

const languageOptions = [
    { value: "en", label: "English" },
    { value: "kn", label: "Kannada" },
    { value: "tulu", label: "Tulu" },
];

function PublicDashboard() {
    const [activeTab, setActiveTab] = useState("text");
    const [lang, setLang] = useState("en");

    // Medicine search
    const [medicineNames, setMedicineNames] = useState([]);
    const [query, setQuery] = useState("");
    const [textLoading, setTextLoading] = useState(false);
    const [textError, setTextError] = useState("");
    const [textResult, setTextResult] = useState(null);

    // OCR
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState("");
    const [ocrLoading, setOcrLoading] = useState(false);
    const [ocrError, setOcrError] = useState("");
    const [ocrResult, setOcrResult] = useState(null);
const [cameraOpen, setCameraOpen] = useState(false);
const [cameraError, setCameraError] = useState("");

const videoRef = useRef(null);
const cameraStreamRef = useRef(null);
    // Voice
    const [audioFile, setAudioFile] = useState(null);
    const [audioPreview, setAudioPreview] = useState("");
    const [voiceLoading, setVoiceLoading] = useState(false);
    const [voiceError, setVoiceError] = useState("");
    const [voiceResult, setVoiceResult] = useState(null);
    const [isRecording, setIsRecording] = useState(false);

    // Patient medication
    const [schedules, setSchedules] = useState([]);
    const [history, setHistory] = useState([]);
    const [scheduleLoading, setScheduleLoading] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [scheduleError, setScheduleError] = useState("");
    const [historyError, setHistoryError] = useState("");
    const [takingMedicineId, setTakingMedicineId] = useState(null);

    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const fileInputRef = useRef(null);

    // Load medicine names
    useEffect(() => {
        let isMounted = true;

        const loadMedicines = async () => {
            try {
                const response = await fetchMedicines(lang);

                if (isMounted) {
                    setMedicineNames(response.medicines || []);
                }
            } catch (error) {
                console.error(error);

                if (isMounted) {
                    setMedicineNames([]);
                }
            }
        };

        loadMedicines();

        return () => {
            isMounted = false;
        };
    }, [lang]);

    // Load patient schedule/history when My Medicines tab opens
    useEffect(() => {
        if (activeTab === "medicines") {
            loadPatientMedication();
        }
    }, [activeTab]);

    // Cleanup
    useEffect(() => {
        return () => {
            if (imagePreview) {
                URL.revokeObjectURL(imagePreview);
            }

            if (audioPreview) {
                URL.revokeObjectURL(audioPreview);
            }

            if (mediaStreamRef.current) {
                mediaStreamRef.current
                    .getTracks()
                    .forEach((track) => track.stop());
            }
             if (cameraStreamRef.current) {
            cameraStreamRef.current
                .getTracks()
                .forEach((track) => track.stop());
        }
        };
    }, [imagePreview, audioPreview]);

    // -----------------------------
    // TEXT SEARCH
    // -----------------------------

    const resetTextState = () => {
        setTextError("");
        setTextResult(null);
    };

    const handleSearch = async () => {
        if (!query.trim()) {
            setTextError("Enter a medicine name first.");
            return;
        }

        try {
            setTextLoading(true);
            resetTextState();

            const response = await searchMedicine(query.trim(), lang);
            setTextResult(response);
        } catch (error) {
            console.error(error);
            setTextError(
                "Unable to search for that medicine right now."
            );
        } finally {
            setTextLoading(false);
        }
    };

    // -----------------------------
    // OCR
    // -----------------------------

    const resetOcrState = () => {
        setOcrError("");
        setOcrResult(null);
    };

    const handleImageChange = (event) => {
        const selectedFile = event.target.files?.[0];

        if (!selectedFile) {
            return;
        }

        if (imagePreview) {
            URL.revokeObjectURL(imagePreview);
        }

        setImageFile(selectedFile);
        setImagePreview(URL.createObjectURL(selectedFile));
        resetOcrState();
    };

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

        setTimeout(() => {
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        }, 100);

    } catch (error) {
        console.error("Camera error:", error);

        if (error.name === "NotAllowedError") {
            setCameraError(
                "Camera permission was denied. Please allow camera access."
            );
        } else if (error.name === "NotFoundError") {
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
                    "Unable to capture the photo."
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

            if (imagePreview) {
                URL.revokeObjectURL(imagePreview);
            }

            setImageFile(capturedFile);

            setImagePreview(
                URL.createObjectURL(blob)
            );

            resetOcrState();

            closeCamera();
        },
        "image/jpeg",
        0.95
    );
};

    const handleOcrScan = async () => {
        if (!imageFile) {
            setOcrError("Please upload a medicine image first.");
            return;
        }

        try {
            setOcrLoading(true);
            resetOcrState();

            const response = await scanMedicine(imageFile, lang);
            setOcrResult(response);
        } catch (error) {
            console.error(error);

            setOcrError(
                error.message ||
                "Unable to scan the medicine image."
            );
        } finally {
            setOcrLoading(false);
        }
    };

    // -----------------------------
    // VOICE
    // -----------------------------

    const resetVoiceState = () => {
        setVoiceError("");
        setVoiceResult(null);
    };

    const handleAudioFileChange = (event) => {
        const selectedFile = event.target.files?.[0];

        if (!selectedFile) {
            return;
        }

        if (audioPreview) {
            URL.revokeObjectURL(audioPreview);
        }

        setAudioFile(selectedFile);
        setAudioPreview(URL.createObjectURL(selectedFile));
        resetVoiceState();
    };

    const startRecording = async () => {
        try {
            resetVoiceState();

            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true,
                });

            mediaStreamRef.current = stream;

            const preferredMimeType = [
                "audio/webm;codecs=opus",
                "audio/webm",
                "audio/mp4",
            ].find(
                (mimeType) =>
                    window.MediaRecorder &&
                    MediaRecorder.isTypeSupported(mimeType)
            );

            const mediaRecorder = preferredMimeType
                ? new MediaRecorder(stream, {
                    mimeType: preferredMimeType,
                })
                : new MediaRecorder(stream);

            chunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const recordingBlob = new Blob(
                    chunksRef.current,
                    {
                        type:
                            mediaRecorder.mimeType ||
                            "audio/webm",
                    }
                );

                const recordingFile = new File(
                    [recordingBlob],
                    "voice-search.webm",
                    {
                        type:
                            recordingBlob.type ||
                            "audio/webm",
                    }
                );

                if (audioPreview) {
                    URL.revokeObjectURL(audioPreview);
                }

                setAudioFile(recordingFile);
                setAudioPreview(
                    URL.createObjectURL(recordingBlob)
                );

                mediaStreamRef.current
                    ?.getTracks()
                    .forEach((track) => track.stop());

                mediaStreamRef.current = null;
                chunksRef.current = [];
            };

            mediaRecorder.start();

            mediaRecorderRef.current = mediaRecorder;
            setIsRecording(true);
        } catch (error) {
            console.error(error);
            setVoiceError(
                "Unable to access the microphone."
            );
        }
    };

    const stopRecording = () => {
        if (
            !mediaRecorderRef.current ||
            mediaRecorderRef.current.state !== "recording"
        ) {
            return;
        }

        mediaRecorderRef.current.stop();
        setIsRecording(false);
    };

    const handleVoiceSearch = async () => {
        if (!audioFile) {
            setVoiceError(
                "Please record or upload an audio file first."
            );
            return;
        }

        try {
            setVoiceLoading(true);
            resetVoiceState();

            const response =
                await sendVoiceSearchAudio(
                    audioFile,
                    lang
                );

            setVoiceResult(response);
        } catch (error) {
            console.error(error);

            setVoiceError(
                "Unable to process the voice search request."
            );
        } finally {
            setVoiceLoading(false);
        }
    };

    // -----------------------------
    // PATIENT MEDICATION
    // -----------------------------

    const loadPatientMedication = async () => {
        try {
            setScheduleLoading(true);
            setHistoryLoading(true);

            setScheduleError("");
            setHistoryError("");

            const [scheduleResponse, historyResponse] =
                await Promise.all([
                    fetchPatientSchedule(),
                    fetchMedicationHistory(),
                ]);

            setSchedules(
                scheduleResponse.schedules || []
            );

            setHistory(
                historyResponse.history || []
            );
        } catch (error) {
            console.error(error);

            const status = error?.response?.status;

            if (status === 401) {
                setScheduleError(
                    "Your session has expired. Please login again."
                );
            } else if (status === 403) {
                setScheduleError(
                    "Only patient accounts can access medication schedules."
                );
            } else {
                setScheduleError(
                    "Unable to load your medication schedule."
                );
            }

            setSchedules([]);
            setHistory([]);
        } finally {
            setScheduleLoading(false);
            setHistoryLoading(false);
        }
    };

    const handleMarkAsTaken = async (scheduleId) => {
        try {
            setTakingMedicineId(scheduleId);

            await markMedicineAsTaken(scheduleId);

            // Reload schedule + history after marking medicine taken
            await loadPatientMedication();
        } catch (error) {
            console.error(error);

            alert(
                error?.response?.data?.detail ||
                "Unable to mark medicine as taken."
            );
        } finally {
            setTakingMedicineId(null);
        }
    };

    // -----------------------------
    // RESULTS
    // -----------------------------

    const textMedicine = textResult?.medicine ?? null;

    const ocrMedicine =
        ocrResult?.ocr_result?.medicine_details ?? null;

    const voiceMedicine =
        voiceResult?.medicine_details ?? null;

    return (
        <div className="patient-portal">
            <section className="patient-shell">

                {/* HERO */}
                <div className="patient-hero">
                    <p className="patient-kicker">
                        Patient Portal
                    </p>

                    <h1>
                        My Medication Dashboard
                    </h1>

                    <p>
                        Search medicines, scan medicine strips,
                        use voice search, and manage your
                        medication schedule.
                    </p>
                </div>

                {/* TOOLBAR */}
                <div className="patient-toolbar">

                    <div
                        className="patient-tabs"
                        role="tablist"
                        aria-label="Patient portal tabs"
                    >

                        <button
                            type="button"
                            className={`patient-tab ${
                                activeTab === "text"
                                    ? "is-active"
                                    : ""
                            }`}
                            onClick={() =>
                                setActiveTab("text")
                            }
                        >
                            Medicine Search
                        </button>

                        <button
                            type="button"
                            className={`patient-tab ${
                                activeTab === "ocr"
                                    ? "is-active"
                                    : ""
                            }`}
                            onClick={() =>
                                setActiveTab("ocr")
                            }
                        >
                            OCR Scan
                        </button>

                        <button
                            type="button"
                            className={`patient-tab ${
                                activeTab === "voice"
                                    ? "is-active"
                                    : ""
                            }`}
                            onClick={() =>
                                setActiveTab("voice")
                            }
                        >
                            Voice Search
                        </button>

                        <button
                            type="button"
                            className={`patient-tab ${
                                activeTab === "medicines"
                                    ? "is-active"
                                    : ""
                            }`}
                            onClick={() =>
                                setActiveTab("medicines")
                            }
                        >
                            My Medicines
                        </button>
                        <Link
    to="/prescription"
    className="patient-tab"
>
    Prescription
</Link>

<Link
    to="/patient-profile"
    className="patient-tab patient-profile-link"
>
    My Profile
</Link>

                    </div>

                    <label className="patient-language">
                        <span>Language</span>

                        <select
                            value={lang}
                            onChange={(event) =>
                                setLang(event.target.value)
                            }
                        >
                            {languageOptions.map(
                                (option) => (
                                    <option
                                        key={option.value}
                                        value={option.value}
                                    >
                                        {option.label}
                                    </option>
                                )
                            )}
                        </select>
                    </label>
                </div>

                {/* MAIN PANEL */}
                <div className="patient-panel">

                    {/* =========================
                        MEDICINE SEARCH
                    ========================= */}
                    {activeTab === "text" && (
                        <div className="patient-section">

                            <div className="patient-section__header">
                                <h2>
                                    Medicine Search
                                </h2>

                                <p>
                                    Search by drug name,
                                    generic name, or active
                                    ingredient.
                                </p>
                            </div>

                            <datalist id="patient-medicine-options">
                                {medicineNames.map(
                                    (medicine) => (
                                        <option
                                            key={medicine}
                                            value={medicine}
                                        />
                                    )
                                )}
                            </datalist>

                            <div className="patient-search-row">

                                <input
                                    type="text"
                                    list="patient-medicine-options"
                                    value={query}
                                    onChange={(event) =>
                                        setQuery(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Type a medicine name"
                                />

                                <button
                                    type="button"
                                    onClick={handleSearch}
                                    disabled={textLoading}
                                >
                                    {textLoading
                                        ? "Searching..."
                                        : "Search"}
                                </button>

                            </div>

                            {textLoading && <Loading />}

                            {textError && (
                                <div className="patient-error">
                                    {textError}
                                </div>
                            )}

                            {textResult && (
                                <div className="patient-result">

                                    {textMedicine ? (
                                        <MedicineCard
                                            medicine={
                                                textMedicine
                                            }
                                        />
                                    ) : (
                                        <div className="patient-empty">
                                            Medicine not found.
                                        </div>
                                    )}

                                </div>
                            )}
                        </div>
                    )}

                    {/* =========================
                        OCR
                    ========================= */}
                    {/* =========================
    OCR
========================= */}
{activeTab === "ocr" && (
    <div className="patient-section">

        <div className="patient-section__header">
            <p className="patient-section__kicker">
                PRESCRIPTION OCR
            </p>

            <h2>
                OCR Scan
            </h2>

            <p>
                Upload a prescription image or take a photo.
                OCR will automatically detect available
                medicine information.
            </p>
        </div>

        {/* OCR IMAGE OPTIONS */}
        <div className="ocr-options">

            {/* Upload Image */}
            <label className="ocr-option">
                <div className="ocr-option-icon">
                    📁
                </div>

                <div className="ocr-option-content">
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
                    onChange={handleImageChange}
                    hidden
                />
            </label>


            {/* Take Photo */}
            {/* Take Photo */}
<button
    type="button"
    className="ocr-option"
    onClick={openCamera}
>
    <div className="ocr-option-icon">
        📷
    </div>

    <div className="ocr-option-content">
        <strong>
            Take Prescription Photo
        </strong>

        <span>
            Use your device camera
        </span>
    </div>
</button>
        </div>
{/* =========================
    CAMERA
========================= */}

{cameraOpen && (
    <div className="camera-container">

        <div className="camera-header">

            <h3>
                Take Prescription Photo
            </h3>

            <button
                type="button"
                className="camera-close"
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
            className="camera-video"
        />

        <div className="camera-controls">

            <button
                type="button"
                className="camera-capture-button"
                onClick={capturePhoto}
            >
                📷 Capture Photo
            </button>

            <button
                type="button"
                className="camera-cancel-button"
                onClick={closeCamera}
            >
                Cancel
            </button>

        </div>

    </div>
)}

{cameraError && (
    <div className="patient-error">
        {cameraError}
    </div>
)}


        {/* IMAGE PREVIEW */}
        {imagePreview && (
            <div className="patient-preview">

                <p className="ocr-preview-label">
                    Prescription Preview
                </p>

                <img
                    src={imagePreview}
                    alt="Prescription preview"
                />

            </div>
        )}


        {/* SCAN BUTTON */}
        <button
            type="button"
            onClick={handleOcrScan}
            disabled={ocrLoading || !imageFile}
        >
            {ocrLoading
                ? "Scanning Prescription..."
                : "Scan Prescription"}
        </button>


        {ocrLoading && <Loading />}


        {/* ERROR */}
        {ocrError && (
            <div className="patient-error">
                {ocrError}
            </div>
        )}


        {/* OCR RESULT */}
        {ocrResult && (
            <div className="patient-result">

                <h3>
                    OCR Result
                </h3>

                {ocrMedicine ? (
                    <MedicineCard
                        medicine={ocrMedicine}
                    />
                ) : (
                    <div className="patient-empty">
                        No medicine detected.
                        Please enter the prescription
                        details manually.
                    </div>
                )}

            </div>
        )}

    </div>
)}

                    {/* =========================
                        VOICE
                    ========================= */}
                    {activeTab === "voice" && (
                        <div className="patient-section">

                            <div className="patient-section__header">

                                <h2>
                                    Voice Search
                                </h2>

                                <p>
                                    Record a medicine name
                                    or upload an audio clip.
                                </p>

                            </div>

                            <div className="patient-voice-controls">

                                <button
                                    type="button"
                                    onClick={startRecording}
                                    disabled={
                                        voiceLoading ||
                                        isRecording
                                    }
                                >
                                    {isRecording
                                        ? "Recording..."
                                        : "Record"}
                                </button>

                                <button
                                    type="button"
                                    onClick={stopRecording}
                                    disabled={!isRecording}
                                >
                                    Stop
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        fileInputRef.current?.click()
                                    }
                                    disabled={voiceLoading}
                                >
                                    Upload Audio
                                </button>

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="audio/*"
                                    onChange={
                                        handleAudioFileChange
                                    }
                                    className="patient-hidden-input"
                                />

                            </div>

                            {audioPreview && (
                                <div className="patient-audio-preview">
                                    <audio
                                        controls
                                        src={audioPreview}
                                    />
                                </div>
                            )}

                            <button
                                type="button"
                                onClick={
                                    handleVoiceSearch
                                }
                                disabled={
                                    voiceLoading ||
                                    isRecording
                                }
                            >
                                {voiceLoading
                                    ? "Processing..."
                                    : "Search medicine"}
                            </button>

                            {(voiceLoading ||
                                isRecording) && (
                                <Loading />
                            )}

                            {voiceError && (
                                <div className="patient-error">
                                    {voiceError}
                                </div>
                            )}

                            {voiceResult && (
                                <div className="patient-result">

                                    {voiceMedicine ? (
                                        <MedicineCard
                                            medicine={
                                                voiceMedicine
                                            }
                                        />
                                    ) : (
                                        <div className="patient-empty">
                                            Medicine not found.
                                        </div>
                                    )}

                                </div>
                            )}

                        </div>
                    )}

                    {/* =========================
                        MY MEDICINES
                    ========================= */}
                    {activeTab === "medicines" && (
                        <div className="patient-section">

                            <div className="patient-section__header patient-medicines-header">

                                <div>
                                    <h2>
                                        My Medicines
                                    </h2>

                                    <p>
                                        View your medicine
                                        schedule and track
                                        medicines you have
                                        taken.
                                    </p>
                                </div>

                                <button
                                    type="button"
                                    className="patient-refresh-button"
                                    onClick={
                                        loadPatientMedication
                                    }
                                    disabled={
                                        scheduleLoading ||
                                        historyLoading
                                    }
                                >
                                    Refresh
                                </button>

                            </div>

                            {/* SCHEDULE */}
                            <div className="patient-medication-block">

                                <div className="patient-medication-title">
                                    <h3>
                                        💊 Medicine Schedule
                                    </h3>

                                    <span>
                                        {
                                            schedules.length
                                        }{" "}
                                        scheduled
                                    </span>
                                </div>

                                {scheduleLoading && (
                                    <Loading />
                                )}

                                {scheduleError && (
                                    <div className="patient-error">
                                        {scheduleError}
                                    </div>
                                )}

                                {!scheduleLoading &&
                                    !scheduleError &&
                                    schedules.length === 0 && (
                                        <div className="patient-empty">
                                            No medicines have
                                            been scheduled yet.
                                        </div>
                                    )}

                                <div className="patient-schedule-list">

                                    {schedules.map(
                                        (schedule) => (
                                            <div
                                                key={
                                                    schedule.schedule_id
                                                }
                                                className={`patient-schedule-card ${
                                                    schedule.status ===
                                                    "taken"
                                                        ? "is-taken"
                                                        : ""
                                                }`}
                                            >

                                                <div className="patient-schedule-main">

                                                    <div>
                                                        <h3>
                                                            {
                                                                schedule.medicine_name
                                                            }
                                                        </h3>

                                                        <p className="patient-dosage">
                                                            {
                                                                schedule.dosage
                                                            }
                                                        </p>
                                                    </div>

                                                    <span
                                                        className={`patient-status ${
                                                            schedule.status ===
                                                            "taken"
                                                                ? "taken"
                                                                : "pending"
                                                        }`}
                                                    >
                                                        {schedule.status ===
                                                        "taken"
                                                            ? "✓ Taken"
                                                            : "Pending"}
                                                    </span>

                                                </div>

                                                <div className="patient-schedule-details">

                                                    <div>
                                                        <span>
                                                            Time
                                                        </span>
                                                        <strong>
                                                            {
                                                                schedule.scheduled_time
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Frequency
                                                        </span>
                                                        <strong>
                                                            {
                                                                schedule.frequency
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Disease
                                                        </span>
                                                        <strong>
                                                            {
                                                                schedule.disease ||
                                                                "—"
                                                            }
                                                        </strong>
                                                    </div>

                                                </div>

                                                {schedule.status !==
                                                    "taken" && (
                                                    <button
                                                        type="button"
                                                        className="patient-taken-button"
                                                        onClick={() =>
                                                            handleMarkAsTaken(
                                                                schedule.schedule_id
                                                            )
                                                        }
                                                        disabled={
                                                            takingMedicineId ===
                                                            schedule.schedule_id
                                                        }
                                                    >
                                                        {takingMedicineId ===
                                                        schedule.schedule_id
                                                            ? "Saving..."
                                                            : "✓ Mark as Taken"}
                                                    </button>
                                                )}

                                                {schedule.status ===
                                                    "taken" && (
                                                    <div className="patient-taken-message">
                                                        ✓ Medicine
                                                        marked as
                                                        taken
                                                    </div>
                                                )}

                                            </div>
                                        )
                                    )}

                                </div>

                            </div>

                            {/* HISTORY */}
                            <div className="patient-medication-block">

                                <div className="patient-medication-title">
                                    <h3>
                                        📋 Medication History
                                    </h3>

                                    <span>
                                        {history.length}{" "}
                                        records
                                    </span>
                                </div>

                                {historyLoading && (
                                    <Loading />
                                )}

                                {historyError && (
                                    <div className="patient-error">
                                        {historyError}
                                    </div>
                                )}

                                {!historyLoading &&
                                    history.length === 0 && (
                                        <div className="patient-empty">
                                            No medication history
                                            yet.
                                        </div>
                                    )}

                                <div className="patient-history-list">

                                    {history.map(
                                        (record) => (
                                            <div
                                                key={
                                                    record.history_id
                                                }
                                                className="patient-history-card"
                                            >

                                                <div>
                                                    <h3>
                                                        {
                                                            record.medicine_name
                                                        }
                                                    </h3>

                                                    <p>
                                                        {
                                                            record.dosage
                                                        }
                                                    </p>
                                                </div>

                                                <div className="patient-history-info">

                                                    <span>
                                                        Scheduled:{" "}
                                                        {
                                                            record.scheduled_time
                                                        }
                                                    </span>

                                                    <span>
                                                        Taken:{" "}
                                                        {record.taken_at
                                                            ? new Date(
                                                                record.taken_at
                                                            ).toLocaleString()
                                                            : "—"}
                                                    </span>

                                                </div>

                                                <span className="patient-status taken">
                                                    ✓ Taken
                                                </span>

                                            </div>
                                        )
                                    )}

                                </div>

                            </div>

                        </div>
                    )}

                </div>
            </section>
        </div>
    );
}

export default PublicDashboard;