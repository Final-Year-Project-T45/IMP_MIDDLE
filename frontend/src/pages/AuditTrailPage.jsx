import React, { useEffect, useState } from 'react';
import { getAuditEvents } from '../api';
import { ShieldCheck, RefreshCw, ShieldAlert } from 'lucide-react';

export default function AuditTrailPage() {
  const [events, setEvents] = useState([]);

  const fetchEvents = async () => {
    try {
      const res = await getAuditEvents();
      setEvents(res.data);
    } catch (err) {
      console.error('Failed to load audit events:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Audit Trail</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Operational history for completed banking activities.</p>
        </div>
        <button onClick={fetchEvents} className="btn-secondary">
          <RefreshCw size={14} /> Refresh Logs
        </button>
      </div>

      {/* Phase 1 Disclaimer Notice */}
      <div style={{
        padding: '12px 16px',
        borderRadius: '6px',
        background: '#FFFBEB',
        border: '1px solid #FDE68A',
        color: '#B45309',
        marginBottom: '20px',
        fontSize: '0.825rem',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        <ShieldAlert size={18} />
        <div>
          <strong>Phase 1 Audit Trail:</strong> Standard application event logging. Cryptographic integrity protection (Merkle audit tree) will be introduced in a later project phase.
        </div>
      </div>

      <div className="fin-card">
        <table className="fin-table">
          <thead>
            <tr>
              <th>Event ID</th>
              <th>Timestamp</th>
              <th>Operation Reference</th>
              <th>Staff / Agent</th>
              <th>Target Hop</th>
              <th>Event Type</th>
              <th>Action Summary</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.event_id}>
                <td><code>#{ev.event_id}</code></td>
                <td style={{ fontSize: '0.775rem', color: '#64748B' }}>{ev.timestamp ? ev.timestamp.substring(0, 19).replace('T', ' ') : 'N/A'}</td>
                <td><code>{ev.task_id}</code></td>
                <td><span className="badge badge-purple">{ev.source_agent}</span></td>
                <td><span className="badge badge-blue">{ev.destination_agent}</span></td>
                <td style={{ fontSize: '0.75rem', color: '#64748B' }}>{ev.event_type}</td>
                <td style={{ fontSize: '0.8rem', color: '#334155' }}>{ev.action_summary}</td>
                <td><span className="badge badge-success">{ev.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
