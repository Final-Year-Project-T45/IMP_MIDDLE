import React, { useState } from 'react';
import { CheckSquare, CheckCircle, AlertCircle, Eye, Send, Lock } from 'lucide-react';
import { disburseLoan, freezeAccount } from '../api';

export default function PendingReviewsPage() {
  const [reviews, setReviews] = useState([
    {
      id: 'REV-101',
      type: 'Loan Disbursement',
      customer: 'Suresh Kumar (C-6634)',
      reference: 'LOAN-6634',
      amount: 500000.0,
      details: 'Sanctioned Personal Loan approved by Credit Committee Panel B. Awaiting staff disbursement sign-off.',
      status: 'Awaiting Review',
      actionType: 'DISBURSE_LOAN'
    },
    {
      id: 'REV-102',
      type: 'Account Emergency Freeze',
      customer: 'Vikram Patel (C-1003)',
      reference: 'ACC-7742',
      amount: 0,
      details: 'Customer reported suspicious foreign IP debit attempts. Emergency freeze sign-off requested.',
      status: 'Awaiting Review',
      actionType: 'FREEZE_ACCOUNT'
    }
  ]);

  const [message, setMessage] = useState(null);

  const handleApprove = async (item) => {
    try {
      if (item.actionType === 'DISBURSE_LOAN') {
        await disburseLoan('LOAN-6634');
        setMessage(`Loan LOAN-6634 successfully disbursed to customer ${item.customer}!`);
      } else if (item.actionType === 'FREEZE_ACCOUNT') {
        await freezeAccount('ACC-7742', 'Staff approved security freeze');
        setMessage(`Account ACC-7742 status transitioned to FROZEN!`);
      }
      setReviews(reviews.filter((r) => r.id !== item.id));
    } catch (err) {
      alert(`Approval error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>
          Pending Operational Reviews
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
          Human-in-the-loop operational review desk for high-impact transactions and security actions.
        </p>
      </div>

      {message && (
        <div style={{ padding: '14px 18px', borderRadius: '6px', background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#047857', marginBottom: '20px', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} />
          <div>{message}</div>
        </div>
      )}

      <div className="fin-card">
        {reviews.length > 0 ? (
          <table className="fin-table">
            <thead>
              <tr>
                <th>Review ID</th>
                <th>Operation Type</th>
                <th>Customer / Account</th>
                <th>Sanctioned Amount</th>
                <th>Details</th>
                <th>Status</th>
                <th>Staff Decision</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((r) => (
                <tr key={r.id}>
                  <td><code>{r.id}</code></td>
                  <td style={{ fontWeight: '600', color: '#0F172A' }}>{r.type}</td>
                  <td>{r.customer}</td>
                  <td style={{ fontWeight: '700', color: r.amount > 0 ? '#059669' : '#64748B' }}>
                    {r.amount > 0 ? `₹${r.amount.toLocaleString('en-IN')}` : '—'}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#475569', maxWidth: '280px' }}>{r.details}</td>
                  <td><span className="badge badge-pending">{r.status}</span></td>
                  <td>
                    <button onClick={() => handleApprove(r)} className="btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                      Approve & Execute
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '32px 0', color: '#64748B' }}>
            <CheckCircle size={32} color="#059669" style={{ margin: '0 auto 8px auto', display: 'block' }} />
            <div style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A' }}>You're all caught up!</div>
            <div style={{ fontSize: '0.825rem', marginTop: '4px' }}>No pending operational reviews require your attention right now.</div>
          </div>
        )}
      </div>
    </div>
  );
}
