import { useState } from "react";
import { api } from "@/lib/api";
import PdfViewer from "@/components/PdfViewer";


const STATUS_META = {
    COMPLIANT: { label: "Compliant", pill: "bg-emerald-50", text: "text-emerald-700" },
    NON_COMPLIANT: { label: "Non-Compliant", pill: "bg-red-50", text: "text-red-700" },
    NEEDS_REVIEW: { label: "Review Required", pill: "bg-amber-50", text: "text-amber-700" },
    NOT_APPLICABLE: { label: "Not Applicable", pill: "bg-gray-100", text: "text-gray-600" },
    NOT_EVALUATED: { label: "Not Evaluated", pill: "bg-sky-50", text: "text-sky-700" },
};

// Maps a button action to the status the evidence should move to
const DECISION_STATUS = {
    ACCEPT_EVIDENCE: "COMPLIANT",
    REJECT_EVIDENCE: "NON_COMPLIANT",
    REVIEW_EVIDENCE: "NEEDS_REVIEW",
};

const DECISION_LABEL = {
    ACCEPT_EVIDENCE: "Accepted",
    REJECT_EVIDENCE: "Overridden",
    REVIEW_EVIDENCE: "Clarification requested",
};

function InfoBlock({ label, corner, children }) {
    return (
        <div className="rounded-xl bg-gray-50 p-4">
            <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-gray-900">{label}</p>
                {corner && <p className="text-xs text-gray-400">{corner}</p>}
            </div>
            {children}
        </div>
    );
}

function DocumentViewer({ doc }) {
    if (!doc) return null;
    const url = doc.url ? api.absoluteUrl(doc.url) : null;
    return <PdfViewer url={url} initialPage={doc.page || 1} title={doc.heading} />;
}

/**
 * Officer decision panel: Accept / Reject / Review buttons for a single
 * piece of evidence. Calls `onDecision(action, meta)` so the parent can
 * pipe it into the audit log (see auditLog.js / AuditTrailScreen.jsx) and,
 * ultimately, PATCH the relevant document's status on the backend.
 */
function OfficerDecisionPanel({ detail, currentStatus, onDecide }) {
    const [remarks, setRemarks] = useState("");
    const [lastAction, setLastAction] = useState(null);
    const [overrideStatus, setOverrideStatus] = useState("NON_COMPLIANT");
    const excluded = currentStatus === "NOT_APPLICABLE";

    const handleClick = async (action) => {
        await onDecide(action, remarks.trim(), overrideStatus);
        setLastAction(action);
    };

    return (
        <div className="rounded-xl bg-gray-50 p-4">
            <p className="mb-2 text-sm font-semibold text-gray-900">Officer Decision</p>

            <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add a reason or clarification message — included in the audit trail"
                rows={2}
                className="mb-3 w-full rounded-lg border border-gray-200 bg-white p-2 text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-300"
            />

            <div className="flex flex-wrap gap-2">
                <button
                    type="button"
                    onClick={() => handleClick("ACCEPT_EVIDENCE")}
                    disabled={excluded}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Accept
                </button>
                <button
                    type="button"
                    onClick={() => handleClick("REJECT_EVIDENCE")}
                    disabled={excluded || !remarks.trim()}
                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Override Status
                </button>
                <select aria-label="Override status" value={overrideStatus} onChange={(e)=>setOverrideStatus(e.target.value)} className="rounded-lg border bg-white px-2 text-sm">{["COMPLIANT","NON_COMPLIANT","NEEDS_REVIEW"].map(status=><option key={status}>{status}</option>)}</select>
                <button
                    type="button"
                    onClick={() => handleClick("REVIEW_EVIDENCE")}
                    disabled={excluded || currentStatus === "NEEDS_REVIEW"}
                    className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Request Clarification
                </button>
            </div>

            {lastAction && (
                <p className="mt-3 text-xs text-gray-500">
                    {DECISION_LABEL[lastAction]} · {detail.requirementName} for {detail.bidderName}, just now.
                </p>
            )}
        </div>
    );
}

function EvidenceDetail({ detail, onBack, onDecision = () => {} }) {
    const [activeDocTab, setActiveDocTab] = useState("clause"); // "clause" | "document"
    const [currentStatus, setCurrentStatus] = useState(detail.status);
    const meta = STATUS_META[currentStatus] ?? STATUS_META.NEEDS_REVIEW;

    const handleDecide = async (action, remarks, overrideStatus) => {
        const nextStatus = action === "REJECT_EVIDENCE" ? overrideStatus : action === "ACCEPT_EVIDENCE" ? detail.machineStatus : DECISION_STATUS[action];

        const remarkSuffix = remarks ? ` — remark: "${remarks}"` : "";
        const description = `${DECISION_LABEL[action]} evidence for "${detail.requirementName}" (${detail.bidderName}) on tender ${detail.tenderId}${remarkSuffix}`;

        await onDecision(action, {
            description,
            tenderId: detail.tenderId,
            requirementName: detail.requirementName,
            bidderName: detail.bidderName,
            // New: identifies exactly which backend document/category this
            // decision applies to, so the parent can PATCH it correctly.
            category: detail.category ?? null,
            documentId: detail.documentId ?? null,
            nextStatus,
            remarks,
        });
        setCurrentStatus(nextStatus);
    };

    return (
        <div className="min-h-screen bg-[#fcf8f6] p-6">
            {/* BREADCRUMB */}
            <div className="mb-4 text-sm text-gray-500">
                Tenders
                <span className="mx-2">›</span>
                {detail.tenderId}
                <span className="mx-2">›</span>
                Evaluation Matrix
            </div>

            {/* HEADER */}
            <div className="mb-1 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-bold text-gray-900">{detail.requirementName}</h1>
                    <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${meta.pill} ${meta.text}`}
                    >
                        {meta.label}
                    </span>
                </div>

                <button
                    type="button"
                    onClick={onBack}
                    className="flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-amber-700"
                >
                    ← Back to Matrix
                </button>
            </div>

            <p className="mb-6 text-sm text-gray-500">{detail.bidderName}</p>

            {/* MAIN GRID */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* LEFT: INFO CARDS */}
                <div className="space-y-4">
                    <InfoBlock
                        label="Tender Requirement"
                        corner={`Clause ${detail.clauseRef}, Page ${detail.clausePage}`}
                    >
                        <p className="text-sm text-gray-700">{detail.requirementText}</p>
                        {detail.tenderClause.url&&<a href={api.absoluteUrl(`${detail.tenderClause.url}#page=${detail.tenderClause.page}`)} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs font-bold text-[#B3432E]">Open Tender Source</a>}
                    </InfoBlock>

                    <InfoBlock
                        label={detail.documentTitle || "Submitted Evidence"}
                        corner={detail.pageLabel}
                    >
                        <p className="mb-1 text-xs text-gray-500">Original File: {detail.extractedSourceLabel}</p>
                        <p className="text-lg font-bold text-gray-900">{detail.extractedValue}</p>
                        {detail.bidderDocument.url&&<a href={api.absoluteUrl(`${detail.bidderDocument.url}#page=${detail.bidderDocument.page}`)} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs font-bold text-[#B3432E]">Open Original Document</a>}
                    </InfoBlock>

                    <InfoBlock label="Applied Rule">
                        <p className="text-sm font-semibold text-gray-800">{detail.appliedRule}</p>
                    </InfoBlock>

                    <InfoBlock label="Verdict State">
                        <p className="text-sm text-gray-700">Machine: <span className="font-semibold">{detail.machineStatus}</span></p>
                        <p className="mt-1 text-sm text-gray-700">Effective: <span className="font-semibold">{currentStatus}</span></p>
                        <p className="mt-1 text-xs text-gray-500">Bidder Identity Masking: {detail.identityMasking === "APPLIED" ? "Applied" : "Not Applied"}</p>
                    </InfoBlock>

                    {detail.officerDecision&&<InfoBlock label="Latest Officer Verification"><p className="text-sm text-gray-700">{detail.officerDecision.action} by {detail.officerDecision.verified_by}</p><p className="mt-1 text-xs text-gray-500">{detail.officerDecision.reason || "No comment"} · {new Date(detail.officerDecision.verified_at).toLocaleString()}</p></InfoBlock>}

                    {detail.registry && (
                        <InfoBlock label={`Registry Verification · ${detail.registry.source}`}>
                            <dl className="space-y-2 text-sm text-gray-700">
                                <div><dt className="font-semibold">Submitted identifier/value</dt><dd>{detail.registry.submittedValue || "—"}</dd></div>
                                <div><dt className="font-semibold">Registry value/status</dt><dd className="break-words">{JSON.stringify(detail.registry.registryValue)} · {detail.registry.status}</dd></div>
                                <div><dt className="font-semibold">Match</dt><dd>{detail.registry.matched ? "MATCH" : "MISMATCH"}</dd></div>
                                <div><dt className="font-semibold">Discrepancies</dt><dd>{detail.registry.discrepancies.length ? detail.registry.discrepancies.join("; ") : "None"}</dd></div>
                            </dl>
                        </InfoBlock>
                    )}

                    <InfoBlock label="System Finding">
                        <p className="text-sm text-gray-700">{detail.systemFinding}</p>
                    </InfoBlock>

                    <OfficerDecisionPanel
                        detail={detail}
                        currentStatus={currentStatus}
                        onDecide={handleDecide}
                    />
                </div>

                {/* RIGHT: DOCUMENT VIEWER */}
                <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                    <div className="mb-3 flex gap-6 border-b border-gray-100 pb-3">
                        <button
                            type="button"
                            onClick={() => setActiveDocTab("clause")}
                            className={`text-sm font-semibold ${activeDocTab === "clause"
                                ? "text-gray-900"
                                : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            Tender Clause (Page {detail.tenderClause.page})
                        </button>
                        <button
                            type="button"
                            onClick={() => setActiveDocTab("document")}
                            className={`text-sm font-semibold ${activeDocTab === "document"
                                ? "text-gray-900"
                                : "text-gray-400 hover:text-gray-600"
                                }`}
                        >
                            Bidder Document (Page {detail.bidderDocument.page})
                        </button>
                    </div>

                    <DocumentViewer
                        doc={activeDocTab === "clause" ? detail.tenderClause : detail.bidderDocument}
                    />
                </div>
            </div>
        </div>
    );
}

export { EvidenceDetail };
