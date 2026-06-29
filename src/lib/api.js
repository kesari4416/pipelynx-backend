// Centralized API client for Pipelynx
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api/v1`;

const TOKEN_KEY = "pipelynx_token";
const USER_KEY = "pipelynx_user";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export const userStorage = {
  get: () => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  set: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
};

// Axios instance with interceptors
export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
      // Redirect to login if we're not already there
      if (!window.location.pathname.startsWith("/auth")) {
        window.location.href = "/auth/login";
      }
    }
    // 402 Payment Required → broadcast to the global upgrade modal
    if (error.response?.status === 402) {
      const detail = error.response.data?.detail;
      // Detail may be a plain string or our structured payload
      const payload = typeof detail === "object" ? detail : { detail };
      window.dispatchEvent(new CustomEvent("pipelynx:upgrade-required", { detail: payload }));
    }
    return Promise.reject(error);
  }
);

// ============ Billing APIs ============
// Region & plans are public; subscription & intent require auth (handled by interceptor).
export const billingApi = {
  region: () => api.get("/billing/region").then((r) => r.data),
  plans: () => api.get("/billing/plans").then((r) => r.data),
  subscription: () => api.get("/billing/subscription").then((r) => r.data),
  limits: () => api.get("/billing/limits").then((r) => r.data),
  recordIntent: (data) => api.post("/billing/intent", data).then((r) => r.data),
  cancel: () => api.post("/billing/cancel").then((r) => r.data),
};

// ============ Auth APIs ============
export const authApi = {
  register: (data) => api.post("/auth/register", data).then((r) => r.data),
  login: (data) => api.post("/auth/login", data).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
};

// ============ Organization APIs ============
export const orgApi = {
  me: () => api.get("/organizations/me").then((r) => r.data),
};

// ============ Pipeline APIs ============
export const pipelineApi = {
  list: () => api.get("/pipelines/").then((r) => r.data),
  get: (id) => api.get(`/pipelines/${id}`).then((r) => r.data),
  listIntegrations: () => api.get("/pipelines/integrations").then((r) => r.data),
  createIntegration: (data) =>
    api.post("/pipelines/integrations", data).then((r) => r.data),
  deleteIntegration: (id) =>
    api.delete(`/pipelines/integrations/${id}`).then((r) => r.data),
  setupGuide: (id) =>
    api.get(`/pipelines/integrations/${id}/setup-guide`).then((r) => r.data),
  syncNow: (id) =>
    api.post(`/pipelines/integrations/${id}/sync`).then((r) => r.data),
};

// ============ Runs APIs ============
export const runsApi = {
  list: (params = {}) => api.get("/runs/", { params }).then((r) => r.data),
  get: (id) => api.get(`/runs/${id}`).then((r) => r.data),
  live: () => api.get("/runs/live").then((r) => r.data),
};

// ============ Metrics APIs ============
export const metricsApi = {
  summary: (days = 30) =>
    api.get("/metrics/summary", { params: { days } }).then((r) => r.data),
  dora: (days = 30) =>
    api.get("/metrics/dora", { params: { days } }).then((r) => r.data),
  timeseries: (days = 30, bucket = "day") =>
    api.get("/metrics/timeseries", { params: { days, bucket } }).then((r) => r.data),
  topFailing: (days = 30, limit = 10) =>
    api.get("/metrics/top-failing", { params: { days, limit } }).then((r) => r.data),
};

// ============ AI APIs ============
export const aiApi = {
  analyzeRun: (runId) => api.post(`/ai/runs/${runId}/analyze`).then((r) => r.data),
  patterns: (days = 7) => api.get("/ai/patterns", { params: { days } }).then((r) => r.data),
  digest: () => api.get("/ai/digest").then((r) => r.data),
  anomalies: (days = 30) => api.get("/ai/anomalies", { params: { days } }).then((r) => r.data),
};

// ============ Alerts APIs ============
export const alertsApi = {
  listRules: () => api.get("/alerts/rules").then((r) => r.data),
  createRule: (data) => api.post("/alerts/rules", data).then((r) => r.data),
  deleteRule: (id) => api.delete(`/alerts/rules/${id}`).then((r) => r.data),
  history: (limit = 50) => api.get("/alerts/history", { params: { limit } }).then((r) => r.data),
  test: (channel, config) => api.post("/alerts/test", { channel, config }).then((r) => r.data),
};

// ============ Webhook simulation (for testing) ============
export const webhookApi = {
  github: (payload, eventType = "workflow_run") =>
    axios.post(`${BACKEND_URL}/api/v1/webhooks/github`, payload, {
      headers: {
        "Content-Type": "application/json",
        "X-GitHub-Event": eventType,
      },
    }),
  gitlab: (payload) =>
    axios.post(`${BACKEND_URL}/api/v1/webhooks/gitlab`, payload, {
      headers: {
        "Content-Type": "application/json",
        "X-Gitlab-Event": "Pipeline Hook",
      },
    }),
  jenkins: (payload) =>
    axios.post(`${BACKEND_URL}/api/v1/webhooks/jenkins`, payload),
};
