import React from 'react';
import { Search, Bell, Settings } from 'lucide-react';

export default function TopBar({ onStartNewScan, searchQuery, setSearchQuery }) {
  return (
    <header className="h-16 bg-white border-b border-[#E5E0DA] px-8 flex items-center justify-between sticky top-0 z-10">
      {/* Left branding & quick nav links */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3 text-sm text-[#786F66]">
          <span className="text-base font-extrabold text-[#2B2523] tracking-tight">BidLens Workstation</span>
          <span>•</span>
          <span className="font-medium hover:text-[#2B2523] cursor-pointer">Enterprise Suite</span>
          <span>•</span>
          <span className="font-medium hover:text-[#2B2523] cursor-pointer">Help Center</span>
        </div>
      </div>

      {/* Center Search Bar */}
      <div className="flex-1 max-w-xl mx-8">
        <div className="relative">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-[#786F66]" />
          <input
            type="text"
            placeholder="Search RFPs, clauses, eligibility criteria..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 h-10 text-sm bg-[#FAF8F5] border border-[#E5E0DA] focus:bg-white rounded-xl focus:outline-none focus:border-[#B3432E] transition-colors"
          />
        </div>
      </div>

      {/* Right User Actions */}
      <div className="flex items-center space-x-4">

        {/* Notifications */}
        <button className="p-2 rounded-xl hover:bg-[#F5F1EB] text-[#786F66] hover:text-[#2B2523] transition-colors">
          <Bell className="w-5 h-5" />
        </button>

        {/* Settings */}
        <button className="p-2 rounded-xl hover:bg-[#F5F1EB] text-[#786F66] hover:text-[#2B2523] transition-colors">
          <Settings className="w-5 h-5" />
        </button>

        {/* Profile Avatar */}
        <div className="flex items-center space-x-3 pl-2 border-l border-[#E5E0DA]">
          <div className="w-8 h-8 rounded-full bg-[#B3432E]/10 border border-[#B3432E]/20 flex items-center justify-center text-[#B3432E] font-extrabold text-sm">
            MP
          </div>
        </div>
      </div>
    </header>
  );
}
