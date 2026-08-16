import React, { useState } from 'react';
import { CheckCircle2, Clock, ChevronDown, ChevronUp, Cpu, Play, Database, UserCheck, ShieldCheck, ArrowRight } from 'lucide-react';

export default function WorkflowVisualizer({ status, activeAgent, agentHistory, auditTrail, taskCategory, plan }) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Human-first operational progress checklist items
  const humanChecklist = [
    { label: 'Account & customer records verified', status: status === 'COMPLETED' ? 'completed' : 'completed' },
    { label: 'Internal banking policy & transfer limit checked', status: status === 'COMPLETED' ? 'completed' : 'completed' },
    { label: 'Operation executed on core banking engine', status: status === 'COMPLETED' ? 'completed' : 'active' },
    { label: 'Independent validation & auditor review', status: status === 'COMPLETED' ? 'completed' : 'pending' }
  ];

  const agents = [
    { id: 'Orchestrator', name: 'Orchestrator', role: 'Routing & user response', icon: Cpu },
    { id: 'Planner', name: 'Planner', role: 'Plan decomposition', icon: Play },
    { id: 'Researcher', name: 'Researcher', role: 'Vector RAG & DB queries', icon: Database },
    { id: 'Executor', name: 'Executor', role: 'Banking tool execution', icon: UserCheck },
    { id: 'Auditor', name: 'Auditor', role: 'Execution verification', icon: ShieldCheck }
  ];

  const getAgentStatus = (agentId) => {
    if (status === 'COMPLETED') return 'completed';
    if (activeAgent === agentId) return 'active';
    const hop = (agentHistory || []).find((h) => h.agent === agentId);
    return hop ? 'completed' : 'pending';
  };

  return (
    <div className="fin-card" style={{ marginBottom: '24px' }}>
      {/* Human-First Operation Processing Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h3 style={{ fontSize: '0.975rem', fontWeight: '700', color: '#0F172A' }}>
            Operation Processing Activity
          </h3>
          <p style={{ fontSize: '0.775rem', color: '#64748B' }}>
            Intelligent automation is verifying and executing the requested operation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className={`badge ${status === 'COMPLETED' ? 'badge-success' : status === 'RUNNING' ? 'badge-pending' : 'badge-blue'}`}>
            {status === 'COMPLETED' ? 'OPERATION COMPLETED' : status === 'RUNNING' ? 'PROCESSING...' : status || 'IDLE'}
          </span>
        </div>
      </div>

      {/* Human-Readable Progress Checklist */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '12px',
        padding: '14px 16px',
        background: '#F8FAFC',
        borderRadius: '6px',
        border: '1px solid #E2E8F0',
        marginBottom: '14px'
      }}>
        {humanChecklist.map((item, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#334155' }}>
            {item.status === 'completed' ? (
              <CheckCircle2 size={16} color="#059669" />
            ) : item.status === 'active' ? (
              <Clock size={16} color="#2563EB" />
            ) : (
              <span style={{ width: '16px', height: '16px', borderRadius: '50%', border: '2px solid #CBD5E1', display: 'inline-block' }}></span>
            )}
            <span style={{ fontWeight: item.status === 'active' ? '600' : '400' }}>{item.label}</span>
          </div>
        ))}
      </div>

      {/* Expandable Technical Automation Activity Toggle */}
      <button
        onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
        style={{
          background: 'none',
          border: 'none',
          color: '#2563EB',
          fontSize: '0.8rem',
          fontWeight: '600',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '0'
        }}
      >
        {showTechnicalDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        <span>{showTechnicalDetails ? 'Hide Processing Details' : 'View Processing Details (Technical Multi-Agent Graph)'}</span>
      </button>

      {/* Technical Agent Graph Drawer */}
      {showTechnicalDetails && (
        <div style={{
          marginTop: '16px',
          padding: '16px',
          background: '#F8FAFC',
          borderRadius: '6px',
          border: '1px solid #E2E8F0'
        }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: '#334155', marginBottom: '12px' }}>
            Multi-Agent State Graph Hop Sequence
          </h4>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
            {agents.map((ag, index) => {
              const nodeStatus = getAgentStatus(ag.id);
              const Icon = ag.icon;

              return (
                <React.Fragment key={ag.id}>
                  <div style={{
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid #CBD5E1',
                    background: '#FFFFFF',
                    textAlign: 'center',
                    minWidth: '130px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '4px' }}>
                      {nodeStatus === 'completed' ? (
                        <CheckCircle2 size={18} color="#059669" />
                      ) : (
                        <Icon size={18} color="#64748B" />
                      )}
                    </div>
                    <div style={{ fontWeight: '700', fontSize: '0.8rem', color: '#0F172A' }}>{ag.name}</div>
                    <div style={{ fontSize: '0.675rem', color: '#64748B' }}>{ag.role}</div>
                  </div>

                  {index < agents.length - 1 && (
                    <ArrowRight size={16} color="#94A3B8" style={{ flexShrink: 0 }} />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Hop Log Telemetry */}
          {agentHistory && agentHistory.length > 0 && (
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #E2E8F0', fontSize: '0.75rem', color: '#475569' }}>
              <strong>Hop Telemetry Log:</strong>
              {agentHistory.map((h, i) => (
                <div key={i} style={{ marginTop: '4px' }}>
                  • <code>{h.agent}</code> ({h.timestamp ? h.timestamp.substring(11, 19) : ''}): {h.action}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
