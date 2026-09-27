import { useEffect, useRef, useState } from "react";
import * as pdfjs from "pdfjs-dist";
import { api } from "@/lib/api";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

export default function PdfViewer(props) {
  // Switching sources must not render a page against the previous destroyed worker.
  return <PdfDocumentViewer key={`${props.url}:${props.initialPage || 1}`} {...props} />;
}

function PdfDocumentViewer({ url, initialPage = 1, title = "Original PDF", sourceLocator, evidenceText = "" }) {
  const canvasRef = useRef(null);
  const scrollRef = useRef(null);
  const [document, setDocument] = useState(null);
  const [page, setPage] = useState(initialPage || 1);
  const [error, setError] = useState("");
  const [source, setSource] = useState(null);
  const [zoom, setZoom] = useState(100);
  const [renderedPage, setRenderedPage] = useState(null);

  useEffect(() => {
    const box = source?.bounding_boxes?.[0];
    if (box && renderedPage === page && source.page_number === page && scrollRef.current && canvasRef.current) {
      scrollRef.current.scrollTop = Math.max(0, box.y0 * canvasRef.current.clientHeight - 100);
    }
  }, [source, renderedPage, page, zoom]);

  useEffect(() => {
    let active = true;
    setSource(null);
    if (sourceLocator) api.source(sourceLocator).then(value => { if (active) { setSource(value); if (value.page_number) setPage(value.page_number); } }).catch(() => { if (active) setSource({ message: "Exact highlight unavailable", bounding_boxes: [] }); });
    return () => { active = false; };
  }, [sourceLocator]);

  useEffect(() => {
    if (!url) return undefined;
    let active = true;
    const task = pdfjs.getDocument({ url, withCredentials: true });
    task.promise.then((loaded) => {
      if (!active) return;
      setDocument(loaded);
      setPage(Math.min(Math.max(initialPage || 1, 1), loaded.numPages));
      setError("");
    }).catch((reason) => active && setError(`Could not display PDF: ${reason.message}`));
    return () => { active = false; task.destroy(); };
  }, [url, initialPage]);

  useEffect(() => {
    if (!document || !canvasRef.current) return undefined;
    let cancelled = false;
    let renderTask;
    setRenderedPage(null);
    document.getPage(page).then((pdfPage) => {
      if (cancelled) return;
      const viewport = pdfPage.getViewport({ scale: 1.35 });
      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      renderTask = pdfPage.render({ canvasContext: context, viewport });
      return renderTask.promise.then(() => { if (!cancelled) setRenderedPage(page); });
    }).catch((reason) => {
      if (!cancelled && reason?.name !== "RenderingCancelledException") setError(`Could not render page: ${reason.message}`);
    });
    return () => { cancelled = true; renderTask?.cancel(); };
  }, [document, page]);

  if (!url) return <div className="p-8 text-center text-sm text-gray-500">No original PDF is linked.</div>;
  return <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
    <div className="flex flex-wrap items-center gap-2 border-b bg-white px-3 py-2 text-xs">
      <span className="mr-auto truncate font-semibold text-gray-700">{source?.source_filename || title}</span>
      <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="rounded border px-2 py-1 disabled:opacity-40">Previous</button>
      <span>Page {page} of {document?.numPages || "—"}</span>
      <button type="button" disabled={!document || page >= document.numPages} onClick={() => setPage((value) => value + 1)} className="rounded border px-2 py-1 disabled:opacity-40">Next</button>
      <label>Zoom <select aria-label="PDF zoom" value={zoom} onChange={event => setZoom(Number(event.target.value))}>{[75,100,125,150,200].map(value => <option key={value} value={value}>{value}%</option>)}</select></label>
      <a href={`${url}#page=${page}`} target="_blank" rel="noreferrer" className="font-bold text-[#B3432E]">Open directly</a>
    </div>
    {error&&<div className="bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div ref={scrollRef} className="max-h-[60vh] overflow-auto p-3"><div className="relative mx-auto" style={{ width: `${zoom}%` }}><canvas ref={canvasRef} aria-label={`${title}, page ${page}`} className="block h-auto w-full bg-white shadow" />{renderedPage === page && page === source?.page_number && source?.bounding_boxes?.slice(0,1).map((box,index) => { const lineHeight=Math.max(box.y1-box.y0,0.016); const top=Math.max(0,box.y0-(lineHeight*0.12)); return <div key={index} data-testid="evidence-highlight" aria-label="Evidence line highlight" className="pointer-events-none absolute rounded-[2px] bg-yellow-300/55 mix-blend-multiply" style={{ left: "4%", top: `${top*100}%`, width: "92%", height: `${lineHeight*1.24*100}%` }} />; })}</div></div>
    {(sourceLocator || evidenceText) && <aside className="border-t bg-white p-3 text-sm"><p className="font-semibold">Evidence extracted from this page {source?.page_number || initialPage}</p><p className="mt-1 whitespace-pre-wrap text-gray-700">{source?.evidence_text || evidenceText || "No extracted source text is available."}</p><p role="status" className="mt-2 text-xs text-gray-600">{source?.message || (sourceLocator ? "Locating evidence…" : "Exact highlight unavailable")}{source?.bounding_boxes?.length > 0 && page !== source.page_number ? ` · Navigate to page ${source.page_number} to see highlight` : ""}</p></aside>}
  </div>;
}

export function PdfModal({ url, page = 1, title, onClose, sourceLocator, evidenceText, details }) {
  if (!url) return null;
  return <div role="dialog" aria-modal="true" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <div className="max-h-[95vh] w-full max-w-5xl overflow-auto rounded-xl bg-white p-4">
      <div className="mb-3 flex items-center justify-between"><div><h2 className="font-extrabold">{title}</h2><p className="text-xs text-gray-500">Original uploaded file · starting at page {page}</p></div><button type="button" onClick={onClose} className="rounded border px-3 py-1.5 text-sm font-bold">Close</button></div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(200px,1fr)]"><PdfViewer url={url} initialPage={page} title={title} sourceLocator={sourceLocator} evidenceText={evidenceText} /><aside className="border bg-gray-50 p-4 text-sm"><h3 className="font-bold">Evidence Details</h3>{details && Object.entries(details).map(([label,value]) => <div key={label} className="mt-3"><p className="text-xs text-gray-500">{label}</p><p className="whitespace-pre-wrap">{value ?? "—"}</p></div>)}<p className="mt-4 text-xs text-gray-500">Original PDF is unchanged. Highlights appear only in this viewer.</p></aside></div>
    </div>
  </div>;
}
