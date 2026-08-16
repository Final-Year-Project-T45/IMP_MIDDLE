import React from 'react';
import { CreditCard, ArrowLeftRight, Landmark, Lock, FileText, AlertTriangle, BookOpen } from 'lucide-react';

export default function QuickActions({ onSelectAction, disabled }) {
  const actions = [
    { label: 'Check Account', prompt: "What's the current balance and last 5 transactions for account ending 4821?", icon: CreditCard },
    { label: 'Make Transfer', prompt: 'Approve a fund transfer of ₹85,000 from account 4821 to account 9034.', icon: Landmark },
    { label: 'Freeze Account', prompt: 'Freeze account 7742 — customer reported it as compromised.', icon: Lock },
    { label: 'Review Loan', prompt: 'Disburse the approved personal loan of ₹5,00,000 for customer ID C-6634.', icon: FileText },
    { label: 'Investigate Fraud Case', prompt: 'Pull up the status of fraud case #FC-2291.', icon: AlertTriangle },
    { label: 'Look Up Policy', prompt: 'Summarize our policy on wire transfer limits for retail customers.', icon: BookOpen }
  ];

  return (
    <div style={{ marginTop: '14px' }}>
      <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748B', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        Quick Operational Shortcuts
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {actions.map((act, idx) => {
          const Icon = act.icon;
          return (
            <button
              key={idx}
              disabled={disabled}
              onClick={() => onSelectAction(act.prompt)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#FFFFFF',
                border: '1px solid #CBD5E1',
                color: '#334155',
                fontSize: '0.775rem',
                fontWeight: '600',
                cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease'
              }}
              className="quick-action-btn"
            >
              <Icon size={14} color="#2563EB" />
              <span>{act.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
