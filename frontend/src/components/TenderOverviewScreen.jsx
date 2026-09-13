import React, { useState } from 'react';
import { ChevronLeft, Lock, CheckCircle2 } from 'lucide-react';
import ChecklistTable from './ChecklistTable';
import TenderDocModal from './TenderDocModal';

export default function TenderOverviewScreen({ 
  tender, 
  onBackToDashboard, 
  onAddRequirement, 
  onEditRequirement, 
  onDeleteRequirement,
  onApproveChecklist 
}) {
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [confirmApproveOpen, setConfirmApproveOpen] = useState(false);

  if (!tender) return null;

  const isApproved = tender.checklist_approved;
  const reqCount = tender.requirements.length;

  const handleApproveClick = () => {
    if (reqCount === 0) return;
    if (isApproved) {
      onApproveChecklist(tender.tender_id, false);
    } else {
      setConfirmApproveOpen(true);
    }
  };

  const handleConfirmApproval = () => {
    onApproveChecklist(tender.tender_id, true);
    setConfirmApproveOpen(false);
  };

  const renderStatusLabel = () => {
    if (isApproved) {
      return (
        <span className="text-xs font-extrabold uppercase tracking-wider px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-md inline-block">
          Checklist Approved & Locked
        </span>
      );
    }
    return (
      <span className="text-xs font-extrabold uppercase tracking-wider px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-md inline-block">
        Pending Officer Approval
      </span>
    );
  };

  return (
    <div className="w-full px-8 py-8 space-y-8">
      <div className="flex items-center text-sm text-[#786F66]">
        <div className="flex items-center space-x-2 font-semibold">
          <button 
            onClick={onBackToDashboard}
            className="flex items-center space-x-1 hover:text-[#B3432E] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Tenders</span>
          </button>
          <span>/</span><span className="text-[#2B2523] font-extrabold">Extracted requirements</span>
        </div>
      </div>

      {/* Tender Header & Plain Label/Value Rows Stack */}
      <div className="border border-[#E5E0DA] bg-white rounded-2xl p-8 space-y-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-[#E5E0DA]">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">{renderStatusLabel()}</div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#2B2523]">Tender requirements</h1>
          </div>

          <div className="flex items-center shrink-0">
            <button
              disabled={reqCount === 0}
              onClick={handleApproveClick}
              className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center space-x-2 transition-colors ${
                isApproved
                  ? 'bg-emerald-700 hover:bg-emerald-800 text-white'
                  : 'bg-[#B3432E] hover:bg-[#9E3824] text-white shadow-xs'
              }`}
            >
              {isApproved ? (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Checklist Approved ✓</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve Checklist</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* MAIN CHECKLIST WORKSTATION SECTION */}
      <div className="space-y-5 pt-2">
        <div className="border-b border-[#E5E0DA] pb-3 flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-[#2B2523] uppercase tracking-wider">Extracted tender requirements</h2>
            <button
              onClick={() => setDocModalOpen(true)}
              className="mt-1 text-xs font-bold text-[#B3432E] hover:underline"
            >
              View source document
            </button>
          </div>
          <span className="text-xs text-[#786F66] font-bold">{reqCount} requirements ready for review</span>
        </div>

        <ChecklistTable
          tender={tender}
          requirements={tender.requirements}
          onAddRequirement={onAddRequirement}
          onEditRequirement={onEditRequirement}
          onDeleteRequirement={onDeleteRequirement}
          isApproved={isApproved}
        />
      </div>

      {/* Tender Document Modal */}
      <TenderDocModal
        open={docModalOpen}
        onOpenChange={setDocModalOpen}
        tender={tender}
      />

      {/* APPROVE CHECKLIST CONFIRMATION DIALOG */}
      {confirmApproveOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#E5E0DA] rounded-2xl p-8 max-w-lg w-full space-y-5 shadow-2xl">
            <h3 className="text-lg font-extrabold text-[#2B2523]">Approve Eligibility Checklist</h3>
            <p className="text-sm text-[#786F66] leading-relaxed">
              You are approving <strong className="text-[#2B2523] font-bold">{reqCount} eligibility requirements</strong> for tender <span className="font-mono font-bold text-[#B3432E]">{tender.tender_id}</span>. Once approved, these criteria lock the evaluation rules on the GeM portal.
            </p>

            <div className="flex justify-end space-x-3 pt-3">
              <button 
                onClick={() => setConfirmApproveOpen(false)}
                className="px-4 py-2 border border-[#E5E0DA] text-[#574E46] hover:bg-[#FAF8F5] rounded-xl text-sm font-semibold"
              >
                Back to Review
              </button>
              <button 
                onClick={handleConfirmApproval}
                className="px-5 py-2 bg-[#B3432E] hover:bg-[#9E3824] text-white rounded-xl text-sm font-extrabold shadow-xs"
              >
                Confirm & Approve Checklist ✓
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
