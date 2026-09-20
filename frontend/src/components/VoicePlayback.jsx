import { useEffect, useRef, useState } from "react";
import api from "../services/api";

const audioCache = new Map();

export default function VoicePlayback({ text, language, controls = true }) {
  const audioRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!text) return;
    // User-supplied Tulu pronunciation; preserve compound numbers and decimals.
    const speechText = language === "tulu"
      ? text.replace(/(?<![\p{L}\p{N}_.,])2(?![\p{L}\p{N}_]|[.,]\d)/gu, "ರಡ್ಡ್")
      : text;
    let disposed = false;
    let objectUrl;
    let fallbackStarted = false;
    let startTimer;
    const controller = new AbortController();
    const synthesis = window.speechSynthesis;
    const fallback = async () => {
      if (disposed || fallbackStarted) return;
      fallbackStarted = true;
      clearTimeout(startTimer);
      synthesis?.cancel();
      setMessage("Preparing spoken response...");
      try {
        const cacheKey = JSON.stringify([language, speechText]);
        let audioBlob = audioCache.get(cacheKey);
        if (!audioBlob) {
          const response = await api.get("/tts", {
            params: { text: speechText, lang: language }, responseType: "blob",
            signal: controller.signal, timeout: 60000,
          });
          audioBlob = response.data;
          if (!audioBlob.type.startsWith("audio/")) throw new Error("No audio returned");
          if (audioCache.size >= 16) audioCache.delete(audioCache.keys().next().value);
          audioCache.set(cacheKey, audioBlob);
        }
        if (disposed) return;
        objectUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(objectUrl);
        setMessage("");
      } catch {
        if (!disposed) setMessage("Speech is unavailable. Please try searching again; the text result is still available.");
      }
    };
    // Kannada/Tulu use server audio because installed browser voices vary.
    if (language !== "en" || !synthesis) {
      void fallback();
    } else {
      synthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-IN";
      const englishVoices = synthesis.getVoices().filter(voice => /^en[-_]/i.test(voice.lang));
      const preferred = englishVoices.find(voice => /female|zira|hazel|susan|samantha|heera|aria|jenny|sonia|libby|neerja/i.test(voice.name));
      if (preferred) {
        utterance.voice = preferred;
        utterance.lang = preferred.lang;
      }
      utterance.rate = 1;
      utterance.onstart = () => clearTimeout(startTimer);
      utterance.onerror = () => { void fallback(); };
      startTimer = setTimeout(() => { void fallback(); }, 4000);
      synthesis.speak(utterance);
    }
    return () => {
      disposed = true;
      clearTimeout(startTimer);
      controller.abort();
      synthesis?.cancel();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [text, language]);

  useEffect(() => {
    if (!audioUrl || !audioRef.current) return;
    let active = true;
    const audio = audioRef.current;
    audio.playbackRate = language === "en" ? 1 : 1.2;
    audio.preservesPitch = true;
    audio.play().catch(() => {
      if (active) setMessage(controls ? "Press Play below to hear the response." : "Your browser blocked automatic audio. Allow sound for this site and search again.");
    });
    return () => { active = false; audio.pause(); };
  }, [audioUrl, language, controls]);

  return (
    <div className="voice-response-audio">
      {message && <p role="status">{message}</p>}
      {audioUrl && <audio ref={audioRef} controls={controls} hidden={!controls} src={audioUrl} aria-label="Spoken medicine response"
        onPlaying={() => setMessage("")}
        onError={() => setMessage("Audio could not play. Please try searching again.")} />}
    </div>
  );
}
