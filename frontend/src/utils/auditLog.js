// Lightweight audit-log utilities for tracking officer activity.
// Entries are kept in memory (lifted state in App.jsx) and rendered
// live on the Audit Trail screen. Swap `CURRENT_OFFICER` for the real
// logged-in user once auth is wired up.

let idCounter = 1;

export const CURRENT_OFFICER = 'Officer A. Sharma'; // TODO: replace with real logged-in user

export const AUDIT_ACTIONS = {
  VIEW_TENDER: 'VIEW_TENDER',
  CREATE_TENDER: 'CREATE_TENDER',
  ADD_REQUIREMENT: 'ADD_REQUIREMENT',
  EDIT_REQUIREMENT: 'EDIT_REQUIREMENT',
  DELETE_REQUIREMENT: 'DELETE_REQUIREMENT',
  APPROVE_CHECKLIST: 'APPROVE_CHECKLIST',
  REVERT_CHECKLIST: 'REVERT_CHECKLIST',
  ACCEPT_EVIDENCE: 'ACCEPT_EVIDENCE',
  REJECT_EVIDENCE: 'REJECT_EVIDENCE',
  REVIEW_EVIDENCE: 'REVIEW_EVIDENCE',
};

/**
 * Creates a single audit-log entry.
 * @param {string} action - one of AUDIT_ACTIONS
 * @param {string} description - human-readable summary shown in the UI
 * @param {object} [meta] - extra context, e.g. { tenderId, requirementId }
 */
export function createAuditEntry(action, description, meta = {}) {
  return {
    id: `audit_${Date.now()}_${idCounter++}`,
    timestamp: new Date().toISOString(),
    officer: CURRENT_OFFICER,
    action,
    description,
    ...meta,
  };
}