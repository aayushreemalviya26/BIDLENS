import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import NewTenderScanModal from "@/components/NewTenderScanModal";
import TenderWorkspace from "@/components/TenderWorkspace";
import BidderWorkspace from "@/components/BidderWorkspace";
import AuditTrailScreen from "@/components/AuditTrailScreen";
import Compliance from "@/pages/Compliance";
import { api } from "@/lib/api";
import AuthWorkspace from "@/components/AuthWorkspace";
import { useAuth } from "@/lib/authContext";
import { ArrowUpToLine, ChevronRight, FileText, Users, Clock3, Building2, CalendarDays, CircleCheck, Activity, Upload, FolderOpen } from "lucide-react";

export default function App() {
  return <AuthWorkspace><Workspace /></AuthWorkspace>;
}

function Workspace() {
  const { user } = useAuth();
  const canUpload = !user.readOnly;
  const [tenders,setTenders]=useState([]); const [activeTenderId,setActiveTenderId]=useState(null); const [currentView,setCurrentView]=useState("dashboard"); const [searchQuery,setSearchQuery]=useState(""); const [scanModalOpen,setScanModalOpen]=useState(false); const [error,setError]=useState("");
  const [demo, setDemo] = useState(null);
  useEffect(() => { api.demo().then(setDemo).catch(e => setError(e.message)); }, []);
  const refresh=async()=>{const items=await api.listTenders();setTenders(items);setActiveTenderId(id=>items.some(x=>x.id===id)?id:(items[0]?.id||null));};
  useEffect(()=>{refresh().catch(e=>setError(e.message));},[]);
  const active=tenders.find(x=>x.id===activeTenderId)||null;
  const filtered=useMemo(()=>tenders.filter(t=>`${t.external_bid_id} ${t.title} ${t.department}`.toLowerCase().includes(searchQuery.toLowerCase())),[tenders,searchQuery]);
  const openTender=(id)=>{setActiveTenderId(id);setCurrentView("tender_overview");};
  const reset=async()=>{if(!window.confirm("Reset the demo database and remove uploaded working copies? Generated demo_files will be preserved."))return;await api.resetDemo();setTenders([]);setActiveTenderId(null);setCurrentView("dashboard");};
  return <div className="flex min-h-screen bg-[#FAF8F5]"><Sidebar currentView={currentView} setCurrentView={setCurrentView} onStartNewScan={()=>setScanModalOpen(true)}/><div className="flex min-w-0 flex-1 flex-col"><TopBar onStartNewScan={()=>setScanModalOpen(true)} searchQuery={searchQuery} setSearchQuery={setSearchQuery}/><main className="flex-1 overflow-y-auto">
    {error&&<div className="m-5 rounded-lg bg-red-50 p-3 text-red-700">Backend unavailable: {error}</div>}
    {(currentView==="dashboard"||currentView==="tenders")&&<Dashboard tenders={filtered} demo={demo} onOpen={openTender} onCreate={()=>setScanModalOpen(true)} onReset={reset} canUpload={canUpload}/>}
    {currentView==="tender_overview"&&(active?<TenderWorkspace tender={active} onRefresh={refresh} onOpenBidders={()=>setCurrentView("bidders")}/>:<Empty onCreate={()=>setScanModalOpen(true)}/>)}
    {currentView==="bidders"&&(active?<BidderWorkspace tender={active} onOpenCompliance={()=>setCurrentView("compliance")}/>:<Empty onCreate={()=>setScanModalOpen(true)}/>)}
    {currentView==="compliance"&&<Compliance selectedTenderId={activeTenderId}/>}
    {currentView==="audit_trail"&&<AuditTrailScreen tenderId={activeTenderId}/>}
  </main><footer className="flex items-center justify-between border-t border-[#E2DCD4] px-8 py-3 text-xs text-[#8A8178]"><span>BidLens</span><span>Copyright © Team Evidentia</span></footer></div><NewTenderScanModal open={scanModalOpen} onOpenChange={setScanModalOpen} onCreated={async(t)=>{await refresh();setActiveTenderId(t.id);setCurrentView("tender_overview");}}/></div>;
}

function Dashboard({tenders,demo,onOpen,onCreate,onReset,canUpload}) {
  const sample = demo?.tender_id ? tenders.find(t=>t.id===demo.tender_id) : null;
  const stage = tenders.length ? "Evaluation available" : "Awaiting tender";
  const displayId = (t) => String(t.external_bid_id||`Tender ${t.id}`).replace(/^PREPROCESSED:/,"");
  return <div className="mx-auto max-w-[1440px] p-7 lg:p-8">
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="min-w-0">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div><p className="mb-1 text-[11px] font-bold uppercase tracking-[.16em] text-[#77716A]">Bid compliance workspace</p><h1 className="text-[28px] font-extrabold tracking-tight text-[#24211F]">Procurement Dashboard</h1><p className="mt-1 text-sm text-[#706A64]">Select a tender or upload a PDF to start an evaluation.</p></div>
          {!demo?.hosted&&<button data-demo-write onClick={onReset} className="border border-red-200 bg-white px-4 py-2 text-sm font-bold text-red-700">Reset Demo</button>}
        </div>
        <div className="mb-5 flex flex-wrap gap-3">
          {demo?.tender_id&&<button onClick={()=>onOpen(demo.tender_id)} className="flex items-center gap-2 bg-[#B3432E] px-5 py-3 text-sm font-bold text-white shadow-sm"><FileText className="h-4 w-4"/>Select Sample Tender</button>}
          {canUpload&&<button onClick={onCreate} className="flex items-center gap-2 border border-[#77716A] bg-white px-5 py-3 text-sm font-bold text-[#24211F]"><ArrowUpToLine className="h-4 w-4"/>Upload Tender PDF</button>}
        </div>
        <div className="mb-5 grid overflow-hidden rounded-lg border border-[#E3DDD5] bg-[#FFFDFC] sm:grid-cols-3">
          <div className="flex gap-3 p-4"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FFF0EA]"><FileText className="h-5 w-5 text-[#C74428]"/></span><div><p className="text-xs text-[#77716A]">Total tenders</p><p className="mt-1 text-xl font-extrabold">{tenders.length}</p><p className="text-xs text-[#8B857F]">in this workspace</p></div></div>
          <div className="flex gap-3 border-y border-[#E3DDD5] p-4 sm:border-x sm:border-y-0"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FFF0EA]"><Clock3 className="h-5 w-5 text-[#C74428]"/></span><div><p className="text-xs text-[#77716A]">Current stage</p><p className="mt-1 font-extrabold">{stage}</p><p className="text-xs text-[#8B857F]">{tenders.length?"Checklist can be reviewed":"Upload or select a tender"}</p></div></div>
          <div className="flex gap-3 p-4"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FFF0EA]"><Users className="h-5 w-5 text-[#C74428]"/></span><div><p className="text-xs text-[#77716A]">Next step</p><p className="mt-1 font-extrabold">{tenders.length?"Select a tender":"Add a tender"}</p><p className="text-xs text-[#8B857F]">to view requirements</p></div></div>
        </div>
        <div className="rounded-lg border border-[#E1DBD3] bg-white p-4">
          <div className="mb-4 flex items-center justify-between"><div className="flex items-center gap-3"><h2 className="text-lg font-extrabold">Available Tenders</h2><span className="rounded-full bg-[#F3EFE9] px-2.5 py-1 text-xs font-bold">{tenders.length} tender{tenders.length===1?"":"s"}</span></div><span className="text-xs text-[#8A8178]">Recently added</span></div>
          {tenders.length===0?<Empty onCreate={onCreate} demo={demo} onOpen={onOpen} canUpload={canUpload}/>:<div className="space-y-3">{tenders.map(t=><button key={t.id} onClick={()=>onOpen(t.id)} className="group w-full rounded-lg border border-[#DDD7D0] bg-[#FFFDFC] p-5 text-left shadow-[0_1px_2px_rgba(36,33,31,.04)] transition hover:border-[#B3432E]">
            <div className="flex items-start justify-between gap-4"><div><p className="text-sm font-extrabold text-[#B3432E]">{displayId(t)}</p><h3 className="mt-1.5 text-lg font-extrabold text-[#24211F]">{t.title}</h3><p className="mt-1 text-sm text-[#77716A]">{t.department||"Procurement workspace"}</p></div><ChevronRight className="mt-7 h-5 w-5 text-[#77716A]"/></div>
            <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-[#E9E4DE] pt-4 text-xs"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#F5F1EC]"><Building2 className="h-4 w-4 text-[#77716A]"/></span><div><span className="text-[#8A8178]">Workspace</span><p className="font-bold text-[#3D3732]">{t.id===sample?.id?"Sample":"Uploaded tender"}</p></div></div><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#F5F1EC]"><FileText className="h-4 w-4 text-[#77716A]"/></span><div><span className="text-[#8A8178]">Document type</span><p className="font-bold text-[#3D3732]">Tender PDF</p></div></div><span className="flex items-center gap-1.5 rounded-md bg-emerald-50 px-2.5 py-1 font-extrabold text-emerald-700"><CircleCheck className="h-3.5 w-3.5"/>{t.status}</span></div>
          </button>)}</div>}
        </div>
      </section>
      <aside className="space-y-4 xl:pt-[106px]">
        <div className="rounded-lg border border-[#E1DBD3] bg-white p-4"><h2 className="mb-3 text-base font-extrabold">Quick Actions</h2><button onClick={onCreate} className="mb-2 flex w-full items-center justify-between rounded-lg border border-[#E5DFD8] p-3 text-left hover:bg-[#FAF8F5]"><span className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#FFF0EA]"><Upload className="h-5 w-5 text-[#C74428]"/></span><span><b className="block text-sm">Upload Tender PDF</b><small className="text-[#77716A]">Start evaluation from your own tender</small></span></span><ChevronRight className="h-4 w-4"/></button>{demo?.tender_id&&<button onClick={()=>onOpen(demo.tender_id)} className="flex w-full items-center justify-between rounded-lg border border-[#E5DFD8] p-3 text-left hover:bg-[#FAF8F5]"><span className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#FFF0EA]"><FolderOpen className="h-5 w-5 text-[#C74428]"/></span><span><b className="block text-sm">Browse Sample Tender</b><small className="text-[#77716A]">Use the provided sample workflow</small></span></span><ChevronRight className="h-4 w-4"/></button>}</div>
        <div className="rounded-lg border border-[#E1DBD3] bg-white p-4"><div className="mb-3 flex items-center justify-between"><h2 className="flex items-center gap-2 text-base font-extrabold"><Activity className="h-4 w-4 text-[#C74428]"/>Workspace Status</h2><span className="text-xs font-bold text-[#B3432E]">Live</span></div><div className="space-y-3 text-sm"><div className="flex justify-between border-b border-[#EEE9E3] pb-3"><span className="text-[#77716A]">Tender records</span><b>{tenders.length}</b></div><div className="flex justify-between"><span className="text-[#77716A]">Processing</span><b>{tenders.length?"Ready":"Waiting"}</b></div></div></div>
      </aside>
    </div>
  </div>;
}
function Empty({onCreate,demo,onOpen,canUpload=true}) { return <div className="m-8 rounded-2xl border-2 border-dashed bg-white p-16 text-center"><h2 className="text-xl font-extrabold">No tender selected</h2><p className="mt-2 text-[#786F66]">Choose the provided tender or upload your own PDF.</p><div className="mt-5 flex justify-center gap-3">{demo?.tender_id&&<button onClick={()=>onOpen?.(demo.tender_id)} className="rounded-lg bg-[#B3432E] px-5 py-2.5 font-bold text-white">Select Sample Tender</button>}{canUpload&&<button onClick={onCreate} className="rounded-lg border bg-white px-5 py-2.5 font-bold">Upload Tender PDF</button>}</div></div>; }
