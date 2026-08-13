import { useEffect, useRef, useState } from "react";
import Loading from "../../components/Loading/Loading";
import MedicineCard from "../../components/MedicineCard/MedicineCard";
import { searchMedicine } from "../../services/medicineService";
import { scanMedicine } from "../../services/ocrService";
import { sendVoiceSearchAudio } from "../../services/voiceService";
import { fetchMedicines } from "../../services/medicineService";
import "./PublicDashboard.css";

const languageOptions = [
    { value: "en", label: "English" },
    { value: "kn", label: "Kannada" },
    { value: "tulu", label: "Tulu" },
];

function PublicDashboard() {
    const [activeTab, setActiveTab] = useState("text");
    const [lang, setLang] = useState("en");
    const [medicineNames, setMedicineNames] = useState([]);

    const [query, setQuery] = useState("");
    const [textLoading, setTextLoading] = useState(false);
    const [textError, setTextError] = useState("");
    const [textResult, setTextResult] = useState(null);

    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState("");
    const [ocrLoading, setOcrLoading] = useState(false);
    const [ocrError, setOcrError] = useState("");
    const [ocrResult, setOcrResult] = useState(null);

    const [audioFile, setAudioFile] = useState(null);
    const [audioPreview, setAudioPreview] = useState("");
    const [voiceLoading, setVoiceLoading] = useState(false);
    const [voiceError, setVoiceError] = useState("");
    const [voiceResult, setVoiceResult] = useState(null);
    const [isRecording, setIsRecording] = useState(false);

    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const fileInputRef = useRef(null);

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

    useEffect(() => {
        return () => {
            if (imagePreview) {
                URL.revokeObjectURL(imagePreview);
            }

            if (audioPreview) {
                URL.revokeObjectURL(audioPreview);
            }

            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            }
        };
    }, [imagePreview, audioPreview]);

    const resetTextState = () => {
        setTextError("");
        setTextResult(null);
    };

    const resetOcrState = () => {
        setOcrError("");
        setOcrResult(null);
    };

    const resetVoiceState = () => {
        setVoiceError("");
        setVoiceResult(null);
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
            setTextError("Unable to search for that medicine right now.");
        } finally {
            setTextLoading(false);
        }
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
            setOcrError(error.message || "Unable to scan the medicine image.");
        } finally {
            setOcrLoading(false);
        }
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

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            const preferredMimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(
                (mimeType) => window.MediaRecorder && MediaRecorder.isTypeSupported(mimeType)
            );

            const mediaRecorder = preferredMimeType
                ? new MediaRecorder(stream, { mimeType: preferredMimeType })
                : new MediaRecorder(stream);

            chunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const recordingBlob = new Blob(chunksRef.current, {
                    type: mediaRecorder.mimeType || "audio/webm",
                });

                const recordingFile = new File([recordingBlob], "voice-search.webm", {
                    type: recordingBlob.type || "audio/webm",
                });

                if (audioPreview) {
                    URL.revokeObjectURL(audioPreview);
                }

                setAudioFile(recordingFile);
                setAudioPreview(URL.createObjectURL(recordingBlob));
                mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
                mediaStreamRef.current = null;
                chunksRef.current = [];
            };

            mediaRecorder.start();
            mediaRecorderRef.current = mediaRecorder;
            setIsRecording(true);
        } catch (error) {
            console.error(error);
            setVoiceError("Unable to access the microphone.");
        }
    };

    const stopRecording = () => {
        if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") {
            return;
        }

        mediaRecorderRef.current.stop();
        setIsRecording(false);
    };

    const handleVoiceSearch = async () => {
        if (!audioFile) {
            setVoiceError("Please record or upload an audio file first.");
            return;
        }

        try {
            setVoiceLoading(true);
            resetVoiceState();

            const response = await sendVoiceSearchAudio(audioFile, lang);
            setVoiceResult(response);
        } catch (error) {
            console.error(error);
            setVoiceError("Unable to process the voice search request.");
        } finally {
            setVoiceLoading(false);
        }
    };

    const textMedicine = textResult?.medicine ?? null;
    const ocrMedicine = ocrResult?.ocr_result?.medicine_details ?? null;
    const voiceMedicine = voiceResult?.medicine_details ?? null;

    return (
        <div className="patient-portal">
            <section className="patient-shell">
                <div className="patient-hero">
                    <p className="patient-kicker">Patient Portal</p>
                    <h1>Find medicines in text, by image, or by voice</h1>
                    <p>
                        One workspace for multilingual medicine lookup in English, Kannada, and Tulu.
                    </p>
                </div>

                <div className="patient-toolbar">
                    <div className="patient-tabs" role="tablist" aria-label="Patient portal tabs">
                        <button
                            type="button"
                            className={`patient-tab ${activeTab === "text" ? "is-active" : ""}`}
                            onClick={() => setActiveTab("text")}
                        >
                            Text Search
                        </button>
                        <button
                            type="button"
                            className={`patient-tab ${activeTab === "ocr" ? "is-active" : ""}`}
                            onClick={() => setActiveTab("ocr")}
                        >
                            OCR Scan
                        </button>
                        <button
                            type="button"
                            className={`patient-tab ${activeTab === "voice" ? "is-active" : ""}`}
                            onClick={() => setActiveTab("voice")}
                        >
                            Voice Search
                        </button>
                    </div>

                    <label className="patient-language">
                        <span>Language</span>
                        <select value={lang} onChange={(event) => setLang(event.target.value)}>
                            {languageOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </label>
                </div>

                <div className="patient-panel">
                    {activeTab === "text" && (
                        <div className="patient-section">
                            <div className="patient-section__header">
                                <h2>Text Search</h2>
                                <p>Search by drug name, generic name, or active ingredient.</p>
                            </div>

                            <datalist id="patient-medicine-options">
                                {medicineNames.map((medicine) => (
                                    <option key={medicine} value={medicine} />
                                ))}
                            </datalist>

                            <div className="patient-search-row">
                                <input
                                    type="text"
                                    list="patient-medicine-options"
                                    value={query}
                                    onChange={(event) => setQuery(event.target.value)}
                                    placeholder="Type a medicine name"
                                />
                                <button type="button" onClick={handleSearch} disabled={textLoading}>
                                    {textLoading ? "Searching..." : "Search"}
                                </button>
                            </div>

                            {textLoading && <Loading />}
                            {textError && <div className="patient-error">{textError}</div>}

                            {textResult && (
                                <div className="patient-result">
                                    {textMedicine ? (
                                        <MedicineCard medicine={textMedicine} />
                                    ) : (
                                        <div className="patient-empty">Medicine not found.</div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "ocr" && (
                        <div className="patient-section">
                            <div className="patient-section__header">
                                <h2>OCR Scan</h2>
                                <p>Upload a strip or prescription image and read the medicine details.</p>
                            </div>

                            <input type="file" accept="image/*" onChange={handleImageChange} />

                            {imagePreview && (
                                <div className="patient-preview">
                                    <img src={imagePreview} alt="Medicine preview" />
                                </div>
                            )}

                            <button type="button" onClick={handleOcrScan} disabled={ocrLoading}>
                                {ocrLoading ? "Scanning..." : "Scan medicine"}
                            </button>

                            {ocrLoading && <Loading />}
                            {ocrError && <div className="patient-error">{ocrError}</div>}

                            {ocrResult && (
                                <div className="patient-result">
                                    {ocrMedicine ? (
                                        <MedicineCard medicine={ocrMedicine} />
                                    ) : (
                                        <div className="patient-empty">No medicine detected.</div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "voice" && (
                        <div className="patient-section">
                            <div className="patient-section__header">
                                <h2>Voice Search</h2>
                                <p>Record a medicine name or upload an audio clip.</p>
                            </div>

                            <div className="patient-voice-controls">
                                <button type="button" onClick={startRecording} disabled={voiceLoading || isRecording}>
                                    {isRecording ? "Recording..." : "Record"}
                                </button>
                                <button type="button" onClick={stopRecording} disabled={!isRecording}>
                                    Stop
                                </button>
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={voiceLoading}
                                >
                                    Upload Audio
                                </button>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="audio/*"
                                    onChange={handleAudioFileChange}
                                    className="patient-hidden-input"
                                />
                            </div>

                            {audioPreview && (
                                <div className="patient-audio-preview">
                                    <audio controls src={audioPreview} />
                                </div>
                            )}

                            <button type="button" onClick={handleVoiceSearch} disabled={voiceLoading || isRecording}>
                                {voiceLoading ? "Processing..." : "Search medicine"}
                            </button>

                            {(voiceLoading || isRecording) && <Loading />}
                            {voiceError && <div className="patient-error">{voiceError}</div>}

                            {voiceResult && (
                                <div className="patient-result">
                                    {voiceMedicine ? (
                                        <MedicineCard medicine={voiceMedicine} />
                                    ) : (
                                        <div className="patient-empty">Medicine not found.</div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default PublicDashboard;