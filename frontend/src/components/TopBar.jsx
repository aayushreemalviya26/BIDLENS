import { useAuth } from "@/lib/authContext";

export default function TopBar({ searchQuery, setSearchQuery }) {
  const { user, openProfile, changeMode } = useAuth();
  if (user.readOnly) return <header className="sticky top-0 z-10 border-b bg-white px-6 py-3"><span className="font-bold text-gray-800">BidLens</span><span className="ml-3 text-sm text-gray-500">Bid Compliance Verification</span></header>;
  return <header className="sticky top-0 z-10 flex flex-wrap items-center gap-5 border-b border-[#DDD6CE] bg-white px-6 py-3">
    <span className="font-bold text-gray-800">BidLens Workstation</span>
    <input aria-label="Search tenders" placeholder="Search tenders…" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} className="min-w-0 flex-1 rounded border bg-gray-50 px-3 py-2 text-sm" />
    <button onClick={changeMode} className="ml-auto text-xs text-gray-600" title="Change Processing Mode">Processing Mode: <b className="text-[#B3432E]">{user.mode}</b></button>
    <button onClick={openProfile} className="rounded-full border border-[#D8D1C8] bg-[#FCFBF9] px-4 py-2 text-sm font-semibold">Admin</button>
  </header>;
}
