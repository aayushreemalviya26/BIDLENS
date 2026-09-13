import { useState } from "react";


const STATUS_META = {
    COMPLIANT: { label: "Compliant", pill: "bg-emerald-50", text: "text-emerald-700" },
    NON_COMPLIANT: { label: "Non-Compliant", pill: "bg-red-50", text: "text-red-700" },
    NEEDS_REVIEW: { label: "Review Required", pill: "bg-amber-50", text: "text-amber-700" },
};

// Maps a button action to the status the evidence should move to
const DECISION_STATUS = {
    ACCEPT_EVIDENCE: "COMPLIANT",
    REJECT_EVIDENCE: "NON_COMPLIANT",
    REVIEW_EVIDENCE: "NEEDS_REVIEW",
};

const DECISION_LABEL = {
    ACCEPT_EVIDENCE: "Accepted",
    REJECT_EVIDENCE: "Rejected",
    REVIEW_EVIDENCE: "Marked for review",
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
    return (
        <div className="overflow-hidden rounded-xl border border-gray-200">
            {/* TOOLBAR */}
            <div className="flex items-center gap-3 border-b border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-500">
                <span>☰</span>
                <span>
                    {doc.page} / {doc.totalPages}
                </span>
                <span className="mx-1 text-gray-300">|</span>
                <span>←</span>
                <span>100%</span>
                <span>→</span>
                <span className="ml-auto flex items-center gap-3">
                    <span>⤢</span>
                    <span>⟳</span>
                    <span>⋮</span>
                </span>
            </div>

            {/* PAGE */}
            <div className="bg-gray-900 p-8">
                <div className="mx-auto max-w-sm rounded-md bg-white p-6 text-sm leading-6 text-gray-800 shadow-lg">
                    <p className="mb-3 font-bold">{doc.heading}</p>
                    <p>
                        {doc.body}
                        <span className="bg-amber-300 px-0.5 font-semibold">{doc.highlight}</span>
                        {doc.bodyEnd}
                    </p>
                </div>
            </div>
        </div>
    );
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

    const handleClick = (action) => {
        onDecide(action, remarks.trim());
        setLastAction(action);
    };

    return (
        <div className="rounded-xl bg-gray-50 p-4">
            <p className="mb-2 text-sm font-semibold text-gray-900">Officer Decision</p>

            <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add a remark (optional) — included in the audit trail"
                rows={2}
                className="mb-3 w-full rounded-lg border border-gray-200 bg-white p-2 text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-300"
            />

            <div className="flex flex-wrap gap-2">
                <button
                    type="button"
                    onClick={() => handleClick("ACCEPT_EVIDENCE")}
                    disabled={currentStatus === "COMPLIANT"}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Accept
                </button>
                <button
                    type="button"
                    onClick={() => handleClick("REJECT_EVIDENCE")}
                    disabled={currentStatus === "NON_COMPLIANT"}
                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Reject
                </button>
                <button
                    type="button"
                    onClick={() => handleClick("REVIEW_EVIDENCE")}
                    disabled={currentStatus === "NEEDS_REVIEW"}
                    className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    Mark for Review
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

    const handleDecide = (action, remarks) => {
        const nextStatus = DECISION_STATUS[action];
        setCurrentStatus(nextStatus);

        const remarkSuffix = remarks ? ` — remark: "${remarks}"` : "";
        const description = `${DECISION_LABEL[action]} evidence for "${detail.requirementName}" (${detail.bidderName}) on tender ${detail.tenderId}${remarkSuffix}`;

        onDecision(action, {
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
                    </InfoBlock>

                    <InfoBlock
                        label="Bidder's Extracted Value"
                        corner={`${detail.extractedSourceLabel}, Page ${detail.extractedSourcePage}`}
                    >
                        <p className="text-lg font-bold text-gray-900">{detail.extractedValue}</p>
                    </InfoBlock>

                    <InfoBlock label="Applied Rule">
                        <p className="text-sm font-semibold text-gray-800">{detail.appliedRule}</p>
                    </InfoBlock>

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

// --- Demo/fake data matching the reference screenshot ---
export const demoEvidenceDetail = {
    tenderId: "GEM/2024/001",
    requirementName: "GST Registration",
    status: "NON_COMPLIANT",
    bidderName: "Bharat Supplies Ltd",
    category: "GST",
    documentId: "DOC_001",
    clauseRef: "8.2",
    clausePage: 14,
    requirementText: "Bidders must submit a valid GST registration certificate.",
    extractedValue: "Not found",
    extractedSourceLabel: "bidder.pdf",
    extractedSourcePage: 1,
    appliedRule: 'Required category "GST" not found → Not Satisfied',
    systemFinding: "No document was classified as GST registration for this bidder.",
    tenderClause: {
        page: 14,
        totalPages: 32,
        heading: "8.2  Statutory Registrations",
        body: "Bidders must submit a valid ",
        highlight: "GST registration certificate",
        bodyEnd: " as part of the eligibility documents.",
    },
    bidderDocument: {
        page: 1,
        totalPages: 12,
        heading: "bidder.pdf",
        body: "No document was classified into this category for this bidder.",
        highlight: "",
        bodyEnd: "",
    },
};

export default function EvidenceDetailDemo() {
    return (
        <EvidenceDetail
            detail={demoEvidenceDetail}
            onBack={() => alert("Back to matrix")}
            onDecision={(action, meta) => console.log("Officer decision:", action, meta)}
        />
    );
}

export { EvidenceDetail };