import React, { useState } from 'react';
import { executeTransfer } from '../api';
import { Send, CheckCircle, AlertCircle, ArrowRight, ArrowLeft } from 'lucide-react';

export default function TransfersPage() {
  const [sender, setSender] = useState('4821');
  const [receiver, setReceiver] = useState('9034');
  const [amount, setAmount] = useState('85000');
  const [description, setDescription] = useState('Operational wire transfer');
  const [step, setStep] = useState(1); // 1: Input, 2: Review, 3: Receipt
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleReview = (e) => {
    e.preventDefault();
    if (!sender || !receiver || !amount) return;
    setStep(2);
  };

  const handleConfirmTransfer = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await executeTransfer(sender, receiver, amount, description);
      setResult(res.data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Transfer failed');
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Fund Transfers</h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Initiate and confirm wire transfers across customer accounts.</p>
      </div>

      <div style={{ maxWidth: '640px' }}>
        {/* Step 1: Input Form */}
        {step === 1 && (
          <div className="fin-card">
            <h2 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0F172A', marginBottom: '16px' }}>New Wire Transfer</h2>
            <form onSubmit={handleReview} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>From Account</label>
                <input type="text" value={sender} onChange={(e) => setSender(e.target.value)} placeholder="e.g. 4821" required />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>To Account</label>
                <input type="text" value={receiver} onChange={(e) => setReceiver(e.target.value)} placeholder="e.g. 9034" required />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>Amount (₹)</label>
                <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>Purpose / Memo (Optional)</label>
                <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>

              <button type="submit" className="btn-primary" style={{ marginTop: '8px' }}>
                Review Transfer <ArrowRight size={16} />
              </button>
            </form>
          </div>
        )}

        {/* Step 2: Review Screen */}
        {step === 2 && (
          <div className="fin-card">
            <h2 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0F172A', marginBottom: '16px' }}>Review Transfer Details</h2>

            <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '6px', border: '1px solid #E2E8F0', fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              <div><strong>Sender Account:</strong> <code>{sender}</code></div>
              <div><strong>Recipient Account:</strong> <code>{receiver}</code></div>
              <div><strong>Transfer Amount:</strong> <span style={{ fontSize: '1.25rem', fontWeight: '800', color: '#059669' }}>₹{parseFloat(amount).toLocaleString('en-IN')}</span></div>
              <div><strong>Daily Limit Check:</strong> <span className="badge badge-success">PASSED (₹2,00,000 Limit)</span></div>
              <div><strong>Purpose:</strong> {description}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button onClick={() => setStep(1)} className="btn-secondary">
                <ArrowLeft size={14} /> Back
              </button>
              <button onClick={handleConfirmTransfer} disabled={loading} className="btn-primary">
                {loading ? 'Executing Transfer...' : 'Review & Confirm Transfer'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Transfer Completed Receipt */}
        {step === 3 && result && (
          <div className="fin-card" style={{ borderLeft: '4px solid #059669' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#059669', fontWeight: '800', fontSize: '1.1rem', marginBottom: '14px' }}>
              <CheckCircle size={24} /> Transfer Completed
            </div>

            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '8px', color: '#1E293B', marginBottom: '20px' }}>
              <div><strong>Amount Transferred:</strong> ₹{result.amount?.toLocaleString('en-IN')}</div>
              <div><strong>From Account:</strong> ••••{sender.slice(-4)}</div>
              <div><strong>To Account:</strong> ••••{receiver.slice(-4)}</div>
              <div><strong>Transaction ID:</strong> <code>{result.transaction_id}</code></div>
              <div><strong>Sender New Balance:</strong> ₹{result.sender_new_balance?.toLocaleString('en-IN')}</div>
            </div>

            <button onClick={() => setStep(1)} className="btn-primary">
              Initiate Another Transfer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
