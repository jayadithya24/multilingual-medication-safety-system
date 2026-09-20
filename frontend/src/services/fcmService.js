import { getApp, getApps, initializeApp } from "firebase/app";
import { getMessaging, getToken, isSupported, onMessage, deleteToken } from "firebase/messaging";
import api from "./api";

const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

function hasFirebaseConfig() {
    return [firebaseConfig.apiKey, firebaseConfig.projectId, firebaseConfig.messagingSenderId, firebaseConfig.appId].every(Boolean);
}

export async function listenForMedicationNotifications() {
    if (!hasFirebaseConfig() || !(await isSupported())) return () => {};
    const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
    return onMessage(getMessaging(app), async (payload) => {
        if (Notification.permission !== "granted" || !localStorage.getItem("mmss_token")) return;
        const registration = await navigator.serviceWorker.getRegistration("/");
        await registration?.showNotification(payload.notification?.title || "Medication reminder", {
            body: payload.notification?.body || "Your medication reminder is ready.",
            tag: payload.data?.event_id || payload.messageId,
            data: { url: "/patient-dashboard?tab=medicines" },
        });
    });
}

export async function unregisterMedicationNotifications() {
    const token = localStorage.getItem("mmss_fcm_token");
    if (!token) return;
    // Revoke the browser subscription even if the backend is temporarily unreachable.
    try {
        await api.delete("/patient/fcm-token", { data: { token }, timeout: 5000 });
    } finally {
        if (hasFirebaseConfig() && await isSupported()) {
            const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
            await deleteToken(getMessaging(app));
        }
        localStorage.removeItem("mmss_fcm_token");
    }
}

export async function registerMedicationNotifications() {
    if (!("Notification" in window)) {
        console.warn("[FCM] Notifications are not supported by this browser.");
        return { registered: false, reason: "unsupported" };
    }

    const supported = await isSupported();
    console.info("[FCM] Messaging supported:", supported);
    if (!supported) return { registered: false, reason: "unsupported" };

    const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY;
    console.info("[FCM] Firebase config present:", hasFirebaseConfig());
    console.info("[FCM] VAPID key present:", Boolean(vapidKey));
    if (!vapidKey || !hasFirebaseConfig()) {
        console.error("[FCM] Missing Firebase web config or VAPID key.");
        return { registered: false, reason: "not-configured" };
    }

    const permission = await Notification.requestPermission();
    console.info("[FCM] Notification permission:", permission);
    if (permission !== "granted") {
        return { registered: false, reason: "permission-denied" };
    }

    const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
    const registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js");
    await navigator.serviceWorker.ready;
    console.info("[FCM] Service worker registered:", registration.scope);
    const token = await getToken(getMessaging(app), {
        vapidKey,
        serviceWorkerRegistration: registration,
    });

    console.info("[FCM] Token generated:", Boolean(token));
    if (!token) {
        return { registered: false, reason: "token-unavailable" };
    }

    const response = await api.post("/patient/fcm-token", { token, platform: "browser" });
    localStorage.setItem("mmss_fcm_token", token);
    console.info("[FCM] Token sent to backend:", response.data);
    return { registered: true };
}

export async function sendTestNotification() {
    const response = await api.post("/patient/fcm-test");
    console.info("[FCM] Test notification response:", response.data);
    return response.data;
}
