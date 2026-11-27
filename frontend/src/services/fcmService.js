export async function listenForMedicationNotifications() {
  return () => {};
}

export async function unregisterMedicationNotifications() {
  localStorage.removeItem("mmss_fcm_token");
}

export async function registerMedicationNotifications() {
  return { registered: false, reason: "unavailable-in-static-demo" };
}

export async function sendTestNotification() {
  throw new Error("Notifications are not available in the static demo.");
}
