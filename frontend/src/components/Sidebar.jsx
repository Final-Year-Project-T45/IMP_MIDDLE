import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Terminal, 
  CreditCard, 
  ArrowLeftRight, 
  Landmark, 
  FileText, 
  AlertTriangle, 
  BookOpen, 
  CheckSquare, 
  History, 
  ShieldCheck, 
  Activity, 
  Layers, 
  Shield 
} from 'lucide-react';

export default function Sidebar() {
  const navMain = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Operations', path: '/operations', icon: Terminal },
    { label: 'Accounts', path: '/accounts', icon: CreditCard },
    { label: 'Transactions', path: '/transactions', icon: ArrowLeftRight },
    { label: 'Transfers', path: '/transfers', icon: Landmark },
    { label: 'Loans', path: '/loans', icon: FileText },
    { label: 'Fraud Cases', path: '/fraud-cases', icon: AlertTriangle },
    { label: 'Policy Center', path: '/policies', icon: BookOpen }
  ];

  const navWork = [
    { label: 'Pending Reviews', path: '/pending-reviews', icon: CheckSquare },
    { label: 'Operation History', path: '/operation-history', icon: History }
  ];

  const navSystem = [
    { label: 'Audit Trail', path: '/audit-trail', icon: ShieldCheck },
    { label: 'Agent Activity', path: '/agent-activity', icon: Activity },
    { label: 'Demo Scenarios', path: '/demo-scenarios', icon: Layers }
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: '#0F172A',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      color: '#94A3B8',
      flexShrink: 0
    }}>
      <div>
        {/* Brand Header */}
        <div style={{
          padding: '20px 20px 16px 20px',
          borderBottom: '1px solid #1E293B',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            background: '#2563EB',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFF'
          }}>
            <Shield size={18} />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: '800', color: '#F8FAFC', letterSpacing: '0.03em' }}>
              FINSECURE
            </div>
            <div style={{ fontSize: '0.675rem', color: '#64748B' }}>
              Banking Operations Platform
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <div style={{ padding: '12px 10px', overflowY: 'auto' }}>
          {/* Main Navigation */}
          <div style={{ padding: '4px 10px 6px 10px', fontSize: '0.675rem', fontWeight: '700', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Navigation
          </div>
          {navMain.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  marginBottom: '2px',
                  borderRadius: '6px',
                  color: isActive ? '#FFFFFF' : '#94A3B8',
                  backgroundColor: isActive ? '#2563EB' : 'transparent',
                  fontWeight: isActive ? '600' : '500',
                  textDecoration: 'none',
                  fontSize: '0.825rem',
                  transition: 'all 0.15s ease'
                })}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}

          <div style={{ height: '1px', backgroundColor: '#1E293B', margin: '10px 0' }} />

          {/* Work Queue */}
          <div style={{ padding: '4px 10px 6px 10px', fontSize: '0.675rem', fontWeight: '700', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Work Queue
          </div>
          {navWork.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  marginBottom: '2px',
                  borderRadius: '6px',
                  color: isActive ? '#FFFFFF' : '#94A3B8',
                  backgroundColor: isActive ? '#2563EB' : 'transparent',
                  fontWeight: isActive ? '600' : '500',
                  textDecoration: 'none',
                  fontSize: '0.825rem',
                  transition: 'all 0.15s ease'
                })}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}

          <div style={{ height: '1px', backgroundColor: '#1E293B', margin: '10px 0' }} />

          {/* System & Technical Demo */}
          <div style={{ padding: '4px 10px 6px 10px', fontSize: '0.675rem', fontWeight: '700', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            System & Demo
          </div>
          {navSystem.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  marginBottom: '2px',
                  borderRadius: '6px',
                  color: isActive ? '#FFFFFF' : '#94A3B8',
                  backgroundColor: isActive ? '#2563EB' : 'transparent',
                  fontWeight: isActive ? '600' : '500',
                  textDecoration: 'none',
                  fontSize: '0.825rem',
                  transition: 'all 0.15s ease'
                })}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Staff Profile Bottom Footer */}
      <div style={{
        padding: '14px 16px',
        borderTop: '1px solid #1E293B',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: '#334155',
          color: '#F8FAFC',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.7rem',
          fontWeight: '700'
        }}>
          EP
        </div>
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#F8FAFC' }}>EMP-1092</div>
          <div style={{ fontSize: '0.675rem', color: '#64748B' }}>Operations Staff</div>
        </div>
      </div>
    </aside>
  );
}
