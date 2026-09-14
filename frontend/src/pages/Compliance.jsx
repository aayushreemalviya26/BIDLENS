import { useEffect, useMemo, useState } from "react";
import { EvidenceDetail } from "../components/EvidenceDetail.jsx";
import { api } from "../lib/api.js";

const STATUS_META = {
  COMPLIANT: { label: "Compliant", dot: "bg-emerald-500", text: "text-emerald-700", pill: "bg-emerald-50" },
  NON_COMPLIANT: { label: "Non-Compliant", dot: "bg-red-500", text: "text-red-700", pill: "bg-red-50" },
  NEEDS_REVIEW: { label: "Review Required", dot: "bg-amber-500", text: "text-amber-700", pill: "bg-amber-50" },
  NOT_APPLICABLE: { label: "Not Applicable", dot: "bg-gray-400", text: "text-gray-600", pill: "bg-gray-100" },
  NOT_EVALUATED: { label: "Not Evaluated", dot: "bg-sky-400", text: "text-sky-700", pill: "bg-sky-50" },
};

function StatusPill({ status, onClick }) {
  const meta = STATUS_META[status] || STATUS_META.NOT_EVALUATED;
  return <button type="button" onClick={onClick} disabled={!onClick} className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-semibold ${meta.pill} ${meta.text}`}><span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />{meta.label}</button>;
}

function pageLabel(start, end) {
  if (!start) return "Page —";
  return end && end !== start ? `Pages ${start}–${end}` : `Page ${start}`;
}

function toDetail(payload) {
  const evidence = payload.evidence || [];
  const first = evidence[0] || {};
  const req = payload.requirement;
  const registry = payload.registry_source;
  const evidenceSummary = evidence.length ? evidence.map((item) => `${item.field || "Evidence"}: ${item.value || "—"}`).join("; ") : "Not found";
  return {
    complianceId: payload.compliance_id, tenderId: payload.tender_id,
    requirementName: req.name, status: payload.effective_status, machineStatus: payload.machine_status,
    bidderName: payload.bidder.bidder_name, category: req.category,
    documentId: first.document_id || null, clauseRef: req.source?.clause || "—",
    clausePage: req.source?.page || "—", requirementText: req.description,
    documentTitle: first.document_title || first.document_category || "Submitted Evidence",
    extractedValue: evidenceSummary,
    extractedSourceLabel: first.source_filename || first.document_id || payload.bidder.source_file || "Evidence document",
    extractedSourcePage: first.source_page || first.page || "—", pageLabel: pageLabel(first.page_start || first.source_page || first.page, first.page_end || first.source_page || first.page), appliedRule: `${payload.rule}: ${payload.reason}`,
    systemFinding: registry ? `${payload.explanation} Registry ${registry.source}: ${registry.status}${registry.discrepancies?.length ? ` (${registry.discrepancies.join("; ")})` : ""}.` : payload.explanation,
    registry: registry ? {
      source: registry.source,
      submittedValue: registry.identifier,
      registryValue: registry.record,
      status: registry.status,
      matched: registry.matched,
      discrepancies: registry.discrepancies || [],
    } : null,
    identityMasking: payload.bidder.identity_masking,
    officerDecision: payload.officer_decision,
    tenderClause: { page: req.source?.page || 1, heading: req.name, url: payload.tender_document_url },
    bidderDocument: { page: first.page_start || first.source_page || first.page || 1, heading: first.source_filename || first.document_id || "Bidder evidence", url: first.source_url },
  };
}

export default function Compliance({ selectedTenderId: initialTenderId = null }) {
  const [tenders, setTenders] = useState([]);
  const [selectedTenderId, setSelectedTenderId] = useState(initialTenderId);
  const [matrix, setMatrix] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState("matrix");
  const [completeness, setCompleteness] = useState(null);

  useEffect(() => {
    api.listTenders().then((items) => { setTenders(items); setSelectedTenderId((id) => id || initialTenderId || items[0]?.id || null); })
      .catch((err) => setError(err.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { if (initialTenderId) setSelectedTenderId(initialTenderId); }, [initialTenderId]);

  const refreshMatrix = async (tenderId = selectedTenderId) => {
    if (!tenderId) return;
    try { setMatrix(await api.complianceMatrix(tenderId)); setError(""); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (!selectedTenderId) return;
    api.complianceMatrix(selectedTenderId)
      .then((payload) => { setMatrix(payload); setError(""); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedTenderId]);

  const runEvaluation = async () => { setBusy(true); setError(""); try { await api.evaluate(selectedTenderId); await refreshMatrix(); setCompleteness(await api.completeness(selectedTenderId)); } catch(err){setError(err.message);} finally{setBusy(false);} };
  const openCompleteness = async () => { setTab("completeness"); try { setCompleteness(await api.completeness(selectedTenderId)); } catch(err){setError(err.message);} };

  const cells = useMemo(() => {
    const map = new Map();
    (matrix?.bidders || []).forEach((bidder) => (bidder.cells || []).forEach((cell) => map.set(`${bidder.bidder_id}_${cell.requirement_id}`, cell)));
    return map;
  }, [matrix]);

  const openEvidence = async (cell) => {
    if (!cell?.compliance_id) return;
    try { setDetail(toDetail(await api.complianceEvidence(cell.compliance_id))); }
    catch (err) { setError(err.message); }
  };

  const handleDecision = async (action, meta) => {
    if (!detail?.complianceId) return;
    try {
      if (action === "ACCEPT_EVIDENCE") await api.accept(detail.complianceId, meta.remarks);
      else if (action === "REVIEW_EVIDENCE") await api.clarification(detail.complianceId, meta.remarks);
      else await api.override(detail.complianceId, meta.nextStatus, meta.remarks);
      setDetail(toDetail(await api.complianceEvidence(detail.complianceId)));
      await refreshMatrix();
    } catch (err) { setError(err.message); }
  };

  if (detail) return <EvidenceDetail key={`${detail.complianceId}-${detail.status}-${detail.officerDecision?.verified_at || "machine"}`} detail={detail} onBack={() => setDetail(null)} onDecision={handleDecision} />;
  if (loading && !matrix) return <div className="p-8 text-gray-500">Loading compliance data…</div>;
  if (error && !matrix) return <div className="p-8 text-red-700">Backend unavailable: {error}</div>;
  if (!matrix) return <div className="p-8 text-gray-500">No tenders available.</div>;

  const requirements = matrix.requirements || [];
  const bidders = matrix.bidders || [];
  return <div className="min-h-screen bg-[#fcf8f6] p-6">
    {error && <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div className="mb-4 flex items-center justify-between"><div className="text-sm text-gray-500">Tenders <span className="mx-2">›</span><span className="font-medium text-gray-700">{matrix.external_bid_id || matrix.id}</span></div><select value={selectedTenderId || ""} onChange={(event) => { setSelectedTenderId(Number(event.target.value)); setDetail(null); }} className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm">{tenders.map((tender) => <option key={tender.id} value={tender.id}>{tender.external_bid_id || tender.id} — {tender.title}</option>)}</select></div>
    <div className="mb-5 flex items-start justify-between"><div><div className="flex items-center gap-3"><h1 className="text-2xl font-bold text-gray-900">{matrix.external_bid_id || matrix.id}</h1><span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">{matrix.status}</span></div><p className="mt-2 font-semibold text-gray-800">{matrix.title}</p><p className="mt-1 text-sm text-gray-500">{matrix.department} <span className="mx-2">|</span>{bidders.length} Bids Received</p></div><div className="flex gap-2">{matrix.documentUrl && <a href={api.absoluteUrl(`${matrix.documentUrl}#page=1`)} target="_blank" rel="noreferrer" className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 shadow-sm">View Tender Document</a>}<button onClick={runEvaluation} disabled={!bidders.length||busy} className="rounded-lg bg-[#B3432E] px-4 py-2.5 text-sm font-bold text-white disabled:opacity-40">{busy?"Evaluating…":"Run Compliance"}</button></div></div>
    <div className="mb-4 flex gap-2"><button onClick={()=>setTab("matrix")} className={`rounded-lg px-4 py-2 text-sm font-bold ${tab==="matrix"?"bg-[#2B2523] text-white":"border bg-white"}`}>Compliance Matrix</button><button onClick={openCompleteness} className={`rounded-lg px-4 py-2 text-sm font-bold ${tab==="completeness"?"bg-[#2B2523] text-white":"border bg-white"}`}>Document Completeness</button></div>
    {tab==="matrix"&&<div className="rounded-2xl border border-gray-200 bg-white shadow-sm"><div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 p-5"><div><h2 className="text-lg font-bold text-gray-900">Compliance Matrix</h2><p className="text-sm text-gray-500">Backend-evaluated comparison against approved requirements.</p></div><div className="flex flex-wrap gap-3 text-xs">{Object.entries(STATUS_META).map(([key, meta]) => <span key={key} className="flex items-center gap-1"><span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />{meta.label}</span>)}</div></div>
      <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50"><tr><th className="px-5 py-4 text-left text-xs font-semibold uppercase text-gray-500">Requirement</th>{bidders.map((bidder) => <th key={bidder.bidder_id} className="px-5 py-4 text-left text-xs font-semibold uppercase text-gray-500"><div>{bidder.bidder_name}</div><div className="mt-1 normal-case text-gray-400">{bidder.compliance_score ?? 0}% · {bidder.risk_level || "—"} risk</div></th>)}</tr></thead><tbody>{requirements.map((requirement) => <tr key={requirement.requirement_id} className="border-t border-gray-100 hover:bg-gray-50"><td className="px-5 py-4"><div className="font-semibold text-gray-800">{requirement.name}</div><div className="mt-1 text-xs text-gray-400">{requirement.category}</div></td>{bidders.map((bidder) => { const cell = cells.get(`${bidder.bidder_id}_${requirement.requirement_id}`); return <td key={bidder.bidder_id} className="px-5 py-4"><StatusPill status={cell?.status || "NOT_EVALUATED"} />{cell?.compliance_id&&<button type="button" onClick={()=>openEvidence(cell)} className="ml-2 text-xs font-bold text-[#B3432E] hover:underline">Verify Document</button>}{cell?.reason && <p className="mt-1 max-w-xs text-xs text-gray-400">{cell.reason}</p>}</td>; })}</tr>)}</tbody></table></div>
    </div>}
    {tab==="completeness"&&<CompletenessView rows={completeness?.rows||[]} requirements={requirements} bidders={bidders}/>}
    <div className="mt-5 grid gap-4 lg:grid-cols-3">{bidders.map(b=><div key={b.id} className="rounded-2xl border bg-white p-4"><h3 className="font-extrabold">{b.bidder_name}</h3><p className="mb-3 text-sm"><b>Overall:</b> {b.overall_status} · {b.compliance_score??0}%</p><div className="space-y-2">{(b.registry_verifications||[]).map((v,i)=><details key={`${v.source}-${i}`} className="rounded-lg bg-[#FAF8F5] p-2 text-xs"><summary className="cursor-pointer font-bold">{v.source}: {v.status} · {v.matched?"MATCH":"MISMATCH"}</summary><p className="mt-2"><b>Submitted:</b> {v.identifier}</p><p><b>Registry:</b> {JSON.stringify(v.record)}</p><p><b>Discrepancies:</b> {v.discrepancies?.join("; ")||"None"}</p></details>)}</div></div>)}</div>
  </div>;
}

function CompletenessView({rows,requirements,bidders}) { const map=new Map(rows.map(r=>[`${r.bidder_id}_${r.requirement_id}`,r])); return <div className="overflow-x-auto rounded-2xl border bg-white"><table className="w-full text-sm"><thead className="bg-gray-50"><tr><th className="p-4 text-left">Approved requirement</th>{bidders.map(b=><th key={b.bidder_id} className="p-4 text-left">{b.bidder_name}</th>)}</tr></thead><tbody>{requirements.filter(r=>r.approved).map(r=><tr key={r.requirement_id} className="border-t"><td className="p-4"><b>{r.name}</b><div className="text-xs text-gray-500">{r.required_document_type||r.category}</div></td>{bidders.map(b=>{const cell=map.get(`${b.bidder_id}_${r.requirement_id}`);return <td key={b.bidder_id} className="p-4"><span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-bold">{cell?.status||"NOT_PROCESSED"}</span>{cell?.sources?.length?cell.sources.map(source=><a key={source.document_id} href={source.file_url?api.absoluteUrl(`${source.file_url}#page=${source.page_start||1}`):undefined} target="_blank" rel="noreferrer" className="mt-2 block text-left text-xs text-[#5C554D] hover:text-[#B3432E]"><b>{source.document_title}</b><br/>{source.original_file_name} · {pageLabel(source.page_start,source.page_end)}</a>):<div className="mt-1 text-xs text-gray-500">No classified file</div>}</td>})}</tr>)}</tbody></table></div>; }
