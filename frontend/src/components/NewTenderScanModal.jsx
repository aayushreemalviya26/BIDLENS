import React, { useRef, useState } from 'react';
import { CheckCircle2, FileText, Upload } from 'lucide-react';

// Mirrors the JSON result shape supplied for the tender extraction pipeline.
const EXTRACTION_RESULTS = [
  { query: 'GST Registration', status: 'found', requirements: [{ page: 3, requirement: 'The bidder must hold an active GST Registration Certificate.' }] },
  { query: 'Make in India / Local Content', status: 'found', requirements: [{ page: 7, requirement: 'Minimum 50% local content is required for qualification as a Class 1 supplier.' }] },
  { query: 'EPFO / ESIC', status: 'not_found', requirements: [] },
  { query: 'Startup India', status: 'not_found', requirements: [] }
];

export default function NewTenderScanModal({ open, onOpenChange, onAddNewTender }) {
  const [step, setStep] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  if (!open) return null;

  const close = () => {
    setStep('upload');
    setSelectedFile(null);
    onOpenChange(false);
  };

  const continueToVerify = (event) => {
    event.preventDefault();
    if (selectedFile) setStep('verify');
  };

  const verifyAndOpenRequirements = () => {
    const newTender = {
      tender_id: `tender-${Date.now()}`,
      title: selectedFile.name,
      bids_count: 0,
      status: 'Under Evaluation',
      last_updated: 'Just Now',
      checklist_approved: false,
      source_document: selectedFile.name,
      extraction_results: EXTRACTION_RESULTS,
      requirements: EXTRACTION_RESULTS.filter((result) => result.status === 'found').flatMap((result, resultIndex) =>
        result.requirements.map((item, itemIndex) => ({
          requirement_id: `REQ_${resultIndex + 1}_${itemIndex + 1}`,
          name: item.requirement,
          category: result.query,
          source: { clause: result.query, page: item.page },
          approved: true
        }))
      )
    };
    onAddNewTender(newTender);
    close();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-[#E5E0DA] rounded-2xl p-8 max-w-xl w-full space-y-6 shadow-2xl">
        <div className="flex items-start justify-between border-b border-[#E5E0DA] pb-5">
          <div>
            <h3 className="text-xl font-extrabold text-[#2B2523]">Add tender document</h3>
            <p className="text-sm text-[#786F66] font-medium mt-1">{step === 'upload' ? 'Upload the RFP first. You will verify its details next.' : 'Confirm the document details before reviewing requirements.'}</p>
          </div>
          <button onClick={close} aria-label="Close" className="text-[#786F66] hover:text-[#2B2523] text-lg font-bold px-3 py-2 rounded-xl hover:bg-[#F5F1EB] transition-colors">✕</button>
        </div>

        {step === 'upload' ? (
          <form onSubmit={continueToVerify} className="space-y-5 text-sm">
            <div>
              <label className="font-bold text-[#2B2523] block mb-2">Tender document</label>
              <p className="text-sm text-[#786F66]">Upload one PDF. Tender details and requirements come from the backend extraction result.</p>
            </div>
            <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} />
            <button type="button" onClick={() => fileInputRef.current?.click()} className="w-full border-2 border-dashed border-[#E5E0DA] bg-[#FAF8F5] rounded-2xl p-7 text-center space-y-2 hover:border-[#B3432E]/50 transition-colors">
              {selectedFile ? <FileText className="w-8 h-8 text-[#B3432E] mx-auto" /> : <Upload className="w-8 h-8 text-[#B3432E] mx-auto" />}
              <p className="font-bold text-[#2B2523]">{selectedFile ? selectedFile.name : 'Choose tender RFP document'}</p>
              <p className="text-xs text-[#786F66]">PDF format • Select one document</p>
            </button>
            <div className="flex justify-end pt-2"><button type="submit" disabled={!selectedFile} className="px-6 py-2.5 bg-[#B3432E] hover:bg-[#9E3824] disabled:bg-[#B3432E]/40 disabled:cursor-not-allowed text-white rounded-xl text-sm font-extrabold transition-colors">Continue to verification</button></div>
          </form>
        ) : (
          <div className="space-y-5">
            <div className="rounded-xl border border-[#E5E0DA] bg-[#FAF8F5] divide-y divide-[#E5E0DA] text-sm">
              <div className="p-4 flex gap-3 items-center"><FileText className="w-5 h-5 text-[#B3432E] shrink-0" /><div><p className="font-bold text-[#2B2523]">{selectedFile?.name}</p><p className="text-xs text-[#786F66]">Tender RFP document</p></div></div>
            </div>
            <p className="text-sm leading-relaxed text-[#786F66]">The document is ready for verification. Requirement extraction is handled by the backend, so this flow does not simulate a progress timer.</p>
            <div className="flex items-center justify-between gap-3 pt-2"><button onClick={() => setStep('upload')} className="px-4 py-2.5 text-sm font-semibold text-[#574E46] hover:bg-[#F5F1EB] rounded-xl">Back</button><button onClick={verifyAndOpenRequirements} className="px-5 py-2.5 bg-[#B3432E] hover:bg-[#9E3824] text-white rounded-xl text-sm font-extrabold flex items-center gap-2 transition-colors"><CheckCircle2 className="w-4 h-4" />Verify & open requirements</button></div>
          </div>
        )}
      </div>
    </div>
  );
}
