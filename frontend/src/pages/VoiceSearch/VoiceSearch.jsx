import { useEffect, useRef, useState } from "react";
import MedicineCard from "../../components/MedicineCard/MedicineCard";
import { sendVoiceSearchAudio } from "../../services/voiceService";
import { scanMedicine } from "../../services/ocrService";
import "./VoiceSearch.css";

function VoiceSearch() {
  const [lang, setLang] = useState("auto");
  const [isRecording, setIsRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [audioPreview, setAudioPreview] = useState("");
  const [medicineImage, setMedicineImage] = useState(null);
  const [medicinePreview, setMedicinePreview] = useState("");
  const [ocrMedicine, setOcrMedicine] = useState("");

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const chunksRef = useRef([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (audioPreview) {
        URL.revokeObjectURL(audioPreview);
      }

      if (medicinePreview) {
        URL.revokeObjectURL(medicinePreview);
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [audioPreview]);

  const resetResultState = () => {
    setResult(null);
    setError("");
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
    resetResultState();
  };

  const handleMedicineImageChange = (event) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    if (medicinePreview) {
      URL.revokeObjectURL(medicinePreview);
    }

    setMedicineImage(selectedFile);
    setMedicinePreview(URL.createObjectURL(selectedFile));
    setOcrMedicine("");
    resetResultState();
  };

  const startRecording = async () => {
    try {
      resetResultState();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const preferredMimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(
        (mimeType) => window.MediaRecorder && MediaRecorder.isTypeSupported(mimeType)
      );

      const mediaRecorder = preferredMimeType
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);

      console.debug("Recording started", {
        mimeType: mediaRecorder.mimeType || "browser default",
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          console.debug("Audio chunk received", event.data.size);
        }
      };

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder.mimeType || preferredMimeType || "audio/webm";
        const recordingBlob = new Blob(chunksRef.current, {
          type: mimeType,
        });

        console.debug("Recording stopped", {
          chunks: chunksRef.current.length,
          blobSize: recordingBlob.size,
          blobType: recordingBlob.type,
        });

        if (recordingBlob.size === 0) {
          setAudioFile(null);
          setError("No audio was recorded. Please try again.");
          mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
          mediaStreamRef.current = null;
          return;
        }

        const extension = mimeType.includes("mp4") ? "mp4" : "webm";
        const recordingFile = new File([recordingBlob], `voice-search.${extension}`, {
          type: recordingBlob.type,
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

      mediaRecorder.start(250);
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (recordingError) {
      console.error(recordingError);
      setError(
        recordingError?.name === "NotAllowedError"
          ? "Microphone permission is required."
          : "Unable to access the microphone."
      );
    }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") {
      return;
    }

    console.debug("Stopping recording");
    mediaRecorderRef.current.requestData?.();
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  const handleVoiceSearch = async () => {
    if (!audioFile) {
      setError("Please record or upload an audio file first.");
      return;
    }

    try {
      setProcessing(true);
      setError("");
      setResult(null);

      let identifiedMedicine = ocrMedicine;
      if (medicineImage && !identifiedMedicine) {
        const ocrResponse = await scanMedicine(medicineImage, lang);
        identifiedMedicine = ocrResponse?.ocr_result?.detected_medicine || "";
        setOcrMedicine(identifiedMedicine);
        if (!identifiedMedicine) {
          throw new Error(
            "This medicine is not available in the system. Please consult a doctor."
          );
        }
      }

      const response = await sendVoiceSearchAudio(audioFile, lang, identifiedMedicine);
      setResult(response);

      if (response.response_text && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const spokenResponse = new SpeechSynthesisUtterance(response.response_text);
        spokenResponse.lang = response.response_language === "tulu"
          ? "tcy-IN"
          : response.response_language === "kn"
            ? "kn-IN"
            : "en-IN";
        window.speechSynthesis.speak(spokenResponse);
      }
    } catch (searchError) {
      console.error(searchError);
      setError(
        searchError?.response?.data?.detail ||
        searchError?.message ||
        "Unable to process the voice search request."
      );
    } finally {
      setProcessing(false);
    }
  };

  const medicineDetails = result?.medicine_details ?? null;
  const matchingMedicines = result?.matching_medicines ?? [];
  const detectedText = result?.detected_text ?? "";
  const detectedMedicine = result?.detected_medicine ?? medicineDetails?.drug_name ?? "";
  const isNotFound = result?.status === "not_found" || result?.clarification_required;

  return (
    <div className="voice-search-page">
      <section className="voice-shell">
        <div className="voice-hero">
          <p className="voice-kicker">Voice Search</p>
          <h1>Speak or upload an audio clip to find a medicine</h1>
          <p>
            Record the name of a medicine, or upload an audio file and let the backend recognize it.
          </p>
        </div>

        <label className="voice-language-selector">
          <span>Language</span>
          <select value={lang} onChange={(event) => setLang(event.target.value)}>
            <option value="auto">Automatic</option>
            <option value="en">English</option>
            <option value="kn">Kannada</option>
            <option value="tulu">Tulu</option>
          </select>
        </label>

        <div className="voice-panel">
          <div className="voice-controls">
            <button
              className={`voice-button voice-button--primary ${isRecording ? "is-recording" : ""}`}
              onClick={startRecording}
              disabled={processing || isRecording}
            >
              {isRecording ? "Recording..." : "Record"}
            </button>

            <button
              className="voice-button voice-button--secondary"
              onClick={stopRecording}
              disabled={!isRecording}
            >
              Stop
            </button>

            <button
              className="voice-button voice-button--ghost"
              onClick={() => fileInputRef.current?.click()}
              disabled={processing}
            >
              Upload Audio
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleAudioFileChange}
              className="voice-hidden-input"
            />
          </div>

          <label className="voice-medicine-image">
            <span>Show or upload medicine image</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleMedicineImageChange}
            />
          </label>

          {medicinePreview && (
            <div className="voice-medicine-preview">
              <img src={medicinePreview} alt="Medicine" />
              {ocrMedicine && <p>Medicine identified: {ocrMedicine}</p>}
            </div>
          )}

          {audioPreview && (
            <div className="voice-audio-preview">
              <audio controls src={audioPreview} />
            </div>
          )}

          <button
            className="voice-submit"
            onClick={handleVoiceSearch}
            disabled={processing || isRecording}
          >
            {processing ? "Processing..." : "Search Medicine"}
          </button>

          {(processing || isRecording) && (
            <div className="voice-processing" aria-live="polite">
              <div className="voice-spinner" />
              <p>{isRecording ? "Listening for medicine name..." : "Transcribing audio..."}</p>
            </div>
          )}

          {error && <div className="voice-error">{error}</div>}

          {result && (
            <div className="voice-result">
              <div className="voice-summary">
                <p className="voice-summary__label">Recognized Text</p>
                <h2>{detectedText || "N/A"}</h2>
                {result.response_text && (
                  <p className="voice-summary__response">
                    {result.response_text}
                  </p>
                )}
                {matchingMedicines.length > 0 && (
                  <ul className="voice-matching-medicines">
                    {matchingMedicines.map((medicine) => (
                      <li key={medicine.drug_name}>{medicine.drug_name}</li>
                    ))}
                  </ul>
                )}
                <p className="voice-summary__medicine">
                  {isNotFound
                    ? "Medicine not found."
                    : `Detected Medicine: ${detectedMedicine || "N/A"}`}
                </p>
              </div>

              {medicineDetails ? (
                <MedicineCard medicine={medicineDetails} />
              ) : (
                <MedicineCard medicine={null} />
              )}

              {isNotFound && (
                <p className="voice-result__message">{result.message}</p>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default VoiceSearch;