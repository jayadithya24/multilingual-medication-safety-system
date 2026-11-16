import api, { clearStoredToken, setStoredRole, setStoredSession } from "./api";
import { unregisterMedicationNotifications } from "./fcmService";

function persistAuth(responseData) {
  setStoredSession();

  if (responseData?.role) {
    setStoredRole(responseData.role);
  }
}

export async function loginWithPassword(username, password, patientOnly = false, expectedRole = null) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const response = await api.post("/auth/session", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  expectedRole = patientOnly ? "patient" : expectedRole;
  if (expectedRole && response.data?.role !== expectedRole) {
    await api.post("/auth/logout");
    clearStoredToken();
    throw new Error(`Please sign in with a registered ${expectedRole} account.`);
  }
  persistAuth(response.data);
  return response.data;
}

export async function registerPatient(name, email, password, confirmPassword) {
  const response = await api.post("/auth/register-session", {
    name,
    email,
    password,
    confirm_password: confirmPassword,
  });

  return response.data;
}

export async function requestDoctorAccount(request) {
  const response = await api.post("/auth/doctor-request", {
    name: request.name,
    email: request.email,
    phone: request.phone,
    doctor_id: request.medicalRegistrationNo,
    specialization: request.specialization,
    hospital: request.hospital,
    password: request.password,
    confirm_password: request.confirmPassword,
  });

  return response.data;
}

export async function logout() {
  try { await unregisterMedicationNotifications(); }
  catch { console.warn("Could not fully unregister notifications on this device."); }
  await api.post("/auth/logout");
  window.google?.accounts?.id?.disableAutoSelect();
  clearStoredToken();
}

export async function loginWithGoogle(credential, mode = "login", password) {
  const response = await api.post("/auth/google-session", { credential, mode, password });
  persistAuth(response.data);
  return response.data;
}
