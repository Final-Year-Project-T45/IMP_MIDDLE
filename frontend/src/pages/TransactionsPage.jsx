import React, { useEffect, useState } from 'react';
import { getTransactions } from '../api';
import { RefreshCw, Search } from 'lucide-react';

export default function TransactionsPage() {
  const [txs, setTxs] = useState([]);
  const [filter, setFilter] = useState('');

  const fetchTxs = async () => {
    try {
      const res = await getTransactions();
      setTxs(res.data);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    }
  };

  useEffect(() => {
    fetchTxs();
  }, []);

  const filtered = txs.filter((t) =>
    t.transaction_id.toLowerCase().includes(filter.toLowerCase()) ||
    t.sender_account.toLowerCase().includes(filter.toLowerCase()) ||
    t.receiver_account.toLowerCase().includes(filter.toLowerCase()) ||
    (t.description && t.description.toLowerCase().includes(filter.toLowerCase()))
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Transactions</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Core banking ledger for processed deposits, transfers, and disbursements.</p>
        </div>
        <button onClick={fetchTxs} className="btn-secondary">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="fin-card">
        <div style={{ marginBottom: '16px', position: 'relative', width: '320px' }}>
          <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '10px' }} />
          <input
            type="text"
            placeholder="Search transaction ID or account..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ paddingLeft: '36px' }}
          />
        </div>

        <table className="fin-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>Date & Time</th>
              <th>From</th>
              <th>To</th>
              <th>Amount</th>
              <th>Type</th>
              <th>Initiated By</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => (
              <tr key={t.transaction_id}>
                <td><code>{t.transaction_id}</code></td>
                <td style={{ fontSize: '0.775rem', color: '#64748B' }}>{t.timestamp ? t.timestamp.substring(0, 19).replace('T', ' ') : 'N/A'}</td>
                <td><code>{t.sender_account}</code></td>
                <td><code>{t.receiver_account}</code></td>
                <td style={{ fontWeight: '700', color: '#0F172A' }}>₹{t.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td><span className="badge badge-purple">{t.transaction_type}</span></td>
                <td style={{ fontSize: '0.8rem', color: '#64748B' }}>{t.initiated_by}</td>
                <td><span className="badge badge-success">{t.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
