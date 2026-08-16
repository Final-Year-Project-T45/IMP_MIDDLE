import React from 'react';
import { Play, Sparkles } from 'lucide-react';

export default function SeedTaskSelector({ onSelectTask, isLoading }) {
  const seedTasks = [
    {
      id: 1,
      tier: 'Tier 1 — Read',
      category: 'ACCOUNT_INQUIRY',
      title: 'Task 1: Account Inquiry (4821)',
      prompt: "What's the current balance and last 5 transactions for account ending 4821?",
      backend: 'SQL Database'
    },
    {
      id: 2,
      tier: 'Tier 1 — Read',
      category: 'POLICY_LOOKUP',
      title: 'Task 2: Policy Lookup',
      prompt: 'Summarize our policy on wire transfer limits for retail customers.',
      backend: 'Vector DB / Policy KB'
    },
    {
      id: 3,
      tier: 'Tier 2 — Write',
      category: 'FUND_TRANSFER',
      title: 'Task 3: Fund Transfer (₹85,000)',
      prompt: 'Approve a fund transfer of ₹85,000 from account 4821 to account 9034.',
      backend: 'Mock Core Banking API'
    },
    {
      id: 4,
      tier: 'Tier 2 — Write',
      category: 'ACCOUNT_FREEZE',
      title: 'Task 4: Account Freeze (7742)',
      prompt: 'Freeze account 7742 — customer reported it as compromised.',
      backend: 'SQL Database'
    },
    {
      id: 5,
      tier: 'Tier 1 — Read',
      category: 'FRAUD_CASE_LOOKUP',
      title: 'Task 5: Fraud Case Lookup (#FC-2291)',
      prompt: 'Pull up the status of fraud case #FC-2291.',
      backend: 'Fraud Case Repository'
    },
    {
      id: 6,
      tier: 'Tier 2 — High-Value Write',
      category: 'LOAN_DISBURSEMENT',
      title: 'Task 6: Loan Disbursement (₹5,00,000)',
      prompt: 'Disburse the approved personal loan of ₹5,00,000 for customer ID C-6634.',
      backend: 'REST API + SQL Database'
    }
  ];

  return (
    <div className="fin-card" style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
        <Sparkles size={18} color="#F59E0B" />
        <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#F9FAFB' }}>
          Canonical Benchmark Seed Tasks (Phase 1 Baseline)
        </h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {seedTasks.map((t) => (
          <div
            key={t.id}
            onClick={() => !isLoading && onSelectTask(t.prompt)}
            style={{
              padding: '14px',
              borderRadius: '8px',
              background: '#111827',
              border: '1px solid #374151',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
              display: 'flex',
              flexDirection: 'column',
              justify: 'space-between',
              gap: '8px'
            }}
            className="seed-task-card"
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>{t.tier}</span>
                <span style={{ fontSize: '0.65rem', color: '#9CA3AF' }}>{t.backend}</span>
              </div>
              <div style={{ fontWeight: '700', fontSize: '0.85rem', color: '#F9FAFB' }}>{t.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#9CA3AF', marginTop: '4px', fontStyle: 'italic' }}>
                "{t.prompt}"
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
              <button
                disabled={isLoading}
                style={{
                  background: 'rgba(59, 130, 246, 0.15)',
                  color: '#60A5FA',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '6px',
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: '600',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Play size={12} /> Launch
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
