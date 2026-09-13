import React from 'react';
import { ChevronRight, Filter } from 'lucide-react';

export default function DashboardScreen({ tenders, onSelectTender, searchQuery }) {
  const filteredTenders = tenders.filter(t => 
    t.tender_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeTendersCount = tenders.length;
  const totalBidsCount = tenders.reduce((acc, t) => acc + t.bids_count, 0);
  const underEvaluationCount = tenders.filter(t => t.status === 'Under Evaluation').length;
  const pendingReviewCount = tenders.filter(t => !t.checklist_approved).length;

  const renderStatusLabel = (status, approved) => {
    if (approved || status === 'Checklist Approved') {
      return (
        <span className="text-xs font-extrabold uppercase tracking-wider px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-md inline-block">
          Checklist Approved
        </span>
      );
    }
    if (status === 'Under Evaluation') {
      return (
        <span className="text-xs font-extrabold uppercase tracking-wider px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-md inline-block">
          Under Evaluation
        </span>
      );
    }
    return (
      <span className="text-xs font-extrabold uppercase tracking-wider px-3 py-1 bg-neutral-100 text-neutral-700 border border-neutral-300 rounded-md inline-block">
        Draft
      </span>
    );
  };

  return (
    <div className="w-full px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">
            GeM Procurement Portal • Officer Workstation
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#2B2523]">Procurement Overview</h1>
          <p className="text-sm text-[#786F66] font-medium mt-1">
            Monitor tender eligibility compliance, review AI-extracted criteria, and approve checklists for evaluation.
          </p>
        </div>
      </div>

      {/* SINGLE STAT STRIP (High Readability & Full Width) */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl overflow-hidden shadow-xs">
        <div className="grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-[#E5E0DA]">
          <div className="p-6 md:p-8 flex flex-col justify-center">
            <span className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">Active Tenders</span>
            <div className="text-4xl font-extrabold text-[#2B2523] tracking-tight">{activeTendersCount}</div>
          </div>

          <div className="p-6 md:p-8 flex flex-col justify-center">
            <span className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">Bids Received</span>
            <div className="text-4xl font-extrabold text-[#2B2523] tracking-tight">{totalBidsCount}</div>
          </div>

          <div className="p-6 md:p-8 flex flex-col justify-center">
            <span className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">Under Evaluation</span>
            <div className="text-4xl font-extrabold text-amber-800 tracking-tight">{underEvaluationCount}</div>
          </div>

          <div className="p-6 md:p-8 flex flex-col justify-center">
            <span className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">Pending Review</span>
            <div className="text-4xl font-extrabold text-[#B3432E] tracking-tight">{pendingReviewCount}</div>
          </div>
        </div>
      </div>

      {/* STRIPPED-DOWN RECENT TENDERS TABLE (Full Width) */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl overflow-hidden shadow-xs">
        <div className="p-6 border-b border-[#E5E0DA] flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#2B2523]">Recent Tenders</h2>
            <p className="text-xs text-[#786F66] font-medium">Select a tender row to review its compliance checklist</p>
          </div>

          <button className="border border-[#E5E0DA] hover:bg-[#F5F1EB] text-[#574E46] px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-colors">
            <Filter className="w-4 h-4 text-[#786F66]" />
            <span>Filter</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E0DA] text-xs font-extrabold uppercase tracking-wider text-[#574E46]">
                <th className="py-4 px-6">Tender ID</th>
                <th className="py-4 px-6">Title & Est. Value</th>
                <th className="py-4 px-6">Department</th>
                <th className="py-4 px-6 text-center">Bids</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Last Updated</th>
                <th className="py-4 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0DA] text-sm">
              {filteredTenders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-[#786F66] text-sm">
                    No tenders found matching "{searchQuery}".
                  </td>
                </tr>
              ) : (
                filteredTenders.map((tender) => (
                  <tr
                    key={tender.tender_id}
                    onClick={() => onSelectTender(tender.tender_id)}
                    className="cursor-pointer hover:bg-[#FAF8F5] transition-colors group"
                  >
                    <td className="py-4 px-6 font-mono font-extrabold text-sm text-[#B3432E]">
                      {tender.tender_id}
                    </td>

                    <td className="py-4 px-6">
                      <div className="font-bold text-[#2B2523] text-base group-hover:text-[#B3432E] transition-colors">
                        {tender.title}
                      </div>
                      <div className="text-xs text-[#786F66] font-medium mt-0.5">Est. Value: <strong className="text-[#2B2523]">{tender.estimated_value}</strong></div>
                    </td>

                    <td className="py-4 px-6 text-[#574E46] font-semibold text-sm">
                      {tender.department}
                    </td>

                    <td className="py-4 px-6 text-center font-extrabold text-base text-[#2B2523]">
                      {tender.bids_count}
                    </td>

                    <td className="py-4 px-6">
                      {renderStatusLabel(tender.status, tender.checklist_approved)}
                    </td>

                    <td className="py-4 px-6 text-xs text-[#786F66] font-medium">
                      {tender.last_updated}
                    </td>

                    <td className="py-4 px-6 text-right">
                      <span className="text-[#B3432E] font-bold text-sm flex items-center justify-end space-x-1 hover:underline">
                        <span>Review</span>
                        <ChevronRight className="w-4 h-4 ml-0.5" />
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
