import React, { useRef, useState } from "react";
import { FileText, Upload } from "lucide-react";
import { api } from "@/lib/api";

export default function NewTenderScanModal({ open, onOpenChange, onCreated }) {
  const [form, setForm] = useState({ external_bid_id: "", title: "", department: "" });
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  if (!open) return null;

  const close = () => { if (!busy) onOpenChange(false); };
  const submit = async (event) => {
    event.preventDefault();
    if (!file) return;
    setBusy(true); setError("");
    try {
      const tender = await api.createTender(form);
      await api.uploadTender(tender.id, file);
      onCreated(await api.tender(tender.id));
      setForm({ external_bid_id: "", title: "", department: "" }); setFile(null); onOpenChange(false);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
    <form onSubmit={submit} className="w-full max-w-xl space-y-5 rounded-2xl border border-[#E5E0DA] bg-white p-7 shadow-2xl">
      <div className="flex items-start justify-between"><div><h2 className="text-xl font-extrabold">Create Tender</h2><p className="mt-1 text-sm text-[#786F66]">Create the backend tender record and upload its real PDF.</p></div><button type="button" onClick={close} aria-label="Close">✕</button></div>
      {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <label className="block text-sm font-bold">GeM bid number<input aria-label="GeM bid number" required value={form.external_bid_id} onChange={(e) => setForm({...form, external_bid_id:e.target.value})} placeholder="GEM/2026/B/7910945" className="mt-2 w-full rounded-lg border p-3 font-normal" /></label>
      <label className="block text-sm font-bold">Tender title<input aria-label="Tender title" required value={form.title} onChange={(e) => setForm({...form, title:e.target.value})} className="mt-2 w-full rounded-lg border p-3 font-normal" /></label>
      <label className="block text-sm font-bold">Department<input aria-label="Department" value={form.department} onChange={(e) => setForm({...form, department:e.target.value})} className="mt-2 w-full rounded-lg border p-3 font-normal" /></label>
      <input ref={inputRef} type="file" accept="application/pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button type="button" onClick={() => inputRef.current?.click()} className="w-full rounded-xl border-2 border-dashed bg-[#FAF8F5] p-6"><Upload className="mx-auto mb-2 h-7 w-7 text-[#B3432E]"/><span className="font-bold">{file?.name || "Choose tender PDF"}</span></button>
      {file && <p className="flex items-center gap-2 text-sm text-[#786F66]"><FileText className="h-4 w-4"/>{file.name}</p>}
      <div className="flex justify-end gap-3"><button type="button" onClick={close} className="rounded-lg px-4 py-2">Cancel</button><button disabled={busy || !file} className="rounded-lg bg-[#B3432E] px-5 py-2.5 font-bold text-white disabled:opacity-50">{busy ? "Uploading…" : "Create & Upload"}</button></div>
    </form>
  </div>;
}
