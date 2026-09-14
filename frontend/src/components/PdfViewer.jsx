import { useEffect, useRef, useState } from "react";
import * as pdfjs from "pdfjs-dist";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

export default function PdfViewer({ url, initialPage = 1, title = "Original PDF" }) {
  const canvasRef = useRef(null);
  const [document, setDocument] = useState(null);
  const [page, setPage] = useState(initialPage || 1);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!url) return undefined;
    let active = true;
    const task = pdfjs.getDocument({ url });
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
    document.getPage(page).then((pdfPage) => {
      if (cancelled) return;
      const viewport = pdfPage.getViewport({ scale: 1.35 });
      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      renderTask = pdfPage.render({ canvasContext: context, viewport });
      return renderTask.promise;
    }).catch((reason) => {
      if (!cancelled && reason?.name !== "RenderingCancelledException") setError(`Could not render page: ${reason.message}`);
    });
    return () => { cancelled = true; renderTask?.cancel(); };
  }, [document, page]);

  if (!url) return <div className="p-8 text-center text-sm text-gray-500">No original PDF is linked.</div>;
  return <div className="overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
    <div className="flex items-center gap-2 border-b bg-white px-3 py-2 text-xs">
      <span className="mr-auto truncate font-semibold text-gray-700">{title}</span>
      <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="rounded border px-2 py-1 disabled:opacity-40">Previous</button>
      <span>Page {page} of {document?.numPages || "—"}</span>
      <button type="button" disabled={!document || page >= document.numPages} onClick={() => setPage((value) => value + 1)} className="rounded border px-2 py-1 disabled:opacity-40">Next</button>
      <a href={`${url}#page=${page}`} target="_blank" rel="noreferrer" className="font-bold text-[#B3432E]">Open directly</a>
    </div>
    {error&&<div className="bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div className="max-h-[680px] overflow-auto p-3"><canvas ref={canvasRef} aria-label={`${title}, page ${page}`} className="mx-auto h-auto max-w-full bg-white shadow" /></div>
  </div>;
}

export function PdfModal({ url, page = 1, title, onClose }) {
  if (!url) return null;
  return <div role="dialog" aria-modal="true" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <div className="max-h-[95vh] w-full max-w-5xl overflow-auto rounded-xl bg-white p-4">
      <div className="mb-3 flex items-center justify-between"><div><h2 className="font-extrabold">{title}</h2><p className="text-xs text-gray-500">Original uploaded file · starting at page {page}</p></div><button type="button" onClick={onClose} className="rounded border px-3 py-1.5 text-sm font-bold">Close</button></div>
      <PdfViewer url={url} initialPage={page} title={title} />
    </div>
  </div>;
}
