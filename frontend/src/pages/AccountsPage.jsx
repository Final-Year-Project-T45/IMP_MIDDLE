import React, { useEffect, useState } from 'react';
import { getAccounts, freezeAccount, unfreezeAccount } from '../api';
import { CreditCard, Lock, Unlock, RefreshCw, Search, Eye, X } from 'lucide-react';

export default function AccountsPage() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAcc, setSelectedAcc] = useState(null);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res = await getAccounts();
      setAccounts(res.data);
    } catch (err) {
      console.error('Failed to load accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleToggleFreeze = async (acc) => {
    try {
      if (acc.status === 'FROZEN') {
        await unfreezeAccount(acc.account_id);
      } else {
        await freezeAccount(acc.account_id, 'Staff security status toggle');
      }
      fetchAccounts();
      if (selectedAcc && selectedAcc.account_id === acc.account_id) {
        setSelectedAcc({ ...selectedAcc, status: acc.status === 'FROZEN' ? 'ACTIVE' : 'FROZEN' });
      }
    } catch (err) {
      alert(`Action failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const filtered = accounts.filter((a) => {
    const matchesStatus = filterStatus === 'ALL' || a.status === filterStatus;
    const matchesSearch = a.account_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          a.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          a.customer_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Accounts</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Customer banking accounts ledger and status management.</p>
        </div>
        <button onClick={fetchAccounts} className="btn-secondary">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="fin-card">
        {/* Search & Status Filters */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', width: '320px' }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search by account ID, customer name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {['ALL', 'ACTIVE', 'FROZEN', 'CLOSED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid #CBD5E1',
                  background: filterStatus === st ? '#2563EB' : '#FFFFFF',
                  color: filterStatus === st ? '#FFFFFF' : '#475569',
                  fontSize: '0.775rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <table className="fin-table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Customer</th>
              <th>Type</th>
              <th>Available Balance</th>
              <th>Daily Limit</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a) => (
              <tr key={a.account_id}>
                <td><code>{a.account_id}</code></td>
                <td style={{ fontWeight: '600', color: '#0F172A' }}>
                  {a.customer_name} <span style={{ fontSize: '0.75rem', color: '#64748B' }}>(<code>{a.customer_id}</code>)</span>
                </td>
                <td><span className="badge badge-retail">{a.account_type}</span></td>
                <td style={{ fontWeight: '700', color: '#059669' }}>₹{a.balance?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td>₹{a.daily_transfer_limit?.toLocaleString('en-IN')}</td>
                <td>
                  <span className={`badge ${a.status === 'ACTIVE' ? 'badge-success' : 'badge-frozen'}`}>
                    {a.status}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button onClick={() => setSelectedAcc(a)} className="btn-secondary" style={{ padding: '3px 8px', fontSize: '0.75rem' }}>
                      <Eye size={12} /> View
                    </button>
                    <button
                      onClick={() => handleToggleFreeze(a)}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: 'none',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        background: a.status === 'FROZEN' ? '#ECFDF5' : '#FEF2F2',
                        color: a.status === 'FROZEN' ? '#047857' : '#B91C1C'
                      }}
                    >
                      {a.status === 'FROZEN' ? <><Unlock size={12} /> Unfreeze</> : <><Lock size={12} /> Freeze</>}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Account Details Slide-out Modal */}
      {selectedAcc && (
        <div className="modal-overlay" onClick={() => setSelectedAcc(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#0F172A' }}>
                Account {selectedAcc.account_id}
              </h2>
              <button onClick={() => setSelectedAcc(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div><strong>Customer Name:</strong> {selectedAcc.customer_name} (<code>{selectedAcc.customer_id}</code>)</div>
              <div><strong>Account Type:</strong> {selectedAcc.account_type}</div>
              <div>
                <strong>Available Balance:</strong> <span style={{ fontSize: '1.25rem', fontWeight: '800', color: '#059669' }}>₹{selectedAcc.balance?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
              </div>
              <div><strong>Daily Transfer Limit:</strong> ₹{selectedAcc.daily_transfer_limit?.toLocaleString('en-IN')}</div>
              <div><strong>Account Status:</strong> <span className={`badge ${selectedAcc.status === 'ACTIVE' ? 'badge-success' : 'badge-frozen'}`}>{selectedAcc.status}</span></div>

              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #E2E8F0', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={() => handleToggleFreeze(selectedAcc)} className="btn-primary" style={{ background: selectedAcc.status === 'FROZEN' ? '#059669' : '#DC2626' }}>
                  {selectedAcc.status === 'FROZEN' ? 'Unfreeze Account' : 'Freeze Account'}
                </button>
                <button onClick={() => setSelectedAcc(null)} className="btn-secondary">Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
