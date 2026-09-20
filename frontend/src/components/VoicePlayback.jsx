import { useEffect, useRef, useState } from "react";
import api from "../services/api";

const audioCache = new Map();

export default function VoicePlayback({ text, language, controls = true }) {
  const audioRef = useRef(null);
  const [resource, setResource] = useState(null);
  const [playbackMessage, setPlaybackMessage] = useState("");
  const key = JSON.stringify([language, text]);
  const current = resource?.key === key ? resource : null;

  useEffect(() => {
    if (!text) return;
    let disposed = false;
    let objectUrl;
    const controller = new AbortController();
    // Every page uses the same explicitly female server voices. Never let the
    // browser silently choose its default (possibly male) system voice.
    const load = async () => {
      try {
        let audioBlob = audioCache.get(key);
        if (!audioBlob) {
          const response = await api.get("/tts", {
            params: { text, lang: language }, responseType: "blob",
            signal: controller.signal, timeout: 30000,
          });
          audioBlob = response.data;
          if (!audioBlob.type.startsWith("audio/")) throw new Error("No audio returned");
          if (audioCache.size >= 16) audioCache.delete(audioCache.keys().next().value);
          audioCache.set(key, audioBlob);
        }
        if (disposed) return;
        objectUrl = URL.createObjectURL(audioBlob);
        setPlaybackMessage("");
        setResource({ key, url: objectUrl });
      } catch {
        if (!disposed) setResource({ key, message: "The female voice is unavailable. Please try again; the text result is still available." });
      }
    };
    void load();
    return () => {
      disposed = true;
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [text, language, key]);

  useEffect(() => {
    if (!current?.url || !audioRef.current) return;
    let active = true;
    const audio = audioRef.current;
    audio.playbackRate = 1;
    audio.preservesPitch = true;
    audio.play().catch(() => {
      if (active) setPlaybackMessage(controls ? "Press Play below to hear the response." : "Your browser blocked automatic audio. Allow sound for this site and search again.");
    });
    return () => { active = false; audio.pause(); };
  }, [current?.url, controls]);

  if (!text) return null;
  const message = current ? current.message || playbackMessage : "Preparing spoken response...";
  return (
    <div className="voice-response-audio">
      {message && <p role="status">{message}</p>}
      {current?.url && <audio ref={audioRef} controls={controls} hidden={!controls} src={current.url} aria-label="Spoken medicine response"
        onPlaying={() => setPlaybackMessage("")}
        onError={() => setPlaybackMessage("Audio could not play. Please try searching again.")} />}
    </div>
  );
}
