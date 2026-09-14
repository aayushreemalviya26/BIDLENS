const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: options.body instanceof FormData
      ? options.headers
      : { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export const api = {
  listTenders: () => request("/api/tenders"),
  tender: (tenderId) => request(`/api/tenders/${tenderId}`),
  createTender: (payload) => request("/api/tenders", { method: "POST", body: JSON.stringify(payload) }),
  uploadTender: (tenderId, file) => { const body = new FormData(); body.append("file", file); return request(`/api/tenders/${tenderId}/upload`, { method: "POST", body }); },
  extractTender: (tenderId) => request(`/api/tenders/${tenderId}/extract`, { method: "POST" }),
  requirements: (tenderId) => request(`/api/tenders/${tenderId}/requirements`),
  addRequirement: (tenderId, payload) => request(`/api/tenders/${tenderId}/requirements`, { method: "POST", body: JSON.stringify(payload) }),
  patchRequirement: (requirementId, payload) => request(`/api/requirements/${requirementId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteRequirement: (requirementId) => request(`/api/requirements/${requirementId}`, { method: "DELETE" }),
  approveRequirements: (tenderId) => request(`/api/tenders/${tenderId}/approve`, { method: "POST" }),
  listBidders: (tenderId) => request(`/api/tenders/${tenderId}/bidders`),
  createBidder: (tenderId, payload) => request(`/api/tenders/${tenderId}/bidders`, { method: "POST", body: JSON.stringify(payload) }),
  uploadBidderFiles: (bidderId, files) => { const body = new FormData(); Array.from(files).forEach((file) => body.append("files", file)); return request(`/api/bidders/${bidderId}/upload`, { method: "POST", body }); },
  processBidder: (bidderId) => request(`/api/bidders/${bidderId}/process`, { method: "POST" }),
  evaluate: (tenderId) => request(`/api/tenders/${tenderId}/evaluate`, { method: "POST" }),
  completeness: (tenderId) => request(`/api/tenders/${tenderId}/document-completeness`),
  resetDemo: () => request("/api/demo/reset", { method: "POST" }),
  complianceMatrix: (tenderId) => request(`/api/tenders/${tenderId}/compliance-matrix`),
  complianceEvidence: (checkId) => request(`/api/compliance/${checkId}/evidence`),
  audit: (tenderId) => request(`/api/tenders/${tenderId}/audit`),
  accept: (checkId, remarks) => request(`/api/compliance/${checkId}/accept`, { method: "POST", body: JSON.stringify({ remarks }) }),
  clarification: (checkId, message) => request(`/api/compliance/${checkId}/clarification`, { method: "POST", body: JSON.stringify({ message: message || "Please provide clarification and supporting evidence." }) }),
  override: (checkId, newStatus, remarks) => request(`/api/compliance/${checkId}/override`, { method: "POST", body: JSON.stringify({ new_status: newStatus, remarks: remarks || "Officer override recorded from compliance matrix." }) }),
  absoluteUrl: (path) => !path || /^https?:/i.test(path) ? path : `${API_URL}${path.startsWith("/") ? "" : "/"}${path}`,
};
