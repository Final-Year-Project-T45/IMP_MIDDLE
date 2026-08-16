import React, { useEffect, useState } from 'react';
import { getAccounts, getTransactions, getLoans, getFraudCases, getAuditEvents, getTasks } from '../api';
import { CheckSquare, ArrowLeftRight, Landmark, AlertTriangle, Clock, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    pendingReviews: 2,
    todayTxs: 0,
    transfersVolume: 0,
    fraudAttention: 0
  });

  useEffect(() => {
    async function loadStats() {
      try {
        const [txRes, fraudRes] = await Promise.all([
          getTransactions(),
          getFraudCases()
        ]);
        const volume = txRes.data.reduce((sum, t) => sum + (t.amount || 0), 0);
        setStats({
          pendingReviews: 2,
          todayTxs: txRes.data.length,
          transfersVolume: volume,
          fraudAttention: fraudRes.data.length
        });
      } catch (err) {
        console.error('Failed to load operational metrics:', err);
      }
    }
    loadStats();
  }, []);

  const metrics = [
    { title: 'Pending Reviews', value: stats.pendingReviews, icon: CheckSquare, color: '#D97706', subtitle: 'Requires staff review' },
    { title: "Today's Transactions", value: stats.todayTxs, icon: ArrowLeftRight, color: '#2563EB', subtitle: 'Executed operations' },
    { title: 'Transfers Volume', value: `₹${(stats.transfersVolume / 1000).toFixed(0)}k`, icon: Landmark, color: '#059669', subtitle: 'Processed today' },
    { title: 'Fraud Cases Requiring Attention', value: stats.fraudAttention, icon: AlertTriangle, color: '#DC2626', subtitle: 'Active investigations' }
  ];

  const todaysWork = [
    { customerId: 'C-6634', customerName: 'Suresh Kumar', operation: 'Loan Disbursement', amount: 500000.0, status: 'Ready for Review', time: '10:42 AM', path: '/pending-reviews' },
    { customerId: 'C-1001', customerName: 'Rajesh Sharma', operation: 'Fund Transfer', amount: 85000.0, status: 'Completed', time: '10:18 AM', path: '/transactions' },
    { customerId: 'C-1003', customerName: 'Vikram Patel', operation: 'Account Freeze', amount: 0, status: 'Completed', time: '10:31 AM', path: '/accounts' },
    { customerId: 'C-1002', customerName: 'Anita Desai', operation: 'Fraud Case Review', amount: 0, status: 'In Review', time: '10:02 AM', path: '/fraud-cases' }
  ];

  const recentOps = [
    { time: '10:42 AM', title: 'Loan disbursement prepared for customer C-6634 (Sanction: ₹5,00,000)' },
    { time: '10:31 AM', title: 'Account 7742 status transitioned to FROZEN per customer alert' },
    { time: '10:18 AM', title: 'Transfer TXN-88213 of ₹85,000 completed from 4821 to 9034' },
    { time: '10:02 AM', title: 'Fraud case file #FC-2291 reviewed by Analyst Sarah Jenkins' }
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>
          Good afternoon, EMP-1092
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
          Here's what's happening across today's banking operations.
        </p>
      </div>

      {/* Operational Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        {metrics.map((m, i) => {
          const Icon = m.icon;
          return (
            <div key={i} className="fin-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{m.title}</div>
                <div style={{ fontSize: '1.75rem', fontWeight: '800', color: '#0F172A', margin: '4px 0' }}>{m.value}</div>
                <div style={{ fontSize: '0.75rem', color: m.color, fontWeight: '500' }}>{m.subtitle}</div>
              </div>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '8px',
                background: `${m.color}14`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Icon size={22} color={m.color} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Today's Work Section */}
      <div className="fin-card" style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0F172A' }}>Today's Work</h2>
            <p style={{ fontSize: '0.775rem', color: '#64748B' }}>Primary banking operations requiring action or monitoring.</p>
          </div>
          <button onClick={() => navigate('/pending-reviews')} className="btn-secondary">
            View All Pending Reviews <ArrowRight size={14} />
          </button>
        </div>

        <table className="fin-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Operation</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {todaysWork.map((w, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: '600' }}>
                  {w.customerName} <span style={{ fontSize: '0.75rem', color: '#64748B' }}>(<code>{w.customerId}</code>)</span>
                </td>
                <td style={{ fontWeight: '600', color: '#0F172A' }}>{w.operation}</td>
                <td style={{ fontWeight: '700', color: w.amount > 0 ? '#059669' : '#64748B' }}>
                  {w.amount > 0 ? `₹${w.amount.toLocaleString('en-IN')}` : '—'}
                </td>
                <td>
                  <span className={`badge ${w.status === 'Completed' ? 'badge-success' : 'badge-pending'}`}>
                    {w.status}
                  </span>
                </td>
                <td style={{ fontSize: '0.775rem', color: '#64748B' }}>{w.time}</td>
                <td>
                  <button onClick={() => navigate(w.path)} className="btn-secondary" style={{ padding: '3px 8px', fontSize: '0.75rem' }}>
                    Open
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent Human Operations Stream */}
      <div className="fin-card">
        <h2 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0F172A', marginBottom: '14px' }}>
          Recent Operations Stream
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {recentOps.map((op, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.825rem', color: '#334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#64748B', width: '80px', flexShrink: 0, fontSize: '0.75rem' }}>
                <Clock size={12} /> {op.time}
              </div>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#2563EB', flexShrink: 0 }}></div>
              <div style={{ fontWeight: '500' }}>{op.title}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
