import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import { loginWithGoogle } from "../../services/authService";

let googleScript;
function loadGoogle() {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (!googleScript) {
    googleScript = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.onload = resolve;
      script.onerror = () => { script.remove(); googleScript = null; reject(new Error("Google could not load. Use email and password or reload to retry.")); };
      document.head.appendChild(script);
    });
  }
  return googleScript;
}

export default function GoogleSignIn({ mode = "login" }) {
  const container = useRef(null);
  const navigate = useNavigate();
  const [message, setMessage] = useState("Checking Google sign-in availability…");
  const [linkCredential, setLinkCredential] = useState("");
  const [password, setPassword] = useState("");
  const [linking, setLinking] = useState(false);
  useEffect(() => {
    let active = true;
    let pending = false;
    api.get("/auth/providers").then(async ({ data }) => {
      if (!active) return;
      if (!data.google_client_id) {
        setMessage("Google sign-in is not available yet. You can use email and password below.");
        return;
      }
      await loadGoogle();
      if (!active) return;
      window.google.accounts.id.initialize({
        client_id: data.google_client_id,
        auto_select: false,
        callback: async ({ credential }) => {
          if (!active || pending) return;
          pending = true;
          setMessage("Signing in with Google…");
          try {
            await loginWithGoogle(credential, mode);
            if (active) navigate("/patient-profile", { replace: true });
          } catch (error) {
            if (active) {
              const detail = error.response?.data?.detail;
              if (detail?.code === "google_link_required") setLinkCredential(credential);
              setMessage(typeof detail === "string" ? detail : detail?.message || "Google sign-in failed. Please retry.");
            }
          } finally { pending = false; }
        },
      });
      window.google.accounts.id.renderButton(container.current, {
        theme: "outline", size: "large", text: mode === "register" ? "signup_with" : "signin_with", shape: "pill",
      });
      setMessage("");
    }).catch(() => { if (active) setMessage("Google sign-in is unavailable. Use email and password or reload to retry."); });
    return () => { active = false; };
  }, [navigate, mode]);
  const linkAccount = async (event) => {
    event.preventDefault();
    if (linking) return;
    setLinking(true);
    try {
      await loginWithGoogle(linkCredential, mode, password);
      setPassword("");
      setLinkCredential("");
      navigate("/patient-profile", { replace: true });
    } catch (error) {
      const detail = error.response?.data?.detail;
      setMessage(typeof detail === "string" ? detail : detail?.message || "Unable to link Google. Please try again.");
    } finally { setLinking(false); }
  };
  return <div className="portal-google"><div ref={container} />{message && <p role="status">{message}</p>}
    {linkCredential && <form className="portal-auth-form" onSubmit={linkAccount}>
      <label>Existing account password<input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
      <button disabled={linking} type="submit">{linking ? "Linking…" : "Link Google and sign in"}</button>
      <button type="button" disabled={linking} onClick={() => { setLinkCredential(""); setPassword(""); setMessage(""); }}>Cancel</button>
    </form>}
    <p className="portal-auth-divider">or continue with email</p></div>;
}
