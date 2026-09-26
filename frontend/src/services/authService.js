import api, { clearStoredToken, setStoredRole, setStoredToken } from "./api";
import { unregisterMedicationNotifications } from "./fcmService";

function persistAuth(responseData) {
  const accessToken = responseData?.access_token || responseData?.token;

  if (accessToken) {
    setStoredToken(accessToken);
  }

  if (responseData?.role) {
    setStoredRole(responseData.role);
  }
}

export async function loginWithPassword(username, password, patientOnly = false, expectedRole = null) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const response = await api.post(patientOnly ? "/auth/patient-token" : "/auth/token", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  if (expectedRole && response.data?.role !== expectedRole) {
    throw new Error(`Please sign in with a registered ${expectedRole} account.`);
  }
  persistAuth(response.data);
  return response.data;
}

export async function registerPatient(name, email, password, confirmPassword) {
  const response = await api.post("/auth/register", {
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
  window.google?.accounts?.id?.disableAutoSelect();
  clearStoredToken();
}

export async function loginWithGoogle(credential, mode = "login", password) {
  const response = await api.post("/auth/google", { credential, mode, password });
  persistAuth(response.data);
  return response.data;
}
