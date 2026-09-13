import React, { useState } from 'react';

import { INITIAL_TENDERS } from '@/data/mockData';
import { createAuditEntry, AUDIT_ACTIONS } from '@/utils/auditLog';

import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import DashboardScreen from '@/components/DashboardScreen';
import TendersListScreen from '@/components/TendersListScreen';
import TenderOverviewScreen from '@/components/TenderOverviewScreen';
import NewTenderScanModal from '@/components/NewTenderScanModal';
import BidReadinessScreen from '@/components/BidReadinessScreen';
import AuditTrailScreen from '@/components/AuditTrailScreen';
import Compliance from '@/pages/Compliance';

export default function App() {
  // Top-Level Lifted State for persistence across views
  const [tenders, setTenders] = useState(INITIAL_TENDERS);
  const [activeTenderId, setActiveTenderId] = useState('GEM/2024/001');
  const [currentView, setCurrentView] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [auditLog, setAuditLog] = useState([]);

  // Active tender object
  const activeTender =
    tenders.find((t) => t.tender_id === activeTenderId) || tenders[0];

  // Central logger - every officer action funnels through here
  const logActivity = (action, description, meta = {}) => {
    setAuditLog((prev) => [createAuditEntry(action, description, meta), ...prev]);
  };

  // Navigation handlers
  const handleSelectTender = (tenderId) => {
    setActiveTenderId(tenderId);
    setCurrentView('tender_overview');
    logActivity(
      AUDIT_ACTIONS.VIEW_TENDER,
      `Opened tender ${tenderId}`,
      { tenderId }
    );
  };

  const handleBackToDashboard = () => {
    setCurrentView('dashboard');
  };

  // Requirement Handlers
  const handleAddRequirement = (tenderId, newReq) => {
    setTenders((prevTenders) =>
      prevTenders.map((tender) => {
        if (tender.tender_id === tenderId) {
          return {
            ...tender,
            requirements: [...tender.requirements, newReq],
            last_updated: 'Just Now',
          };
        }

        return tender;
      })
    );

    logActivity(
      AUDIT_ACTIONS.ADD_REQUIREMENT,
      `Added requirement "${newReq.title || newReq.description || newReq.requirement_id}" to tender ${tenderId}`,
      { tenderId, requirementId: newReq.requirement_id }
    );
  };

  const handleEditRequirement = (tenderId, reqId, updatedReq) => {
    setTenders((prevTenders) =>
      prevTenders.map((tender) => {
        if (tender.tender_id === tenderId) {
          return {
            ...tender,
            requirements: tender.requirements.map((req) =>
              req.requirement_id === reqId ? updatedReq : req
            ),
            last_updated: 'Just Now',
          };
        }

        return tender;
      })
    );

    logActivity(
      AUDIT_ACTIONS.EDIT_REQUIREMENT,
      `Edited requirement "${updatedReq.title || updatedReq.description || reqId}" in tender ${tenderId}`,
      { tenderId, requirementId: reqId }
    );
  };

  const handleDeleteRequirement = (tenderId, reqId) => {
    // Look up the requirement before it's removed, so the log entry
    // can still describe what was deleted.
    const tender = tenders.find((t) => t.tender_id === tenderId);
    const deletedReq = tender?.requirements.find(
      (req) => req.requirement_id === reqId
    );

    setTenders((prevTenders) =>
      prevTenders.map((tender) => {
        if (tender.tender_id === tenderId) {
          return {
            ...tender,
            requirements: tender.requirements.filter(
              (req) => req.requirement_id !== reqId
            ),
            last_updated: 'Just Now',
          };
        }

        return tender;
      })
    );

    logActivity(
      AUDIT_ACTIONS.DELETE_REQUIREMENT,
      `Deleted requirement "${deletedReq?.title || deletedReq?.description || reqId}" from tender ${tenderId}`,
      { tenderId, requirementId: reqId }
    );
  };

  const handleApproveChecklist = (tenderId, approvedState = true) => {
    setTenders((prevTenders) =>
      prevTenders.map((tender) => {
        if (tender.tender_id === tenderId) {
          return {
            ...tender,
            checklist_approved: approvedState,
            status: approvedState
              ? 'Checklist Approved'
              : 'Under Evaluation',
            last_updated: 'Just Now',
          };
        }

        return tender;
      })
    );

    logActivity(
      approvedState
        ? AUDIT_ACTIONS.APPROVE_CHECKLIST
        : AUDIT_ACTIONS.REVERT_CHECKLIST,
      approvedState
        ? `Approved compliance checklist for tender ${tenderId}`
        : `Reverted checklist approval for tender ${tenderId}`,
      { tenderId }
    );
  };

  const handleAddNewTender = (newTender) => {
    setTenders((prev) => [newTender, ...prev]);
    setActiveTenderId(newTender.tender_id);
    setCurrentView('tender_overview');

    logActivity(
      AUDIT_ACTIONS.CREATE_TENDER,
      `Created new tender ${newTender.tender_id}`,
      { tenderId: newTender.tender_id }
    );
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] flex flex-row">
      {/* Sidebar Navigation */}
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        activeTender={activeTender}
        onStartNewScan={() => setScanModalOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar
          onStartNewScan={() => setScanModalOpen(true)}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        <main className="flex-1 overflow-y-auto">
          {/* Dashboard */}
          {currentView === 'dashboard' && (
            <DashboardScreen
              tenders={tenders}
              onSelectTender={handleSelectTender}
              searchQuery={searchQuery}
            />
          )}

          {/* Tenders */}
          {currentView === 'tenders' && (
            <TendersListScreen
              tenders={tenders}
              onSelectTender={handleSelectTender}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          )}

          {/* Tender Overview */}
          {currentView === 'tender_overview' && (
            <TenderOverviewScreen
              tender={activeTender}
              onBackToDashboard={handleBackToDashboard}
              onAddRequirement={handleAddRequirement}
              onEditRequirement={handleEditRequirement}
              onDeleteRequirement={handleDeleteRequirement}
              onApproveChecklist={handleApproveChecklist}
            />
          )}

          {currentView === 'bid_readiness' && (
            <BidReadinessScreen tender={activeTender} />
          )}

          {/* Compliance */}
          {currentView === 'compliance' && <Compliance />}

          {/* Audit Trail */}
          {currentView === 'audit_trail' && (
            <AuditTrailScreen logs={auditLog} />
          )}

          {/* Settings */}
          {currentView === 'settings' && (
            <div className="p-8 max-w-7xl mx-auto space-y-4">
              <h1 className="text-xl font-bold text-[#2B2523]">
                Workstation Settings
              </h1>

              <div className="border border-[#E5E0DA] bg-white rounded-xl p-8 text-center text-xs text-[#786F66]">
                GeM Compliance Engine & Notification Settings. Select
                Dashboard or Tenders to navigate back.
              </div>
            </div>
          )}
        </main>
      </div>

      {/* New Tender Scan Simulation Modal */}
      <NewTenderScanModal
        open={scanModalOpen}
        onOpenChange={setScanModalOpen}
        onAddNewTender={handleAddNewTender}
      />
    </div>
  );
}
