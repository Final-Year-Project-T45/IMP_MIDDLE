import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Play, Database, FileText, Landmark, Lock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { executeTask } from '../api';

export default function DemoScenariosPage() {
  const navigate = useNavigate();

  const scenarios = [
    {
      id: 'Scenario 1',
      title: 'Account Inquiry (4821)',
      tier: 'Tier 1 — Read',
      prompt: "What's the current balance and last 5 transactions for account ending 4821?",
      backend: 'SQL Database',
      description: 'Queries balance and transaction history for account ACC-4821.',
      icon: Database
    },
    {
      id: 'Scenario 2',
      title: 'Policy Lookup',
      tier: 'Tier 1 — Read',
      prompt: 'Summarize our policy on wire transfer limits for retail customers.',
      backend: 'Vector DB / Policy KB',
      description: 'Performs semantic vector search over internal banking policy documents.',
      icon: FileText
    },
    {
      id: 'Scenario 3',
      title: 'Fund Transfer (₹85,000)',
      tier: 'Tier 2 — Write',
      prompt: 'Approve a fund transfer of ₹85,00,000 from account 4821 to account 9034.',
      backend: 'Mock Core Banking API',
      description: 'Validates limits, debits ACC-4821, credits ACC-9034, and records transaction.',
      icon: Landmark
    },
    {
      id: 'Scenario 4',
      title: 'Account Freeze (7742)',
      tier: 'Tier 2 — Write',
      prompt: 'Freeze account 7742 — customer reported it as compromised.',
      backend: 'SQL Database',
      description: 'Transitions status of ACC-7742 to FROZEN and creates audit log.',
      icon: Lock
    },
    {
      id: 'Scenario 5',
      title: 'Fraud Case Lookup (#FC-2291)',
      tier: 'Tier 1 — Read',
      prompt: 'Pull up the status of fraud case #FC-2291.',
      backend: 'Fraud Case Repository',
      description: 'Retrieves fraud investigation file #FC-2291 and assigned analyst.',
      icon: AlertTriangle
    },
    {
      id: 'Scenario 6',
      title: 'Loan Disbursement (₹5,00,000)',
      tier: 'Tier 2 — High-Value Write',
      prompt: 'Disburse the approved personal loan of ₹5,00,000 for customer ID C-6634.',
      backend: 'REST API + SQL Database',
      description: 'Verifies sanction, credits customer account, and updates loan status.',
      icon: CheckCircle2
    }
  ];

  const handleRunScenario = (promptText) => {
    navigate('/operations', { state: { prompt: promptText } });
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>
          Demonstration Scenarios
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
          Canonical Phase 1 benchmark test scenarios for project evaluation and multi-agent workflow verification.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          return (
            <div key={sc.id} className="fin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span className="badge badge-purple">{sc.id}</span>
                  <span className="badge badge-blue">{sc.tier}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <Icon size={18} color="#2563EB" />
                  <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A' }}>{sc.title}</h3>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#64748B', marginBottom: '10px' }}>{sc.description}</p>
                <div style={{ padding: '8px 10px', background: '#F8FAFC', borderRadius: '6px', border: '1px solid #E2E8F0', fontSize: '0.775rem', color: '#334155', fontStyle: 'italic' }}>
                  "{sc.prompt}"
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid #E2E8F0' }}>
                <span style={{ fontSize: '0.725rem', color: '#64748B' }}>Backend: {sc.backend}</span>
                <button onClick={() => handleRunScenario(sc.prompt)} className="btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                  <Play size={12} /> Run Scenario
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
