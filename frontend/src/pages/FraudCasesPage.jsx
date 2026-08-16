import React, { useEffect, useState } from 'react';
import { getFraudCases } from '../api';
import { AlertTriangle, RefreshCw, UserCheck, Shield } from 'lucide-react';

export default function FraudCasesPage() {
  const [cases, setCases] = useState([]);

  const fetchCases = async () => {
    try {
      const res = await getFraudCases();
      setCases(res.data);
    } catch (err) {
      console.error('Failed to load fraud cases:', err);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Fraud Cases</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Internal fraud investigation workspace and incident files.</p>
        </div>
        <button onClick={fetchCases} className="btn-secondary">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {cases.map((c) => (
          <div key={c.case_id} className="fin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '14px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="badge badge-purple">Case #{c.case_id}</span>
                <span className={`badge ${c.severity === 'HIGH' ? 'badge-frozen' : 'badge-pending'}`}>{c.severity} Severity</span>
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A', marginBottom: '6px' }}>{c.case_type}</h3>
              <p style={{ fontSize: '0.825rem', color: '#334155', lineHeight: '1.5', marginBottom: '12px' }}>{c.description}</p>
            </div>

            <div style={{ paddingTop: '12px', borderTop: '1px solid #E2E8F0', fontSize: '0.775rem', color: '#64748B', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div>Target Account: <code>{c.account_id}</code></div>
              <div>Customer: <strong>{c.customer_name}</strong> (<code>{c.customer_id}</code>)</div>
              <div>Assigned Analyst: <strong style={{ color: '#2563EB' }}>{c.assigned_analyst}</strong></div>
              <div>Status: <span className="badge badge-pending" style={{ fontSize: '0.675rem' }}>{c.case_status}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
