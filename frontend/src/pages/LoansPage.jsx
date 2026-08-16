import React, { useEffect, useState } from 'react';
import { getLoans, disburseLoan } from '../api';
import { FileText, CheckCircle, RefreshCw, X } from 'lucide-react';

export default function LoansPage() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLoan, setSelectedLoan] = useState(null);

  const fetchLoans = async () => {
    setLoading(true);
    try {
      const res = await getLoans();
      setLoans(res.data);
    } catch (err) {
      console.error('Failed to load loans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, []);

  const handleConfirmDisbursement = async (loanId) => {
    try {
      await disburseLoan(loanId);
      alert(`Disbursement confirmed for loan ${loanId}!`);
      setSelectedLoan(null);
      fetchLoans();
    } catch (err) {
      alert(`Disbursement failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Loans</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Sanctioned customer loans and disbursement management.</p>
        </div>
        <button onClick={fetchLoans} className="btn-secondary">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="fin-card">
        <table className="fin-table">
          <thead>
            <tr>
              <th>Loan ID</th>
              <th>Customer</th>
              <th>Type</th>
              <th>Sanctioned Amount</th>
              <th>Approval</th>
              <th>Disbursement</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((l) => (
              <tr key={l.loan_id}>
                <td><code>{l.loan_id}</code></td>
                <td style={{ fontWeight: '600', color: '#0F172A' }}>
                  {l.customer_name} <span style={{ fontSize: '0.75rem', color: '#64748B' }}>(<code>{l.customer_id}</code>)</span>
                </td>
                <td>{l.loan_type}</td>
                <td style={{ fontWeight: '700', color: '#059669' }}>₹{l.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                <td><span className="badge badge-success">{l.approval_status}</span></td>
                <td>
                  <span className={`badge ${l.disbursement_status === 'DISBURSED' ? 'badge-success' : 'badge-pending'}`}>
                    {l.disbursement_status}
                  </span>
                </td>
                <td>
                  {l.disbursement_status === 'PENDING' ? (
                    <button onClick={() => setSelectedLoan(l)} className="btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                      Review Disbursement
                    </button>
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle size={14} /> Disbursed
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Review Disbursement Confirmation Modal */}
      {selectedLoan && (
        <div className="modal-overlay" onClick={() => setSelectedLoan(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#0F172A' }}>Review Loan Disbursement</h2>
              <button onClick={() => setSelectedLoan(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B' }}><X size={20} /></button>
            </div>

            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div><strong>Loan ID:</strong> <code>{selectedLoan.loan_id}</code></div>
              <div><strong>Customer:</strong> {selectedLoan.customer_name} (<code>{selectedLoan.customer_id}</code>)</div>
              <div><strong>Loan Amount:</strong> <span style={{ fontSize: '1.25rem', fontWeight: '800', color: '#059669' }}>₹{selectedLoan.amount?.toLocaleString('en-IN')}</span></div>
              <div><strong>Sanction Approval:</strong> {selectedLoan.approved_by}</div>
              <div><strong>System Pre-Checks:</strong> <span className="badge badge-success">✓ Approved & Verified</span></div>

              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #E2E8F0', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button onClick={() => setSelectedLoan(null)} className="btn-secondary">Cancel</button>
                <button onClick={() => handleConfirmDisbursement(selectedLoan.loan_id)} className="btn-primary">
                  Confirm Disbursement
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
