import { useMemo, useState } from "react";
import complianceMock from "../data/complianceMock.js";
import { EvidenceDetail } from "../components/EvidenceDetail.jsx";
import { createAuditEntry } from '@/utils/auditLog';

/**
 * Expected complianceMock shape — matches the new backend contract:
 *
 * {
 *   tenders: [
 *     {
 *       id: "GEM/2024/001",
 *       status: "Active",
 *       title: "...",
 *       department: "...",
 *       documentUrl: null,
 *       requirements: [
 *         { requirement_id, name, category, description, source: { clause, page } },
 *         ...
 *       ],
 *       bidders: [
 *         {
 *           bidder_id: "B01",
 *           bidder_name: "ABC Safety Solutions Pvt. Ltd.",
 *           source_file: "bidder.pdf",
 *           documents: [
 *             {
 *               document_id: "DOC_001",
 *               category: "GST",
 *               page_start: 1,
 *               page_end: 3,
 *               pages: [1, 2, 3],
 *               confidence: 0.97,
 *               status: "COMPLIANT",   // <-- backend-computed verdict, once available
 *               reason: null,          // <-- optional backend explanation
 *             },
 *             ...
 *           ],
 *         },
 *         ...
 *       ],
 *     },
 *     ...
 *   ],
 * }
 *
 * `requirement.category` is the join key against `document.category` for a given bidder.
 */



const STATUS_META = {
    COMPLIANT: {
        label: "Compliant",
        dot: "bg-emerald-500",
        text: "text-emerald-700",
        pill: "bg-emerald-50",
    },
    NON_COMPLIANT: {
        label: "Non-Compliant",
        dot: "bg-red-500",
        text: "text-red-700",
        pill: "bg-red-50",
    },
    NEEDS_REVIEW: {
        label: "Review Required",
        dot: "bg-amber-500",
        text: "text-amber-700",
        pill: "bg-amber-50",
    },
};

const OVERALL_META = {
    PASS: "bg-emerald-100 text-emerald-700",
    FAIL: "bg-red-100 text-red-700",
    REVIEW: "bg-amber-100 text-amber-700",
};

// Fake placeholder pages shown until a real tender document is uploaded.
const fakeTenderDocumentPages = [
    {
        heading: "1. Scope of Supply",
        body: "This tender covers the supply of goods/services described in the tender title, in line with the applicable procurement policy.",
    },
    {
        heading: "8. Compliance Requirements",
        body: "Bidders must satisfy all listed policy, legal, financial, and technical requirements to be considered compliant.",
    },
    {
        heading: "12. Eligibility Criteria",
        body: "Bidders must hold valid company registration, tax clearance, and any category-specific certifications required for this tender.",
    },
];

// TEMPORARY fallback until the backend always sends `document.status`.
// Remove this once every document object is guaranteed to include a verdict.
const CONFIDENCE_THRESHOLDS = { compliant: 0.9, review: 0.7 };

function deriveStatusFromConfidence(confidence) {
    if (confidence >= CONFIDENCE_THRESHOLDS.compliant) return "COMPLIANT";
    if (confidence >= CONFIDENCE_THRESHOLDS.review) return "NEEDS_REVIEW";
    return "NON_COMPLIANT";
}

function getDocumentStatus(document) {
    if (!document) return "NON_COMPLIANT"; // required category not found for this bidder
    if (document.status) return document.status; // trust backend once it's sending this
    return deriveStatusFromConfidence(document.confidence ?? 0);
}

function statusMeta(status) {
    return STATUS_META[status] ?? STATUS_META.NEEDS_REVIEW;
}

function overrideKey(tenderId, bidderId, category) {
    return `${tenderId}_${bidderId}_${category}`;
}

function StatusPill({ status, onClick }) {
    const meta = statusMeta(status);
    return (
        <button
            type="button"
            onClick={onClick}
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-semibold transition hover:brightness-95 ${meta.pill} ${meta.text}`}
        >
            <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
            {meta.label}
        </button>
    );
}

function Compliance({ onLogActivity = () => { } }) {
    const tenders = complianceMock.tenders ?? [];

    const [selectedTenderId, setSelectedTenderId] = useState(tenders[0]?.id ?? null);
    const [selectedCell, setSelectedCell] = useState(null); // { requirement_id, bidder_id }
    const [showTenderDoc, setShowTenderDoc] = useState(false);
    const [docPageIndex, setDocPageIndex] = useState(0);

    // Officer decisions, keyed by `${tenderId}_${bidderId}_${category}` -> { status, remarks }.
    // These win over the backend/confidence-derived status until a refetch/PATCH replaces them.
    const [statusOverrides, setStatusOverrides] = useState({});

    const tender = tenders.find((t) => t.id === selectedTenderId) ?? tenders[0];

    const { bidders = [], requirements = [] } = tender ?? {};

    // documentsByKey: `${bidder_id}_${category}` -> document
    // (assumes at most one document per category per bidder; first match wins otherwise)
    const documentsByKey = useMemo(() => {
        const map = new Map();
        bidders.forEach((b) => {
            (b.documents ?? []).forEach((doc) => {
                const key = `${b.bidder_id}_${doc.category}`;
                if (!map.has(key)) map.set(key, doc);
            });
        });
        return map;
    }, [bidders]);

    const bidderById = useMemo(() => {
        const map = new Map();
        bidders.forEach((b) => map.set(b.bidder_id, b));
        return map;
    }, [bidders]);

    // Resolves the status a cell should actually show: officer override first,
    // then backend/confidence-derived status.
    function getEffectiveStatus(bidderId, category, document) {
        const key = overrideKey(tender.id, bidderId, category);
        return statusOverrides[key]?.status ?? getDocumentStatus(document);
    }

    function overallStatusForBidder(bidderId) {
        const statuses = requirements.map((req) =>
            getEffectiveStatus(bidderId, req.category, documentsByKey.get(`${bidderId}_${req.category}`))
        );
        if (statuses.some((s) => s === "NON_COMPLIANT")) return "FAIL";
        if (statuses.some((s) => s === "NEEDS_REVIEW")) return "REVIEW";
        return "PASS";
    }

    const selectedDetail = useMemo(() => {
        if (!selectedCell || !tender) return null;
        const requirement = requirements.find(
            (r) => r.requirement_id === selectedCell.requirement_id
        );
        if (!requirement) return null;
        const bidder = bidderById.get(selectedCell.bidder_id);
        const document = documentsByKey.get(
            `${selectedCell.bidder_id}_${requirement.category}`
        );
        const status = getEffectiveStatus(selectedCell.bidder_id, requirement.category, document);
        const override = statusOverrides[
            overrideKey(tender.id, selectedCell.bidder_id, requirement.category)
        ];
        return { requirement, bidder, document, status, override };
    }, [selectedCell, requirements, bidderById, documentsByKey, statusOverrides, tender]);

    // Maps requirement/bidder/document data into the EvidenceDetail shape.
    // tenderClause/bidderDocument body text is fake placeholder content
    // until the backend renders real clause + document pages.
    const evidenceDetailData = useMemo(() => {
        if (!selectedDetail?.requirement || !selectedCell || !tender) return null;
        const { requirement, bidder, document, status, override } = selectedDetail;

        const pageRange = document
            ? document.page_start === document.page_end
                ? `Page ${document.page_start}`
                : `Pages ${document.page_start}–${document.page_end}`
            : null;

        const baseRule = !document
            ? `Required category "${requirement.category}" not found → Not Satisfied`
            : status === "COMPLIANT"
                ? `${document.category} classified with ${(document.confidence * 100).toFixed(0)}% confidence → Satisfied`
                : status === "NEEDS_REVIEW"
                    ? `${document.category} classified with ${(document.confidence * 100).toFixed(0)}% confidence → Needs Manual Review`
                    : `${document.category} does not satisfy requirement → Not Satisfied`;

        const appliedRule = override
            ? `Officer override → ${statusMeta(status).label}`
            : baseRule;

        const baseFinding = document?.reason ??
            (document
                ? `Classified as "${document.category}" (document ${document.document_id}) with ${(document.confidence * 100).toFixed(0)}% confidence.`
                : "No matching document found for this requirement.");

        const systemFinding = override?.remarks
            ? `${baseFinding} Officer remark: "${override.remarks}"`
            : baseFinding;

        return {
            tenderId: tender.id,
            requirementName: requirement.name,
            status,
            bidderName: bidder?.bidder_name ?? selectedCell.bidder_id,
            category: requirement.category,
            documentId: document?.document_id ?? null,
            clauseRef: requirement.source?.clause ?? "—",
            clausePage: requirement.source?.page ?? document?.page_start ?? "—",
            requirementText:
                requirement.description ?? `Requirement: ${requirement.name}.`,
            extractedValue: pageRange ?? "Not found",
            extractedSourceLabel: bidder?.source_file ?? document?.document_id ?? "Evidence document",
            extractedSourcePage: document?.page_start ?? "—",
            appliedRule,
            systemFinding,
            tenderClause: {
                page: requirement.source?.page ?? document?.page_start ?? 1,
                totalPages: 32,
                heading: requirement.name,
                body: "Full clause text will be rendered here once the backend provides it. Requirement: ",
                highlight: requirement.category ?? "",
                bodyEnd: ".",
            },
            bidderDocument: {
                page: document?.page_start ?? 1,
                totalPages: 12,
                heading: bidder?.source_file ?? "Bidder document",
                body: document
                    ? `Full extracted text for "${document.category}" (${pageRange}) will be rendered here.`
                    : "No document was classified into this category for this bidder.",
                highlight: "",
                bodyEnd: "",
            },
        };
    }, [selectedDetail, selectedCell, tender]);

    // Officer decision from EvidenceDetail: records an override so the matrix
    // reflects it immediately. Swap/extend this to also fire a backend PATCH.
    const handleDecision = (action, meta) => {
        if (!selectedCell || !tender || !meta.category) return;
        const key = overrideKey(tender.id, selectedCell.bidder_id, meta.category);
        setStatusOverrides((prev) => ({
            ...prev,
            [key]: { status: meta.nextStatus, remarks: meta.remarks },
        }));

        onLogActivity(
            createAuditEntry(action, meta.description, {
                tenderId: meta.tenderId,
                requirementName: meta.requirementName,
                bidderName: meta.bidderName,
                category: meta.category,
                documentId: meta.documentId,
                remarks: meta.remarks,
            })
        );
    };

    if (evidenceDetailData) {
        return (
            <EvidenceDetail
                detail={evidenceDetailData}
                onBack={() => setSelectedCell(null)}
                onDecision={handleDecision}
            />
        );
    }

    if (!tender) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-[#fcf8f6] text-gray-500">
                No tenders available.
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#fcf8f6] p-6">
            {/* TENDER PICKER */}
            <div className="mb-4 flex items-center justify-between">
                <div className="text-sm text-gray-500">
                    Tenders
                    <span className="mx-2">›</span>
                    <span className="font-medium text-gray-700">{tender.id}</span>
                </div>

                <select
                    value={selectedTenderId}
                    onChange={(e) => {
                        setSelectedTenderId(e.target.value);
                        setSelectedCell(null);
                    }}
                    className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm outline-none focus:border-amber-500"
                >
                    {tenders.map((t) => (
                        <option key={t.id} value={t.id}>
                            {t.id} — {t.title}
                        </option>
                    ))}
                </select>
            </div>

            {/* TENDER HEADER */}
            <div className="mb-5 flex items-start justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-gray-900">{tender.id}</h1>
                        <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                            {tender.status}
                        </span>
                    </div>

                    <p className="mt-2 font-semibold text-gray-800">{tender.title}</p>

                    <p className="mt-1 text-sm text-gray-500">
                        {tender.department}
                        <span className="mx-2">|</span>
                        {bidders.length} Bids Received
                    </p>
                </div>

                <button
                    type="button"
                    onClick={() => {
                        if (tender.documentUrl) {
                            window.open(tender.documentUrl, "_blank", "noopener,noreferrer");
                        } else {
                            setDocPageIndex(0);
                            setShowTenderDoc(true);
                        }
                    }}
                    className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50"
                >
                    📄 View Tender Document
                </button>
            </div>

            {/* TOTAL BIDDERS */}
            <div className="mb-6 text-sm font-semibold text-gray-700">
                Total Bidders: <span className="text-amber-700">{bidders.length}</span>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex items-start gap-6">
                {/* MATRIX */}
                <div className="w-full rounded-2xl border border-gray-200 bg-white shadow-sm">
                    {/* MATRIX HEADER */}
                    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 p-5">
                        <div>
                            <h2 className="text-lg font-bold text-gray-900">Compliance Matrix</h2>
                            <p className="text-sm text-gray-500">
                                Comparison of all bidders against approved requirements.
                            </p>
                        </div>

                        {/* LEGEND */}
                        <div className="flex items-center gap-4 text-xs font-medium text-gray-600">
                            {Object.entries(STATUS_META).map(([key, meta]) => (
                                <span key={key} className="flex items-center gap-1.5">
                                    <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
                                    {meta.label}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* TABLE */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-5 py-4 text-left text-xs font-semibold uppercase text-gray-500">
                                        Requirement
                                    </th>
                                    {bidders.map((b) => (
                                        <th
                                            key={b.bidder_id}
                                            className="px-5 py-4 text-left text-xs font-semibold uppercase text-gray-500"
                                        >
                                            {b.bidder_name}
                                        </th>
                                    ))}
                                </tr>
                            </thead>

                            <tbody>
                                {requirements.map((req) => (
                                    <tr
                                        key={req.requirement_id}
                                        className="border-t border-gray-100 transition hover:bg-gray-50"
                                    >
                                        <td className="px-5 py-4 font-semibold text-gray-800">
                                            {req.name}
                                        </td>

                                        {bidders.map((b) => {
                                            const document = documentsByKey.get(
                                                `${b.bidder_id}_${req.category}`
                                            );
                                            const status = getEffectiveStatus(b.bidder_id, req.category, document);
                                            return (
                                                <td key={b.bidder_id} className="px-5 py-4">
                                                    <StatusPill
                                                        status={status}
                                                        onClick={() =>
                                                            setSelectedCell({
                                                                requirement_id: req.requirement_id,
                                                                bidder_id: b.bidder_id,
                                                            })
                                                        }
                                                    />
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* TENDER DOCUMENT MODAL — fake preview until a real file is uploaded */}
            {showTenderDoc && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
                    <div className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-xl">
                        {/* MODAL HEADER */}
                        <div className="flex items-center justify-between border-b border-gray-100 p-5">
                            <div>
                                <h2 className="text-lg font-bold text-gray-900">Tender Document</h2>
                                <p className="text-xs text-gray-500">
                                    {tender.id} · Preview only — upload the real RFP PDF to replace this
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setShowTenderDoc(false)}
                                className="text-xl text-gray-400 hover:text-gray-700"
                            >
                                ×
                            </button>
                        </div>

                        {/* TOOLBAR */}
                        <div className="flex items-center gap-3 border-b border-gray-100 bg-gray-50 px-4 py-2 text-xs text-gray-500">
                            <button
                                type="button"
                                disabled={docPageIndex === 0}
                                onClick={() => setDocPageIndex((i) => Math.max(0, i - 1))}
                                className="disabled:opacity-30"
                            >
                                ←
                            </button>
                            <span>
                                Page {docPageIndex + 1} / {fakeTenderDocumentPages.length}
                            </span>
                            <button
                                type="button"
                                disabled={docPageIndex === fakeTenderDocumentPages.length - 1}
                                onClick={() =>
                                    setDocPageIndex((i) =>
                                        Math.min(fakeTenderDocumentPages.length - 1, i + 1)
                                    )
                                }
                                className="disabled:opacity-30"
                            >
                                →
                            </button>
                            <span className="ml-auto">100%</span>
                        </div>

                        {/* PAGE CONTENT */}
                        <div className="flex-1 overflow-y-auto bg-gray-900 p-8">
                            <div className="mx-auto max-w-md rounded-md bg-white p-6 text-sm leading-6 text-gray-800 shadow-lg">
                                <p className="mb-3 font-bold">
                                    {fakeTenderDocumentPages[docPageIndex].heading}
                                </p>
                                <p>{fakeTenderDocumentPages[docPageIndex].body}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Compliance;