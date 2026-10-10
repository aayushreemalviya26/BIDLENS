// Production uses the same-origin /api proxy to retain HttpOnly cookies even
// when third-party cookies are blocked. This value is public, never a secret.
const API_URL = (import.meta.env.PROD ? window.location.origin : (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || window.location.origin)).replace(/\/$/, "");

export async function waitForBackend(signal) {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    try {
      const response = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]), cache: "no-store" });
      if (response.ok && (await response.json()).status === "ok") return;
    } catch { if (signal.aborted) return; }
    if (attempt < 7) await new Promise(resolve => setTimeout(resolve, 3000));
  }
  throw new Error("The demo server is taking longer than expected. Please retry in a minute.");
}

async function request(path, options = {}, checkSession = true) {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    cache: "no-store",
    ...options,
    headers: options.body instanceof FormData
      ? options.headers
      : { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    if (response.status === 401 && checkSession && path !== "/api/auth/login") {
      // A route-level 401 is not proof that the browser's session expired.
      // Never retry mutations automatically: the server may already have acted.
      let expired = path === "/api/auth/session";
      if (!expired) {
        try {
          const session = await fetch(`${API_URL}/api/auth/session`, { credentials: "include", cache: "no-store" });
          expired = session.status === 401;
        } catch { /* Keep the workspace on transient network/server failures. */ }
      }
      if (expired) window.dispatchEvent(new Event("bidlens:unauthenticated"));
    }
    if (response.status === 503) window.dispatchEvent(new CustomEvent("bidlens:ai-unavailable", { detail: error.detail }));
    const failure = new Error(error.detail || `Request failed (${response.status})`);
    failure.status = response.status;
    throw failure;
  }
  return response.json();
}

async function processingJob(kind, id, onProgress = () => {}) {
  onProgress("Starting authenticated processing…");
  const job = await request(`/api/jobs/${kind}/${id}`, { method: "POST" });
  onProgress("Processing started. Waiting for the AI pipeline…");
  for (let attempt = 0; attempt < 360; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    const state = await request(`/api/jobs/${job.job_id}`);
    if (state.status === "COMPLETED") return state.result;
    if (state.status === "FAILED") throw new Error(state.error || "Processing failed. The preprocessed demo remains available.");
    onProgress(`Processing is running (${(attempt + 1) * 5}s). This can take several minutes.`);
  }
  throw new Error("Processing exceeded the 30-minute wait limit. Check the audit trail before retrying.");
}

export const api = {
  demoAccess: () => request("/api/demo/access"),
  demo: () => request("/api/demo/workspace"),
  login: async (username, password) => {
    await request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
    try { return await request("/api/auth/session", {}, false); }
    catch (error) {
      if (error.status === 401) throw new Error("Sign-in succeeded but the session cookie was not retained. Allow cookies for this site and retry.");
      throw error;
    }
  },
  session: () => request("/api/auth/session", {}, false),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  setMode: (mode) => request("/api/auth/mode", { method: "POST", body: JSON.stringify({ mode }) }),
  aiHealth: () => request("/api/auth/health", { method: "POST" }),
  source: (path) => request(path),
  listTenders: () => request("/api/tenders"),
  tender: (tenderId) => request(`/api/tenders/${tenderId}`),
  createTender: (payload) => request("/api/tenders", { method: "POST", body: JSON.stringify(payload) }),
  uploadTender: (tenderId, file) => { const body = new FormData(); body.append("file", file); return request(`/api/tenders/${tenderId}/upload`, { method: "POST", body }); },
  extractTender: (tenderId, onProgress) => processingJob("tender", tenderId, onProgress),
  requirements: (tenderId) => request(`/api/tenders/${tenderId}/requirements`),
  addRequirement: (tenderId, payload) => request(`/api/tenders/${tenderId}/requirements`, { method: "POST", body: JSON.stringify(payload) }),
  patchRequirement: (requirementId, payload) => request(`/api/requirements/${requirementId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteRequirement: (requirementId) => request(`/api/requirements/${requirementId}`, { method: "DELETE" }),
  approveRequirements: (tenderId) => request(`/api/tenders/${tenderId}/approve`, { method: "POST" }),
  listBidders: (tenderId) => request(`/api/tenders/${tenderId}/bidders`),
  createBidder: (tenderId, payload) => request(`/api/tenders/${tenderId}/bidders`, { method: "POST", body: JSON.stringify(payload) }),
  uploadBidderFiles: (bidderId, files) => { const body = new FormData(); Array.from(files).forEach((file) => body.append("files", file)); return request(`/api/bidders/${bidderId}/upload`, { method: "POST", body }); },
  processBidder: (bidderId) => processingJob("bidder", bidderId),
  evaluate: (tenderId) => request(`/api/tenders/${tenderId}/evaluate`, { method: "POST" }),
  completeness: (tenderId) => request(`/api/tenders/${tenderId}/document-completeness`),
  resetDemo: () => request("/api/demo/reset", { method: "POST" }),
  complianceMatrix: (tenderId) => request(`/api/tenders/${tenderId}/compliance-matrix`),
  complianceEvidence: (checkId) => request(`/api/compliance/${checkId}/evidence`),
  audit: (tenderId) => request(`/api/tenders/${tenderId}/audit`),
  accept: (checkId, remarks) => request(`/api/compliance/${checkId}/accept`, { method: "POST", body: JSON.stringify({ remarks }) }),
  clarification: (checkId, message) => request(`/api/compliance/${checkId}/clarification`, { method: "POST", body: JSON.stringify({ message: message || "Please provide clarification and supporting evidence." }) }),
  override: (checkId, newStatus, remarks) => request(`/api/compliance/${checkId}/override`, { method: "POST", body: JSON.stringify({ new_status: newStatus, remarks }) }),
  absoluteUrl: (path) => !path || /^https?:/i.test(path) ? path : `${API_URL}${path.startsWith("/") ? "" : "/"}${path}`,
};
