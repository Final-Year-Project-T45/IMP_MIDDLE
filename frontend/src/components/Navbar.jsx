import React from 'react';
import { Search, UserCheck, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  return (
    <header style={{
      height: '60px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #E2E8F0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 36px',
      zIndex: 10
    }}>
      {/* Search Bar */}
      <div style={{ position: 'relative', width: '380px' }}>
        <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px', top: '10px' }} />
        <input
          type="text"
          placeholder="Search accounts, customer ID, transactions, or policy..."
          style={{
            width: '100%',
            padding: '7px 12px 7px 36px',
            borderRadius: '6px',
            border: '1px solid #E2E8F0',
            background: '#F8FAFC',
            fontSize: '0.825rem',
            color: '#0F172A',
            outline: 'none'
          }}
        />
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* System Operational Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '0.775rem',
          color: '#047857',
          fontWeight: '600',
          background: '#ECFDF5',
          padding: '4px 10px',
          borderRadius: '20px',
          border: '1px solid #A7F3D0'
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981' }}></span>
          <span>System Operational</span>
        </div>

        {/* Staff Profile */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 12px',
          borderRadius: '6px',
          background: '#F8FAFC',
          border: '1px solid #E2E8F0'
        }}>
          <div style={{
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            background: '#2563EB',
            color: '#FFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: '700'
          }}>
            EP
          </div>
          <div>
            <div style={{ fontSize: '0.825rem', fontWeight: '700', color: '#0F172A', lineHeight: '1.1' }}>
              EMP-1092
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>
              Operations Staff
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
