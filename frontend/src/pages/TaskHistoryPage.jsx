import React, { useEffect, useState } from 'react';
import { getTasks, getTaskDetails } from '../api';
import { History, RefreshCw, Eye, X, ListChecks } from 'lucide-react';

export default function TaskHistoryPage() {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);

  const fetchTasks = async () => {
    try {
      const res = await getTasks();
      setTasks(res.data);
    } catch (err) {
      console.error('Failed to load operation history:', err);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleInspect = async (taskId) => {
    try {
      const res = await getTaskDetails(taskId);
      setSelectedTask(res.data);
    } catch (err) {
      console.error('Failed to inspect operation:', err);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Operation History</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Historical records of completed banking operations.</p>
        </div>
        <button onClick={fetchTasks} className="btn-secondary">
          <RefreshCw size={14} /> Refresh History
        </button>
      </div>

      <div className="fin-card">
        <table className="fin-table">
          <thead>
            <tr>
              <th>Operation ID</th>
              <th>Date & Time</th>
              <th>Staff</th>
              <th>Category</th>
              <th>Operation Prompt</th>
              <th>Status</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.task_id}>
                <td><code>{t.task_id}</code></td>
                <td style={{ fontSize: '0.775rem', color: '#64748B' }}>{t.created_at ? t.created_at.substring(0, 19).replace('T', ' ') : 'N/A'}</td>
                <td><span className="badge badge-gray">{t.user_id || 'EMP-1092'}</span></td>
                <td><span className="badge badge-purple">{t.task_type}</span></td>
                <td style={{ fontSize: '0.8rem', color: '#334155', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.request}</td>
                <td><span className="badge badge-success">{t.status}</span></td>
                <td>
                  <button onClick={() => handleInspect(t.task_id)} className="btn-secondary" style={{ padding: '3px 8px', fontSize: '0.75rem' }}>
                    <Eye size={12} /> Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Operation Inspector Slide-out Modal */}
      {selectedTask && (
        <div className="modal-overlay" onClick={() => setSelectedTask(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#0F172A' }}>
                Operation Details: {selectedTask.task_id}
              </h2>
              <button onClick={() => setSelectedTask(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B' }}><X size={20} /></button>
            </div>

            <div style={{ fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div><strong>Requested Instruction:</strong> "{selectedTask.request}"</div>
              <div><strong>Category:</strong> <span className="badge badge-purple">{selectedTask.task_type}</span></div>

              <div>
                <strong>Operational Procedure Steps:</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
                  {selectedTask.plan?.map((step, idx) => (
                    <div key={idx} style={{ padding: '6px 10px', background: '#F8FAFC', borderRadius: '4px', border: '1px solid #E2E8F0', fontSize: '0.775rem' }}>
                      {step}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <strong>Operation Result:</strong>
                <pre style={{ background: '#F8FAFC', padding: '12px', borderRadius: '6px', border: '1px solid #E2E8F0', marginTop: '4px', whiteSpace: 'pre-wrap', color: '#1E293B', fontSize: '0.8rem', lineHeight: '1.5' }}>
                  {selectedTask.final_result}
                </pre>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button onClick={() => setSelectedTask(null)} className="btn-secondary">Close Inspector</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
