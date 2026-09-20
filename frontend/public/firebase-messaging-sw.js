self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    event.stopImmediatePropagation();
    const url = new URL("/patient-dashboard?tab=medicines", self.location.origin).href;
    event.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(async (clients) => {
        const existing = clients.find((client) => new URL(client.url).origin === self.location.origin);
        if (existing) { await existing.navigate(url); return existing.focus(); }
        return self.clients.openWindow(url);
    }));
});

importScripts("https://www.gstatic.com/firebasejs/12.18.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.18.0/firebase-messaging-compat.js");
importScripts("/firebase-public-config.js");

firebase.initializeApp(self.FIREBASE_CONFIG);
const messaging = firebase.messaging();
console.info("[FCM SW] Firebase messaging service worker initialized");

messaging.onBackgroundMessage((payload) => {
    // FCM displays notification payloads automatically in the background.
    if (payload.notification) return;
    const notification = payload.notification || {};
    self.registration.showNotification(
        notification.title || "Medication reminder",
        {
            body: notification.body || "It is time to take your medicine.",
            tag: payload.data?.event_id || payload.messageId,
            data: payload.data || {},
        },
    );
});
