import { useEffect, useRef, useState } from "react";
import VoicePlayback from "../../components/VoicePlayback";
import { sendVoiceSearchAudio } from "../../services/voiceService";
import { scanMedicine } from "../../services/ocrService";
import "./VoiceSearch.css";

const LANGUAGE_COPY = {
  en: {
    name: "English",
    medicine: "Medicine",
    usedFor: "Used for",
    simpleDescription: "What it does",
    warning: "Important warning",
    consult: "Ask a doctor or pharmacist before changing how you take it.",
  },
  kn: {
    name: "ಕನ್ನಡ",
    medicine: "ಔಷಧಿ",
    usedFor: "ಬಳಕೆ",
    simpleDescription: "ಇದು ಏನು ಮಾಡುತ್ತದೆ",
    warning: "ಮುಖ್ಯ ಎಚ್ಚರಿಕೆ",
    consult: "ಔಷಧಿಯನ್ನು ಬದಲಾಯಿಸುವ ಮೊದಲು ವೈದ್ಯರನ್ನು ಅಥವಾ ಔಷಧಿಕಾರರನ್ನು ಕೇಳಿ.",
  },
  tulu: {
    name: "ತುಳು",
    medicine: "ಮರ್ದ್",
    usedFor: "ಬಳಕೆ",
    simpleDescription: "ಉಂದು ದಾದ ಮಲ್ಪುಂಡ್",
    warning: "ಮುಖ್ಯ ಜಾಗ್ರತೆ",
    consult: "ಮರ್ದ್ ಬದಲ್ ಮಲ್ಪುನೆಡ್ದ್ ದುಂಬು ಡಾಕ್ಟ್ರೆಡ ಅತ್ತ್ಂಡ ಫಾರ್ಮಸಿಸ್ಟ್‌ಡ ಕೇನ್ಲೆ",
  },
};

function firstSentence(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  const sentence = text.match(/^.*?[.!?।॥]/)?.[0];
  return sentence || text;
}

function getSimpleInfo(medicine, language) {
  if (!medicine) return null;

  const copy = LANGUAGE_COPY[language] || LANGUAGE_COPY.en;
  return {
    copy,
    name: medicine.drug_name,
    disease: medicine.disease,
    description: firstSentence(medicine.description),
    warning: firstSentence(medicine.warnings),
  };
}

function VoiceSearch({ embedded = false }) {
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
  const recordingTimerRef = useRef(null);
  const silenceCleanupRef = useRef(() => {});

  useEffect(() => {
    return () => {
      clearTimeout(recordingTimerRef.current);
      silenceCleanupRef.current();
      const recorder = mediaRecorderRef.current;
      if (recorder) {
        recorder.onstop = null;
        recorder.ondataavailable = null;
        if (recorder.state !== "inactive") recorder.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    return () => { if (audioPreview) URL.revokeObjectURL(audioPreview); };
  }, [audioPreview]);

  useEffect(() => {
    return () => { if (medicinePreview) URL.revokeObjectURL(medicinePreview); };
  }, [medicinePreview]);

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
        clearTimeout(recordingTimerRef.current);
        silenceCleanupRef.current();
        setIsRecording(false);
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
        void handleVoiceSearch(recordingFile);
      };

      mediaRecorder.start(250);
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      // Wait for sustained sound before interpreting a quiet pause as finished.
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        try {
          const context = new AudioContextClass();
          const source = context.createMediaStreamSource(stream);
          const analyser = context.createAnalyser();
          analyser.fftSize = 2048;
          source.connect(analyser);
          const samples = new Float32Array(analyser.fftSize);
          let speechFrames = 0;
          let lastSound = 0;
          const timer = setInterval(() => {
            analyser.getFloatTimeDomainData(samples);
            const rms = Math.sqrt(samples.reduce((sum, value) => sum + value * value, 0) / samples.length);
            if (rms > 0.02) {
              speechFrames += 1;
              lastSound = performance.now();
            } else if (speechFrames >= 4 && performance.now() - lastSound >= 2500 && mediaRecorder.state === "recording") {
              mediaRecorder.stop();
            }
          }, 100);
          silenceCleanupRef.current = () => {
            clearInterval(timer);
            source.disconnect();
            if (context.state !== "closed") void context.close();
          };
          void context.resume().catch(() => {});
        } catch (audioError) {
          console.warn("Silence detection unavailable; use Stop.", audioError);
        }
      }
      recordingTimerRef.current = setTimeout(() => {
        if (mediaRecorder.state === "recording") mediaRecorder.stop();
      }, 30000);
    } catch (recordingError) {
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
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
    clearTimeout(recordingTimerRef.current);
    mediaRecorderRef.current.requestData?.();
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  const handleVoiceSearch = async (selectedAudio = audioFile) => {
    if (!selectedAudio) {
      setError("Please record or upload an audio file first.");
      return;
    }

    try {
      setProcessing(true);
      setError("");
      setResult(null);

      let identifiedMedicine = ocrMedicine;
      if (medicineImage && !identifiedMedicine) {
        const ocrResponse = await scanMedicine(medicineImage, lang === "auto" ? "en" : lang);
        identifiedMedicine = ocrResponse?.ocr_result?.detected_medicine || "";
        setOcrMedicine(identifiedMedicine);
        if (!identifiedMedicine) {
          throw new Error(
            "This medicine is not available in the system. Please consult a doctor."
          );
        }
      }

      const response = await sendVoiceSearchAudio(selectedAudio, lang, identifiedMedicine);
      setResult(response);

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
  const isNotFound = result?.status === "not_found";
  const simpleInfo = getSimpleInfo(
    medicineDetails,
    result?.response_language || (lang === "auto" ? "en" : lang)
  );
  const spokenResponse = simpleInfo
    ? `${simpleInfo.copy.medicine}: ${simpleInfo.name}. ${simpleInfo.copy.usedFor}: ${simpleInfo.disease}. ${simpleInfo.copy.warning}: ${simpleInfo.warning}. ${simpleInfo.copy.consult}`
    : result?.response_text;

  return (
    <div className={`voice-search-page${embedded ? " voice-search-page--embedded" : ""}`}>
      <section className="voice-shell">
        <div className="voice-hero">
          {!embedded && <p className="voice-kicker">Voice Search</p>}
          {embedded
            ? <h2>Speak or upload an audio clip to find a medicine</h2>
            : <h1>Speak or upload an audio clip to find a medicine</h1>}
          <p>
            Record your medicine name or question. After you speak, pause for about 3 seconds to search automatically. Maximum recording: 30 seconds. You can also press Stop.
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

        {lang === "auto" && (
          <p>Speak a short sentence with the medicine name so we can identify your language. A medicine name alone may not be enough.</p>
        )}

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
              disabled={processing || isRecording}
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
            onClick={() => handleVoiceSearch()}
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
              {result.status === "language_uncertain" && <p role="status">{result.message}</p>}
              <VoicePlayback text={spokenResponse} language={result.response_language || (lang === "auto" ? "en" : lang)} />
              <div className="voice-summary">
                <p className="voice-summary__label">Recognized Text</p>
                <h2>{detectedText || "N/A"}</h2>
                {result.response_text && !medicineDetails && (
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
                  {result.status === "language_uncertain"
                    ? "Please confirm your language above."
                    : isNotFound
                    ? "Medicine not found."
                    : `Detected Medicine: ${detectedMedicine || "N/A"}`}
                </p>
              </div>

              {simpleInfo ? (
                <article className="voice-simple-info" aria-label={`${simpleInfo.copy.name} medicine information`}>
                  <p className="voice-simple-info__language">{simpleInfo.copy.name}</p>
                  <h2>{simpleInfo.name}</h2>
                  <dl>
                    <div>
                      <dt>{simpleInfo.copy.usedFor}</dt>
                      <dd>{simpleInfo.disease}</dd>
                    </div>
                    <div>
                      <dt>{simpleInfo.copy.simpleDescription}</dt>
                      <dd>{simpleInfo.description || "N/A"}</dd>
                    </div>
                    <div>
                      <dt>{simpleInfo.copy.warning}</dt>
                      <dd>{simpleInfo.warning || "N/A"}</dd>
                    </div>
                  </dl>
                  <p className="voice-simple-info__consult">{simpleInfo.copy.consult}</p>
                </article>
              ) : null}

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
