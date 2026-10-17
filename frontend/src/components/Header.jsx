import React from 'react';
import { ShieldAlert, Activity, RefreshCw, Cpu, Layers } from 'lucide-react';

export default function Header({ health, onRefresh, isRefreshing, activeIncidentCount }) {
  return (
    <header className="glass-panel" style={{ padding: '16px 24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.4)'
          }}>
            <ShieldAlert size={28} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: '800', letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #f0f4f8, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                SENTINEL
              </h1>
              <span style={{ fontSize: '0.75rem', background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontWeight: '600', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                DEV INTELLIGENCE
              </span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              Self-Investigating Production Engineer & Incident Correlation
            </p>
          </div>
        </div>

        {/* Stats Pill & Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(0,0,0,0.3)', padding: '6px 14px', borderRadius: '10px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={16} color="#10b981" />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Telemetry Events:</span>
              <strong style={{ fontSize: '0.88rem', color: '#10b981' }}>{health?.total_events_stored ?? 0}</strong>
            </div>
            <div style={{ width: '1px', height: '16px', background: 'var(--border)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={16} color={activeIncidentCount > 0 ? '#ef4444' : '#94a3b8'} />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Incidents:</span>
              <strong style={{ fontSize: '0.88rem', color: activeIncidentCount > 0 ? '#ef4444' : 'var(--text-primary)' }}>
                {activeIncidentCount}
              </strong>
            </div>
          </div>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '8px 14px',
              borderRadius: '8px',
              fontSize: '0.82rem',
              fontWeight: '500'
            }}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>
    </header>
  );
}
