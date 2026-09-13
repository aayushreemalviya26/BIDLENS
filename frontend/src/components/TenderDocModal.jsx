import React from 'react';
import { MOCK_TENDER_DOCUMENT } from '@/data/mockData';

export default function TenderDocModal({ open, onOpenChange, tender }) {
  if (!open) return null;
  const doc = MOCK_TENDER_DOCUMENT;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-[#E5E0DA] rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-[#E5E0DA] bg-[#FAF8F5] flex items-center justify-between">
          <div>
            <div className="text-xs font-extrabold text-[#B3432E] uppercase tracking-wider">
              Tender document reader
            </div>
            <h2 className="text-lg font-extrabold text-[#2B2523] mt-1">
              {tender?.source_document || tender?.title || doc.title}
            </h2>
            <p className="text-xs text-[#786F66] font-mono mt-0.5">
              Uploaded source document
            </p>
          </div>

          <button 
            onClick={() => onOpenChange(false)}
            className="text-[#786F66] hover:text-[#2B2523] text-base font-bold px-3 py-1.5"
          >
            ✕
          </button>
        </div>

        {/* STACKED LIST (High Readability Typography) */}
        <div className="p-6 overflow-y-auto max-h-[60vh] divide-y divide-[#E5E0DA]">
          {doc.clauses.map((clause, idx) => (
            <div key={idx} className="py-5 first:pt-0 last:pb-0 space-y-2">
              <div className="text-xs font-bold text-[#786F66] uppercase tracking-wider">
                Clause {clause.clause} • Page {clause.page}
              </div>
              <h4 className="text-base font-extrabold text-[#1C1917]">{clause.title}</h4>
              <p className="text-sm text-[#2B2523] leading-relaxed pt-1 font-medium">
                "{clause.text}"
              </p>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-[#E5E0DA] bg-[#FAF8F5] flex items-center justify-between">
          <span className="text-xs text-[#786F66] font-semibold">
            Showing 7 parsed clauses from original tender PDF
          </span>
          <button
            onClick={() => onOpenChange(false)}
            className="px-5 py-2 border border-[#E5E0DA] bg-white text-[#2B2523] hover:bg-[#F5F1EB] rounded-xl text-sm font-semibold transition-colors"
          >
            Close Reader
          </button>
        </div>
      </div>
    </div>
  );
}
