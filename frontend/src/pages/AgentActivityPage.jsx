import React, { useEffect, useState } from 'react';
import { getAuditEvents } from '../api';
import { Activity, RefreshCw, Cpu, UserCheck, ShieldCheck, Database, Play } from 'lucide-react';

export default function AgentActivityPage() {
  const [events, setEvents] = useState([]);

  const fetchEvents = async () => {
    try {
      const res = await getAuditEvents();
      setEvents(res.data);
    } catch (err) {
      console.error('Failed to load agent activity:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const agents = [
    { name: 'Orchestrator', role: 'Entry point, task routing & user response', icon: Cpu },
    { name: 'Planner', role: 'Structured execution plan breakdown', icon: Play },
    { name: 'Researcher', role: 'Vector DB RAG & SQL entity retrieval', icon: Database },
    { name: 'Executor', role: 'Explicit validated banking tool execution', icon: UserCheck },
    { name: 'Auditor', role: 'Independent execution verification', icon: ShieldCheck }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Agent Activity</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
            Technical multi-agent architecture telemetry and state transition feed for academic demonstration.
          </p>
        </div>
        <button onClick={fetchEvents} className="btn-secondary">
          <RefreshCw size={14} /> Refresh Stream
        </button>
      </div>

      {/* 5-Agent Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        {agents.map((ag, idx) => {
          const Icon = ag.icon;
          return (
            <div key={idx} className="fin-card" style={{ padding: '16px', textAlign: 'center' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px auto' }}>
                <Icon size={18} color="#2563EB" />
              </div>
              <div style={{ fontWeight: '700', fontSize: '0.875rem', color: '#0F172A' }}>{ag.name}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748B', marginTop: '2px' }}>{ag.role}</div>
            </div>
          );
        })}
      </div>

      {/* Live Agent Hop Stream */}
      <div className="fin-card">
        <h2 style={{ fontSize: '1.05rem', fontWeight: '700', color: '#0F172A', marginBottom: '16px' }}>
          Inter-Agent Hop Stream
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {events.map((ev, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              paddingBottom: '12px',
              borderBottom: idx < events.length - 1 ? '1px solid #E2E8F0' : 'none'
            }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                background: '#F1F5F9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Activity size={16} color="#2563EB" />
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className="badge badge-purple">{ev.source_agent}</span>
                    <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>→</span>
                    <span className="badge badge-blue">{ev.destination_agent}</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#64748B' }}>{ev.timestamp ? ev.timestamp.substring(11, 19) : ''}</span>
                </div>

                <p style={{ fontSize: '0.825rem', color: '#1E293B', margin: '4px 0' }}>{ev.action_summary}</p>
                <div style={{ fontSize: '0.725rem', color: '#64748B' }}>
                  Operation ID: <code>{ev.task_id}</code> | Intercept Verdict: <strong style={{ color: '#059669' }}>{ev.status}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
