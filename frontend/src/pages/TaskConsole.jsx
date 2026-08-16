import React, { useState } from 'react';
import { executeTask } from '../api';
import QuickActions from '../components/QuickActions';
import WorkflowVisualizer from '../components/WorkflowVisualizer';
import { Play, CheckCircle, AlertCircle, ShieldCheck, ListChecks, HelpCircle } from 'lucide-react';

export default function TaskConsole() {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [taskResult, setTaskResult] = useState(null);
  const [error, setError] = useState(null);

  const handleExecute = async (inputPrompt) => {
    const targetPrompt = inputPrompt || prompt;
    if (!targetPrompt.trim()) return;

    setIsLoading(true);
    setError(null);
    setTaskResult(null);

    try {
      const response = await executeTask(targetPrompt);
      setTaskResult(response.data);
    } catch (err) {
      console.error('Operation execution error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to complete banking operation.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>
          Operations
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
          Complete banking tasks using the tools available to your role.
        </p>
      </div>

      {/* Main Command Input Box */}
      <div className="fin-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem', fontWeight: '700', color: '#334155', marginBottom: '10px' }}>
          <HelpCircle size={16} color="#2563EB" />
          <span>Need help with an operation?</span>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
            placeholder="Ask FinSecure to find an account, review a transaction, prepare a transfer, or retrieve a policy..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '11px 14px',
              borderRadius: '6px',
              border: '1px solid #CBD5E1',
              fontSize: '0.875rem',
              color: '#0F172A',
              outline: 'none'
            }}
          />
          <button
            onClick={() => handleExecute()}
            disabled={isLoading || !prompt.trim()}
            className="btn-primary"
          >
            <Play size={15} />
            <span>{isLoading ? 'Processing Operation...' : 'Run Operation'}</span>
          </button>
        </div>

        {/* Quick Operational Shortcuts */}
        <QuickActions
          onSelectAction={(p) => {
            setPrompt(p);
            handleExecute(p);
          }}
          disabled={isLoading}
        />
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ padding: '14px 18px', borderRadius: '6px', background: '#FEF2F2', border: '1px solid #FCA5A5', color: '#B91C1C', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.875rem' }}>
          <AlertCircle size={18} />
          <div><strong>Operation Could Not Be Completed:</strong> {error}</div>
        </div>
      )}

      {/* Operation Processing Visualizer */}
      {(isLoading || taskResult) && (
        <WorkflowVisualizer
          status={isLoading ? 'RUNNING' : taskResult ? 'COMPLETED' : 'IDLE'}
          activeAgent={isLoading ? 'Researcher' : 'Auditor'}
          agentHistory={taskResult?.agent_history || []}
          auditTrail={taskResult?.audit_trail || []}
          taskCategory={taskResult?.task_category}
          plan={taskResult?.plan}
        />
      )}

      {/* Operation Output */}
      {taskResult && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Left: Operation Result */}
          <div className="fin-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <CheckCircle size={18} color="#059669" />
              <h2 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A' }}>Operation Result</h2>
            </div>

            <div style={{
              background: '#F8FAFC',
              padding: '16px',
              borderRadius: '6px',
              border: '1px solid #E2E8F0',
              fontSize: '0.875rem',
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
              color: '#1E293B',
              marginBottom: '16px'
            }}>
              {taskResult.final_result}
            </div>

            {/* Auditor Verification */}
            <div style={{ padding: '12px', borderRadius: '6px', background: '#ECFDF5', border: '1px solid #A7F3D0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: '700', color: '#047857' }}>
                <ShieldCheck size={16} /> Audit Verification Summary
              </div>
              <p style={{ fontSize: '0.75rem', color: '#475569', marginTop: '4px' }}>
                {taskResult.audit_result?.validation_summary}
              </p>
            </div>
          </div>

          {/* Right: Operational Steps */}
          <div className="fin-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <ListChecks size={18} color="#2563EB" />
              <h2 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A' }}>Operational Procedure Steps</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {taskResult.plan?.map((step, idx) => (
                <div key={idx} style={{
                  padding: '9px 12px',
                  background: '#F8FAFC',
                  borderRadius: '6px',
                  border: '1px solid #E2E8F0',
                  fontSize: '0.8rem',
                  color: '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span className="badge badge-blue" style={{ fontSize: '0.65rem' }}>Step {idx + 1}</span>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
