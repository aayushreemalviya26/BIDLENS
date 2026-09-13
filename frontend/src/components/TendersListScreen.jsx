import React, { useState } from 'react';
import { Search, ChevronRight } from 'lucide-react';

export default function TendersListScreen({ tenders, onSelectTender, searchQuery, setSearchQuery }) {
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filteredTenders = tenders.filter(tender => {
    const matchesSearch = 
      tender.title.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || 
      (statusFilter === 'APPROVED' && tender.checklist_approved) ||
      (statusFilter === 'EVALUATION' && !tender.checklist_approved && tender.status === 'Under Evaluation') ||
      (statusFilter === 'DRAFT' && tender.status === 'Draft');

    return matchesSearch && matchesStatus;
  });

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
            Tenders Directory • GeM Master Index
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#2B2523]">All Government Procurement Tenders</h1>
          <p className="text-sm text-[#786F66] font-medium mt-1">
            Search, filter, and inspect tender eligibility checklists across all active government buyers.
          </p>
        </div>
      </div>

      {/* Clean Filter & Search Toolbar */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl p-5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-xs">
        <div className="relative flex-1 max-w-xl">
          <Search className="absolute left-4 top-3.5 h-4 w-4 text-[#786F66]" />
          <input
            type="text"
            placeholder="Search uploaded tender documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 h-11 text-sm bg-[#FAF8F5] border border-[#E5E0DA] rounded-xl focus:outline-none focus:border-[#B3432E] transition-colors"
          />
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-[#786F66] font-semibold">Status:</span>
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-11 px-3 bg-white border border-[#E5E0DA] rounded-xl text-sm text-[#2B2523] font-semibold focus:outline-none focus:border-[#B3432E]"
            >
              <option value="ALL">All Statuses</option>
              <option value="EVALUATION">Under Evaluation</option>
              <option value="APPROVED">Checklist Approved</option>
              <option value="DRAFT">Draft</option>
            </select>
          </div>

        </div>
      </div>

      {/* STRIPPED-DOWN TENDERS TABLE */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl overflow-hidden shadow-xs">
        <div className="p-6 border-b border-[#E5E0DA] flex items-center justify-between">
          <h3 className="text-base font-bold text-[#2B2523]">GeM Tender Directory ({filteredTenders.length})</h3>
          <span className="text-xs text-[#786F66] font-medium">Click any tender row to inspect eligibility checklist</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E0DA] text-xs font-extrabold uppercase tracking-wider text-[#574E46]">
                <th className="py-4 px-6">Document</th>
                <th className="py-4 px-6 text-center">Bids</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0DA] text-sm">
              {filteredTenders.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-[#786F66] text-sm">
                    No tenders found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredTenders.map((tender) => (
                  <tr
                    key={tender.tender_id}
                    onClick={() => onSelectTender(tender.tender_id)}
                    className="cursor-pointer hover:bg-[#FAF8F5] transition-colors group"
                  >
                    <td className="py-4 px-6">
                      <div className="font-bold text-[#2B2523] text-base group-hover:text-[#B3432E] transition-colors">
                        {tender.title}
                      </div>
                    </td>

                    <td className="py-4 px-6 text-center font-extrabold text-base text-[#2B2523]">
                      {tender.bids_count}
                    </td>

                    <td className="py-4 px-6">
                      {renderStatusLabel(tender.status, tender.checklist_approved)}
                    </td>

                    <td className="py-4 px-6 text-right">
                      <span className="text-[#B3432E] font-bold text-sm flex items-center justify-end space-x-1 hover:underline">
                        <span>Checklist</span>
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
