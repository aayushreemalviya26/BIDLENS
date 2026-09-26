import { useAuth } from "@/lib/authContext";

export default function TopBar({ searchQuery, setSearchQuery }) {
  const { user, openProfile, changeMode } = useAuth();
  return <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-4 border-b bg-white px-6 py-3">
    <span className="font-bold text-gray-800">BidLens Workstation</span>
    <input aria-label="Search tenders" placeholder="Search tenders…" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} className="min-w-0 flex-1 rounded border bg-gray-50 px-3 py-2 text-sm" />
    <button onClick={changeMode} className="text-xs text-gray-600" title="Change Processing Mode">Processing Mode: <b className="text-[#B3432E]">{user.mode}</b></button>
    <button onClick={openProfile} className="rounded border px-3 py-2 text-sm font-semibold">Admin</button>
  </header>;
}
