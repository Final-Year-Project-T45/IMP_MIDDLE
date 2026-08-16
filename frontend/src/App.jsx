import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import Dashboard from './pages/Dashboard';
import TaskConsole from './pages/TaskConsole';
import AccountsPage from './pages/AccountsPage';
import TransactionsPage from './pages/TransactionsPage';
import TransfersPage from './pages/TransfersPage';
import LoansPage from './pages/LoansPage';
import FraudCasesPage from './pages/FraudCasesPage';
import PolicyCenterPage from './pages/PolicyCenterPage';
import PendingReviewsPage from './pages/PendingReviewsPage';
import TaskHistoryPage from './pages/TaskHistoryPage';
import AuditTrailPage from './pages/AuditTrailPage';
import AgentActivityPage from './pages/AgentActivityPage';
import DemoScenariosPage from './pages/DemoScenariosPage';

export default function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Navbar />
          <main className="page-body">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/operations" element={<TaskConsole />} />
              <Route path="/console" element={<TaskConsole />} />
              <Route path="/task-console" element={<TaskConsole />} />
              <Route path="/accounts" element={<AccountsPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/transfers" element={<TransfersPage />} />
              <Route path="/loans" element={<LoansPage />} />
              <Route path="/fraud-cases" element={<FraudCasesPage />} />
              <Route path="/policies" element={<PolicyCenterPage />} />
              <Route path="/pending-reviews" element={<PendingReviewsPage />} />
              <Route path="/operation-history" element={<TaskHistoryPage />} />
              <Route path="/audit-trail" element={<AuditTrailPage />} />
              <Route path="/agent-activity" element={<AgentActivityPage />} />
              <Route path="/demo-scenarios" element={<DemoScenariosPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
