import api, { clearStoredToken, setStoredRole, setStoredToken } from "./api";

function persistAuth(responseData) {
  if (responseData?.access_token) {
    setStoredToken(responseData.access_token);
  }

  if (responseData?.role) {
    setStoredRole(responseData.role);
  }
}

export async function loginWithPassword(username, password) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const response = await api.post("/auth/token", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

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

export function logout() {
  clearStoredToken();
}