import React, { useEffect, useState } from 'react';
import { getPolicies, searchPolicies } from '../api';
import { BookOpen, Search, Sparkles } from 'lucide-react';

export default function PolicyCenterPage() {
  const [policies, setPolicies] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    async function loadPolicies() {
      try {
        const res = await getPolicies();
        setPolicies(res.data);
      } catch (err) {
        console.error('Failed to load policies:', err);
      }
    }
    loadPolicies();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      const res = await searchPolicies(searchQuery);
      setSearchResults(res.data);
    } catch (err) {
      console.error('Policy search failed:', err);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#0F172A' }}>Policy Center</h1>
        <p style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>Search, review, and summarize internal banking compliance policies.</p>
      </div>

      {/* Search Input Bar */}
      <div className="fin-card" style={{ marginBottom: '24px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search policy topic (e.g. retail transfer limit, account freeze protocol, loan sanction rules)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '36px' }}
            />
          </div>
          <button type="submit" className="btn-primary">
            <Sparkles size={15} /> Summarize Policy
          </button>
        </form>
      </div>

      {/* Search Results */}
      {searchResults && (
        <div style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A', marginBottom: '12px' }}>
            Policy Summary Search Results ({searchResults.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {searchResults.map((r, idx) => (
              <div key={idx} className="fin-card" style={{ borderLeft: '4px solid #2563EB' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#2563EB' }}>{r.title}</h3>
                  <span className="badge badge-blue">Relevance: {r.relevance_score}</span>
                </div>
                <pre style={{ fontSize: '0.825rem', color: '#334155', whiteSpace: 'pre-wrap', fontFamily: 'inherit', lineHeight: '1.6' }}>{r.content}</pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* List of Policies */}
      <h2 style={{ fontSize: '1rem', fontWeight: '700', color: '#0F172A', marginBottom: '12px' }}>
        Indexed Operational Policies ({policies.length})
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {policies.map((p, idx) => (
          <div key={idx} className="fin-card" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOpen size={20} color="#2563EB" />
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.875rem', color: '#0F172A' }}>{p.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B' }}>Document ID: <code>{p.id}</code></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
