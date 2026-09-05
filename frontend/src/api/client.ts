import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

function getTokens() {
  const raw = localStorage.getItem("resumeai_tokens");
  return raw ? JSON.parse(raw) : null;
}

function setTokens(tokens: { access_token: string; refresh_token: string } | null) {
  if (tokens) localStorage.setItem("resumeai_tokens", JSON.stringify(tokens));
  else localStorage.removeItem("resumeai_tokens");
}

api.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access_token) {
    config.headers.Authorization = `Bearer ${tokens.access_token}`;
  }
  return config;
});

let isRefreshing = false;
let pendingQueue: Array<() => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      const tokens = getTokens();
      if (!tokens?.refresh_token) {
        setTokens(null);
        window.location.href = "/login";
        return Promise.reject(error);
      }

      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingQueue.push(() => resolve(api(original)));
        });
      }

      isRefreshing = true;
      try {
        const { data } = await axios.post(`${API_BASE}/api/auth/refresh`, {
          refresh_token: tokens.refresh_token,
        });
        setTokens(data);
        pendingQueue.forEach((cb) => cb());
        pendingQueue = [];
        return api(original);
      } catch (refreshError) {
        setTokens(null);
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export { getTokens, setTokens };

export function apiErrorMessage(error: unknown): string {
  const anyErr = error as any;
  return anyErr?.response?.data?.error?.message || anyErr?.message || "Something went wrong. Please try again.";
}
