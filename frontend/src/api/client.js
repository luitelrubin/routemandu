import axios from "axios";
import createAuthRefreshInterceptor from "axios-auth-refresh";
const isDevelopment = import.meta.env.mode === "development";
export const API_URL = isDevelopment ? import.meta.env.VITE_DEV_URL : import.meta.env.VITE_PROD_URL;

const client = axios.create({
  baseURL: API_URL,
});

// Attach the current access token (if any) to every request.
client.interceptors.request.use((config) => {
  const access = localStorage.getItem("access");
  if (access) {
    config.headers.Authorization = `JWT ${access}`;
  }
  return config;
});

// On a 401, try to use the refresh token once to get a new access token
// and replay the original request. If that fails too (refresh expired/
// invalid), clear tokens and send the user to /login.
const refreshAuthLogic = async (failedRequest) => {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) {
    throw new Error("No refresh token available");
  }
  try {
    const res = await axios.post(`${API_URL}/auth/jwt/refresh/`, { refresh });
    localStorage.setItem("access", res.data.access);
    failedRequest.response.config.headers.Authorization = `JWT ${res.data.access}`;
    return Promise.resolve();
  } catch (err) {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    if (window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
    throw err;
  }
};

createAuthRefreshInterceptor(client, refreshAuthLogic, {
  statusCodes: [401],
  pauseInstanceWhileRefreshing: true,
});

export default client;
