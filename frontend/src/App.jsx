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
  const [tenders, setTenders] = useState(INITIAL_TENDERS);
  const [activeTenderId, setActiveTenderId] = useState('GEM/2024/001');
  const [currentView, setCurrentView] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [auditLog, setAuditLog] = useState([]);

  const activeTender =
    tenders.find((tender) => tender.tender_id === activeTenderId) ||
    tenders[0];

  const logActivity = (action, description, meta = {}) => {
    setAuditLog((previousLogs) => [
      createAuditEntry(action, description, meta),
      ...previousLogs,
    ]);
  };

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

  const handleAddRequirement = (tenderId, newRequirement) => {
    setTenders((previousTenders) =>
      previousTenders.map((tender) =>
        tender.tender_id === tenderId
          ? {
              ...tender,
              requirements: [...tender.requirements, newRequirement],
              last_updated: 'Just Now',
            }
          : tender
      )
    );

    logActivity(
      AUDIT_ACTIONS.ADD_REQUIREMENT,
      `Added requirement ${newRequirement.requirement_id}`,
      { tenderId, requirementId: newRequirement.requirement_id }
    );
  };

  const handleEditRequirement = (tenderId, requirementId, updatedRequirement) => {
    setTenders((previousTenders) =>
      previousTenders.map((tender) =>
        tender.tender_id === tenderId
          ? {
              ...tender,
              requirements: tender.requirements.map((requirement) =>
                requirement.requirement_id === requirementId
                  ? updatedRequirement
                  : requirement
              ),
              last_updated: 'Just Now',
            }
          : tender
      )
    );

    logActivity(
      AUDIT_ACTIONS.EDIT_REQUIREMENT,
      `Edited requirement ${requirementId}`,
      { tenderId, requirementId }
    );
  };

  const handleDeleteRequirement = (tenderId, requirementId) => {
    setTenders((previousTenders) =>
      previousTenders.map((tender) =>
        tender.tender_id === tenderId
          ? {
              ...tender,
              requirements: tender.requirements.filter(
                (requirement) => requirement.requirement_id !== requirementId
              ),
              last_updated: 'Just Now',
            }
          : tender
      )
    );

    logActivity(
      AUDIT_ACTIONS.DELETE_REQUIREMENT,
      `Deleted requirement ${requirementId}`,
      { tenderId, requirementId }
    );
  };

  const handleApproveChecklist = (tenderId, approvedState = true) => {
    setTenders((previousTenders) =>
      previousTenders.map((tender) =>
        tender.tender_id === tenderId
          ? {
              ...tender,
              checklist_approved: approvedState,
              status: approvedState
                ? 'Checklist Approved'
                : 'Under Evaluation',
              last_updated: 'Just Now',
            }
          : tender
      )
    );

    logActivity(
      approvedState
        ? AUDIT_ACTIONS.APPROVE_CHECKLIST
        : AUDIT_ACTIONS.REVERT_CHECKLIST,
      approvedState
        ? `Approved checklist for tender ${tenderId}`
        : `Reverted checklist approval for tender ${tenderId}`,
      { tenderId }
    );
  };

  const handleAddNewTender = (newTender) => {
    setTenders((previousTenders) => [newTender, ...previousTenders]);
    setActiveTenderId(newTender.tender_id);
    setCurrentView('tender_overview');

    logActivity(
      AUDIT_ACTIONS.CREATE_TENDER,
      `Created tender ${newTender.tender_id}`,
      { tenderId: newTender.tender_id }
    );
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] flex flex-row">
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        activeTender={activeTender}
        onStartNewScan={() => setScanModalOpen(true)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <TopBar
          onStartNewScan={() => setScanModalOpen(true)}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        <main className="flex-1 overflow-y-auto">
          {currentView === 'dashboard' && (
            <DashboardScreen
              tenders={tenders}
              onSelectTender={handleSelectTender}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'tenders' && (
            <TendersListScreen
              tenders={tenders}
              onSelectTender={handleSelectTender}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          )}

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

          {currentView === 'compliance' && <Compliance />}

          {currentView === 'audit_trail' && (
            <AuditTrailScreen logs={auditLog} />
          )}
        </main>
      </div>

      <NewTenderScanModal
        open={scanModalOpen}
        onOpenChange={setScanModalOpen}
        onAddNewTender={handleAddNewTender}
      />
    </div>
  );
}
