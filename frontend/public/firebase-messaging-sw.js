importScripts("https://www.gstatic.com/firebasejs/12.18.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.18.0/firebase-messaging-compat.js");
importScripts("/firebase-public-config.js");

firebase.initializeApp(self.FIREBASE_CONFIG);
const messaging = firebase.messaging();
console.info("[FCM SW] Firebase messaging service worker initialized");

messaging.onBackgroundMessage((payload) => {
    console.info("[FCM SW] Background message received", payload);
    const notification = payload.notification || {};
    self.registration.showNotification(
        notification.title || "Medication reminder",
        {
            body: notification.body || "It is time to take your medicine.",
            icon: "/pwa-192x192.png",
            data: payload.data || {},
        },
    );
});