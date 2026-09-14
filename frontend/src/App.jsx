import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import NewTenderScanModal from "@/components/NewTenderScanModal";
import TenderWorkspace from "@/components/TenderWorkspace";
import BidderWorkspace from "@/components/BidderWorkspace";
import AuditTrailScreen from "@/components/AuditTrailScreen";
import Compliance from "@/pages/Compliance";
import { api } from "@/lib/api";

export default function App() {
  const [tenders,setTenders]=useState([]); const [activeTenderId,setActiveTenderId]=useState(null); const [currentView,setCurrentView]=useState("dashboard"); const [searchQuery,setSearchQuery]=useState(""); const [scanModalOpen,setScanModalOpen]=useState(false); const [error,setError]=useState("");
  const refresh=async()=>{const items=await api.listTenders();setTenders(items);setActiveTenderId(id=>items.some(x=>x.id===id)?id:(items[0]?.id||null));};
  useEffect(()=>{refresh().catch(e=>setError(e.message));},[]);
  const active=tenders.find(x=>x.id===activeTenderId)||null;
  const filtered=useMemo(()=>tenders.filter(t=>`${t.external_bid_id} ${t.title} ${t.department}`.toLowerCase().includes(searchQuery.toLowerCase())),[tenders,searchQuery]);
  const openTender=(id)=>{setActiveTenderId(id);setCurrentView("tender_overview");};
  const reset=async()=>{if(!window.confirm("Reset the demo database and remove uploaded working copies? Generated demo_files will be preserved."))return;await api.resetDemo();setTenders([]);setActiveTenderId(null);setCurrentView("dashboard");};
  return <div className="flex min-h-screen bg-[#FAF8F5]"><Sidebar currentView={currentView} setCurrentView={setCurrentView} onStartNewScan={()=>setScanModalOpen(true)}/><div className="flex min-w-0 flex-1 flex-col"><TopBar onStartNewScan={()=>setScanModalOpen(true)} searchQuery={searchQuery} setSearchQuery={setSearchQuery}/><main className="flex-1 overflow-y-auto">
    {error&&<div className="m-5 rounded-lg bg-red-50 p-3 text-red-700">Backend unavailable: {error}</div>}
    {(currentView==="dashboard"||currentView==="tenders")&&<Dashboard tenders={filtered} onOpen={openTender} onCreate={()=>setScanModalOpen(true)} onReset={reset}/>}
    {currentView==="tender_overview"&&(active?<TenderWorkspace tender={active} onRefresh={refresh} onOpenBidders={()=>setCurrentView("bidders")}/>:<Empty onCreate={()=>setScanModalOpen(true)}/>)}
    {currentView==="bidders"&&(active?<BidderWorkspace tender={active} onOpenCompliance={()=>setCurrentView("compliance")}/>:<Empty onCreate={()=>setScanModalOpen(true)}/>)}
    {currentView==="compliance"&&<Compliance selectedTenderId={activeTenderId}/>}
    {currentView==="audit_trail"&&<AuditTrailScreen tenderId={activeTenderId}/>}
  </main></div><NewTenderScanModal open={scanModalOpen} onOpenChange={setScanModalOpen} onCreated={async(t)=>{await refresh();setActiveTenderId(t.id);setCurrentView("tender_overview");}}/></div>;
}

function Dashboard({tenders,onOpen,onCreate,onReset}) { return <div className="mx-auto max-w-7xl space-y-5 p-8"><div className="flex items-start justify-between"><div><h1 className="text-2xl font-extrabold">Procurement Dashboard</h1><p className="text-sm text-[#786F66]">Live backend records only. No sample bidders are loaded by default.</p></div><button onClick={onReset} className="rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-bold text-red-700">Reset Demo</button></div>{tenders.length===0?<Empty onCreate={onCreate}/>:<div className="grid gap-4 md:grid-cols-2">{tenders.map(t=><button key={t.id} onClick={()=>onOpen(t.id)} className="rounded-2xl border bg-white p-5 text-left shadow-sm hover:border-[#B3432E]"><p className="text-sm font-bold text-[#B3432E]">{t.external_bid_id||`Tender ${t.id}`}</p><h2 className="mt-2 text-lg font-extrabold">{t.title}</h2><p className="mt-1 text-sm text-[#786F66]">{t.department||"No department"}</p><span className="mt-4 inline-block rounded-full bg-[#F5F1EB] px-3 py-1 text-xs font-bold">{t.status}</span></button>)}</div>}</div>; }
function Empty({onCreate}) { return <div className="m-8 rounded-2xl border-2 border-dashed bg-white p-16 text-center"><h2 className="text-xl font-extrabold">No tender selected</h2><p className="mt-2 text-[#786F66]">Create a tender and upload its real GeM PDF to begin.</p><button onClick={onCreate} className="mt-5 rounded-lg bg-[#B3432E] px-5 py-2.5 font-bold text-white">New Tender Scan</button></div>; }
