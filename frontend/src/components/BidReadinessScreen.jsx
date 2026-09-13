import React, { useState } from 'react';
import { CheckCircle2, ChevronRight, FileText, ShieldAlert, XCircle } from 'lucide-react';

// Synthetic bidder evidence follows the pipeline contract. Status is derived
// only from evidence linked to a tender requirement; fee, VAT, unit, and value
// are deliberately not modelled or displayed.
const BIDDER_DATA = [
  {
    bidder_id: 'B01',
    bidder_name: 'Apex Safety Pvt. Ltd.',
    source_file: 'apex-safety-bid.pdf',
    evidence: ['REQ01', 'REQ02', 'REQ02A', 'REQ02B', 'REQ03', 'REQ04', 'REQ05', 'REQ06', 'REQ07', 'REQ08'].map((requirement_id, index) => ({
      evidence_id: `EVD_01${String(index + 1).padStart(3, '0')}`,
      requirement_id,
      document_id: `DOC_01${String(index + 1).padStart(3, '0')}`,
      document_title: 'Bidder supporting document',
      category: 'Tender compliance',
      page_start: index + 1,
      page_end: index + 1,
      field: 'document_evidence',
      entity: 'Apex Safety Pvt. Ltd.',
      evidence_text: 'Supporting document found and linked to the tender requirement.',
      source_chunk_ids: [`CHUNK_01${String(index + 1).padStart(3, '0')}`],
      confidence: 0.98,
      ambiguity: null
    }))
  },
  {
    bidder_id: 'B02',
    bidder_name: 'Bharat Power Control Systems Pvt. Ltd.',
    source_file: 'bidder.pdf',
    evidence: [
      { evidence_id: 'EVD_00001', requirement_id: 'REQ01', document_id: 'DOC_001', document_title: 'GST Registration Certificate', category: 'GST', page_start: 1, page_end: 2, field: 'gstin', entity: 'Bharat Power Control Systems Pvt. Ltd.', evidence_text: 'GSTIN: 07ABCDE1234F1Z5', source_chunk_ids: ['CHUNK_00001'], confidence: 0.98, ambiguity: null },
      { evidence_id: 'EVD_00002', requirement_id: 'REQ02', document_id: 'DOC_002', document_title: 'Udyam Registration Certificate', category: 'Udyam / MSME', page_start: 3, page_end: 3, field: 'udyam_registration', entity: 'Bharat Power Control Systems Pvt. Ltd.', evidence_text: 'Udyam registration certificate submitted.', source_chunk_ids: ['CHUNK_00002'], confidence: 0.96, ambiguity: null },
      { evidence_id: 'EVD_00003', requirement_id: 'REQ03', document_id: 'DOC_003', document_title: 'BIS Licence', category: 'BIS / DPIIT', page_start: 6, page_end: 6, field: 'bis_licence', entity: 'Bharat Power Control Systems Pvt. Ltd.', evidence_text: 'BIS licence identified in the submitted document.', source_chunk_ids: ['CHUNK_00003'], confidence: 0.95, ambiguity: null },
      { evidence_id: 'EVD_00004', requirement_id: 'REQ04', document_id: 'DOC_004', document_title: 'OEM Authorization Certificate', category: 'OEM Authorization', page_start: 7, page_end: 7, field: 'oem_authorization', entity: 'Bharat Power Control Systems Pvt. Ltd.', evidence_text: 'OEM authorization certificate submitted.', source_chunk_ids: ['CHUNK_00004'], confidence: 0.97, ambiguity: null }
    ]
  },
  {
    bidder_id: 'B03',
    bidder_name: 'National Equipment Traders',
    source_file: 'national-equipment-bid.pdf',
    evidence: [
      { evidence_id: 'EVD_00011', requirement_id: 'REQ01', document_id: 'DOC_011', document_title: 'GST Registration Certificate', category: 'GST', page_start: 1, page_end: 1, field: 'gstin', entity: 'National Equipment Traders', evidence_text: 'GST registration evidence identified.', source_chunk_ids: ['CHUNK_00011'], confidence: 0.94, ambiguity: null },
      { evidence_id: 'EVD_00012', requirement_id: 'REQ03', document_id: 'DOC_012', document_title: 'BIS Licence', category: 'BIS / DPIIT', page_start: 4, page_end: 4, field: 'bis_licence', entity: 'National Equipment Traders', evidence_text: 'BIS licence identified in the submitted document.', source_chunk_ids: ['CHUNK_00012'], confidence: 0.93, ambiguity: null },
      { evidence_id: 'EVD_00013', requirement_id: 'REQ04', document_id: 'DOC_013', document_title: 'OEM Authorization Certificate', category: 'OEM Authorization', page_start: 5, page_end: 5, field: 'oem_authorization', entity: 'National Equipment Traders', evidence_text: 'OEM authorization certificate submitted.', source_chunk_ids: ['CHUNK_00013'], confidence: 0.95, ambiguity: null }
    ]
  }
];

const DETAIL_COPY = {
  compliant: {
    label: 'Compliant',
    description: 'The submitted evidence meets the tender requirement.',
    evidence: 'Document verified against the stated source clause and expected value.'
  },
  not_compliant: {
    label: 'Not compliant',
    description: 'The submitted evidence does not meet this tender requirement.',
    evidence: 'Required evidence is missing, expired, or does not satisfy the stated condition.'
  }
};

export default function BidReadinessScreen({ tender }) {
  const [selectedResult, setSelectedResult] = useState(null);
  if (!tender) return null;

  const requirements = tender.requirements;
  const compliantCount = BIDDER_DATA.filter((bidder) => requirements.every((requirement) => bidder.evidence.some((item) => item.requirement_id === requirement.requirement_id))).length;

  return (
    <div className="w-full px-8 py-8 space-y-7">
      <div className="flex items-end justify-between gap-6">
        <div>
          <p className="text-xs font-extrabold text-[#786F66] uppercase tracking-wider mb-1">Tender evaluation</p>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#2B2523]">Bidder evaluation</h1>
          <p className="text-sm text-[#786F66] font-medium mt-1">Review each bidder against the approved tender requirements. Select a status to see the reason.</p>
        </div>
        <div className="rounded-xl border border-[#E5E0DA] bg-white px-4 py-3 text-right shrink-0">
          <p className="text-xs font-bold text-[#786F66]">READY TO PROCEED</p>
          <p className="text-lg font-extrabold text-emerald-800">{compliantCount} of {BIDDER_DATA.length} bidders</p>
        </div>
      </div>

      <div className="border border-[#E5E0DA] bg-white rounded-2xl overflow-hidden shadow-xs">
        <div className="p-5 border-b border-[#E5E0DA] flex items-center justify-between">
          <div>
            <h2 className="font-extrabold text-[#2B2523]">Requirement compliance</h2>
            <p className="text-xs text-[#786F66] mt-1">{tender.title}</p>
          </div>
          <span className="text-xs font-bold text-[#786F66]">Click any result for evidence</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E0DA] text-xs font-extrabold uppercase tracking-wider text-[#574E46]">
                <th className="py-4 px-6 min-w-[250px]">Requirement</th>
                <th className="py-4 px-6 min-w-[160px]">Tender source</th>
                {BIDDER_DATA.map((bidder) => <th key={bidder.bidder_id} className="py-4 px-5 min-w-[185px]">{bidder.bidder_name}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E0DA] text-sm">
              {requirements.map((requirement) => (
                <tr key={requirement.requirement_id} className="hover:bg-[#FAF8F5] transition-colors">
                  <td className="py-4 px-6"><p className="font-bold text-[#2B2523]">{requirement.name}</p><p className="text-xs text-[#786F66] mt-0.5">Clause {requirement.source.clause} · Page {requirement.source.page}</p></td>
                  <td className="py-4 px-6 font-bold text-[#574E46]">Source page {requirement.source.page}</td>
                  {BIDDER_DATA.map((bidder) => {
                    const evidence = bidder.evidence.find((item) => item.requirement_id === requirement.requirement_id);
                    const result = evidence ? 'compliant' : 'not_compliant';
                    const isCompliant = result === 'compliant';
                    return (
                      <td key={bidder.bidder_id} className="py-4 px-5">
                        <button onClick={() => setSelectedResult({ bidder, requirement, result, evidence })} className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-extrabold transition-colors ${isCompliant ? 'border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100' : 'border-rose-200 bg-rose-50 text-rose-800 hover:bg-rose-100'}`}>
                          {isCompliant ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                          {DETAIL_COPY[result].label}
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedResult && <EvidenceDrawer selectedResult={selectedResult} onClose={() => setSelectedResult(null)} />}
    </div>
  );
}

function EvidenceDrawer({ selectedResult, onClose }) {
  const { bidder, requirement, result, evidence } = selectedResult;
  const detail = DETAIL_COPY[result];
  const isCompliant = result === 'compliant';
  return (
    <div className="fixed inset-0 z-40 bg-black/30 flex justify-end">
      <button aria-label="Close evidence panel" onClick={onClose} className="flex-1 cursor-default" />
      <aside className="relative z-50 h-full w-full max-w-md bg-white shadow-2xl p-7 overflow-y-auto">
        <button onClick={onClose} className="absolute top-5 right-5 text-[#786F66] hover:text-[#2B2523] text-xl">×</button>
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${isCompliant ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
          {isCompliant ? <CheckCircle2 className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
        </div>
        <p className="mt-5 text-xs font-extrabold text-[#786F66] uppercase tracking-wider">Bidder evidence</p>
        <h2 className="mt-1 text-xl font-extrabold text-[#2B2523]">{requirement.name}</h2>
        <p className="mt-1 text-sm font-bold text-[#B3432E]">{bidder.bidder_name}</p>

        <div className={`mt-6 rounded-xl border p-4 ${isCompliant ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'}`}>
          <p className={`font-extrabold ${isCompliant ? 'text-emerald-800' : 'text-rose-800'}`}>{detail.label}</p>
          <p className="mt-1 text-sm text-[#574E46] leading-relaxed">{detail.description}</p>
        </div>

        <div className="mt-6 space-y-4 text-sm">
          <div className="border-b border-[#E5E0DA] pb-4"><p className="text-xs font-bold text-[#786F66] uppercase tracking-wider">Tender source</p><p className="mt-1 font-bold text-[#2B2523]">Clause {requirement.source.clause}, page {requirement.source.page}</p></div>
          <div className="border-b border-[#E5E0DA] pb-4"><p className="text-xs font-bold text-[#786F66] uppercase tracking-wider">Evidence reason</p><p className="mt-1 text-[#574E46] leading-relaxed">{evidence ? evidence.evidence_text : detail.evidence}</p></div>
          <div className="flex gap-3 items-start"><FileText className="w-5 h-5 text-[#B3432E] mt-0.5 shrink-0" /><div><p className="font-bold text-[#2B2523]">{evidence ? evidence.document_title : 'No matching supporting document'}</p><p className="text-xs text-[#786F66] mt-0.5">{evidence ? `${evidence.source_file ?? bidder.source_file} · Pages ${evidence.page_start}–${evidence.page_end}` : 'No evidence linked to this requirement'}</p></div></div>
        </div>
      </aside>
    </div>
  );
}
