import React, { useMemo, useState } from 'react';
import { AUDIT_ACTIONS } from '@/utils/auditLog';

const ACTION_LABELS = {
  [AUDIT_ACTIONS.VIEW_TENDER]: 'Viewed Tender',
  [AUDIT_ACTIONS.CREATE_TENDER]: 'Created Tender',
  [AUDIT_ACTIONS.ADD_REQUIREMENT]: 'Added Requirement',
  [AUDIT_ACTIONS.EDIT_REQUIREMENT]: 'Edited Requirement',
  [AUDIT_ACTIONS.DELETE_REQUIREMENT]: 'Deleted Requirement',
  [AUDIT_ACTIONS.APPROVE_CHECKLIST]: 'Approved Checklist',
  [AUDIT_ACTIONS.REVERT_CHECKLIST]: 'Reverted Checklist',
  [AUDIT_ACTIONS.ACCEPT_EVIDENCE]: 'Accepted Evidence',
  [AUDIT_ACTIONS.REJECT_EVIDENCE]: 'Rejected Evidence',
  [AUDIT_ACTIONS.REVIEW_EVIDENCE]: 'Flagged Evidence for Review',
};

const ACTION_COLORS = {
  [AUDIT_ACTIONS.VIEW_TENDER]: 'bg-[#F0EEEA] text-[#5C554D]',
  [AUDIT_ACTIONS.CREATE_TENDER]: 'bg-[#E7F0EA] text-[#2F6B45]',
  [AUDIT_ACTIONS.ADD_REQUIREMENT]: 'bg-[#E7F0EA] text-[#2F6B45]',
  [AUDIT_ACTIONS.EDIT_REQUIREMENT]: 'bg-[#FBF1DE] text-[#8A6116]',
  [AUDIT_ACTIONS.DELETE_REQUIREMENT]: 'bg-[#FAEAE8] text-[#A13D33]',
  [AUDIT_ACTIONS.APPROVE_CHECKLIST]: 'bg-[#E7F0EA] text-[#2F6B45]',
  [AUDIT_ACTIONS.REVERT_CHECKLIST]: 'bg-[#FBF1DE] text-[#8A6116]',
  [AUDIT_ACTIONS.ACCEPT_EVIDENCE]: 'bg-[#E7F0EA] text-[#2F6B45]',
  [AUDIT_ACTIONS.REJECT_EVIDENCE]: 'bg-[#FAEAE8] text-[#A13D33]',
  [AUDIT_ACTIONS.REVIEW_EVIDENCE]: 'bg-[#FBF1DE] text-[#8A6116]',
};

function formatTimestamp(iso) {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export default function AuditTrailScreen({ logs = [] }) {
  const [actionFilter, setActionFilter] = useState('all');
  const [searchText, setSearchText] = useState('');

  const filteredLogs = useMemo(() => {
    return logs.filter((entry) => {
      const matchesAction =
        actionFilter === 'all' || entry.action === actionFilter;
      const matchesSearch =
        searchText.trim() === '' ||
        entry.description.toLowerCase().includes(searchText.toLowerCase()) ||
        entry.officer.toLowerCase().includes(searchText.toLowerCase()) ||
        (entry.tenderId || '').toLowerCase().includes(searchText.toLowerCase());
      return matchesAction && matchesSearch;
    });
  }, [logs, actionFilter, searchText]);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-bold text-[#2B2523]">Audit Trail Log</h1>
        <span className="text-xs text-[#786F66]">
          {logs.length} activit{logs.length === 1 ? 'y' : 'ies'} recorded
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search by officer, tender, or description..."
          className="flex-1 min-w-[220px] border border-[#E5E0DA] rounded-lg px-3 py-2 text-sm text-[#2B2523] bg-white placeholder:text-[#A69C92] focus:outline-none focus:ring-2 focus:ring-[#C9A15C]"
        />
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="border border-[#E5E0DA] rounded-lg px-3 py-2 text-sm text-[#2B2523] bg-white focus:outline-none focus:ring-2 focus:ring-[#C9A15C]"
        >
          <option value="all">All Actions</option>
          {Object.entries(ACTION_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Log table */}
      <div className="border border-[#E5E0DA] bg-white rounded-xl overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#786F66]">
            No activity recorded yet. Actions taken across the workstation
            will appear here.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#E5E0DA] bg-[#FAF8F5] text-left text-xs uppercase tracking-wide text-[#786F66]">
                <th className="px-4 py-3 font-medium">Timestamp</th>
                <th className="px-4 py-3 font-medium">Officer</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Details</th>
                <th className="px-4 py-3 font-medium">Tender</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-[#F0EEEA] last:border-0 hover:bg-[#FAF8F5]"
                >
                  <td className="px-4 py-3 whitespace-nowrap text-[#5C554D]">
                    {formatTimestamp(entry.timestamp)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-[#2B2523]">
                    {entry.officer}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        ACTION_COLORS[entry.action] ||
                        'bg-[#F0EEEA] text-[#5C554D]'
                      }`}
                    >
                      {ACTION_LABELS[entry.action] || entry.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[#5C554D]">
                    {entry.description}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-[#786F66]">
                    {entry.tenderId || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}