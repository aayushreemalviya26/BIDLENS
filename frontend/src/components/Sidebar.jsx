import React from 'react';
import {
  Award,
  CheckSquare,
  FileText,
  History,
  LayoutDashboard,
  PlusCircle,
} from 'lucide-react';

export default function Sidebar({
  currentView,
  setCurrentView,
  onStartNewScan,
}) {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      view: 'dashboard',
    },
    {
      id: 'tenders',
      label: 'Tenders',
      icon: FileText,
      view: 'tenders',
    },
    {
      id: 'bidder_evaluation',
      label: 'Bidder Evaluation',
      icon: CheckSquare,
      view: 'bidders',
    },
    {
      id: 'compliance',
      label: 'Compliance Matrix',
      icon: CheckSquare,
      view: 'compliance',
    },
    {
      id: 'audit_trail',
      label: 'Audit Trail',
      icon: History,
      view: 'audit_trail',
    },
  ];

  return (
    <aside className="w-64 bg-[#F5F1EB] border-r border-[#E5E0DA] flex flex-col justify-between h-screen sticky top-0 select-none z-20 shrink-0">
      <div className="p-4 space-y-6">
        <div className="flex items-center space-x-3 px-1 pt-1">
          <div className="w-9 h-9 rounded-xl bg-[#B3432E] flex items-center justify-center text-white font-bold text-lg shadow-xs">
            <Award className="w-5 h-5 stroke-[2.5]" />
          </div>

          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-extrabold text-base tracking-tight text-[#2B2523]">
                BidLens
              </span>
              <span className="text-[10px] font-bold text-[#B3432E] bg-rose-100/70 px-1.5 py-0.5 rounded border border-rose-200/70 uppercase">
                Enterprise
              </span>
            </div>

            <p className="text-xs text-[#786F66] font-medium">
              Global Procurement Unit
            </p>
          </div>
        </div>

        <button
          onClick={onStartNewScan}
          className="w-full bg-[#B3432E] hover:bg-[#9E3824] text-white flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl font-semibold text-sm shadow-xs transition-colors"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Tender Scan</span>
        </button>

        <nav className="space-y-1 pt-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.view;

            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.view)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-[#B3432E] text-white shadow-xs'
                    : 'text-[#574E46] hover:bg-[#EAE4DC] hover:text-[#2B2523]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`w-4.5 h-4.5 ${
                      isActive ? 'text-white' : 'text-[#786F66]'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge !== undefined && (
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-extrabold ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-rose-100 text-[#B3432E]'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-[#E5E0DA] bg-[#EFEBE4]/50 text-xs font-medium text-[#786F66]">
        <span>BidLens Platform v4.2</span>
      </div>
    </aside>
  );
}
