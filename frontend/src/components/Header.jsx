import React from 'react';
import { Activity, RefreshCw, Layers, Github } from 'lucide-react';
import SentinelLogo from './SentinelLogo';

export default function Header({ health, onRefresh, isRefreshing, activeIncidentCount }) {
  return (
    <header
      className="glass-panel"
      style={{
        padding: '16px 24px',
        marginBottom: '24px',
        border: '1px solid rgba(0, 242, 254, 0.18)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        {/* Brand & Geometric Intelligence Mark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <SentinelLogo size={42} glowing={true} animated={true} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1
                style={{
                  fontSize: '1.4rem',
                  fontWeight: '900',
                  letterSpacing: '0.04em',
                  background: 'linear-gradient(90deg, #ffffff 0%, #73D9F5 60%, #c084fc 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                SENTINEL
              </h1>
              <span
                style={{
                  fontSize: '0.72rem',
                  background: 'rgba(0, 242, 254, 0.12)',
                  color: 'var(--accent-cyan)',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontWeight: '700',
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                  letterSpacing: '0.08em',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                CYBER INTELLIGENCE
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Developer Intelligence & Causal Graph Incident Investigation
            </p>
          </div>
        </div>

        {/* Cyber Telemetry Status & Live Stats Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              background: 'rgba(6, 9, 19, 0.65)',
              padding: '7px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(115, 217, 245, 0.2)',
            }}
          >
            {/* Real-time Status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                className="pulse-dot"
                style={{
                  color: health?.status === 'ok' ? '#10b981' : '#f59e0b',
                  background: health?.status === 'ok' ? '#10b981' : '#f59e0b',
                }}
              />
              <span style={{ fontSize: '0.76rem', fontWeight: '700', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
                {health?.status === 'ok' ? 'SYSTEM OPERATIONAL' : 'SYSTEM CONNECTING'}
              </span>
            </div>

            <div style={{ width: '1px', height: '16px', background: 'var(--border)' }} />

            {/* Telemetry Events */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={15} color="#00f2fe" />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Events:</span>
              <strong style={{ fontSize: '0.86rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                {health?.total_events_stored ?? 0}
              </strong>
            </div>

            <div style={{ width: '1px', height: '16px', background: 'var(--border)' }} />

            {/* Incidents Count */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={15} color={activeIncidentCount > 0 ? '#ef4444' : '#94a3b8'} />
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Incidents:</span>
              <strong
                style={{
                  fontSize: '0.86rem',
                  color: activeIncidentCount > 0 ? '#f87171' : 'var(--text-primary)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
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
              border: '1px solid rgba(115, 217, 245, 0.25)',
              color: 'var(--text-primary)',
              padding: '8px 14px',
              borderRadius: '10px',
              fontSize: '0.82rem',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(115, 217, 245, 0.25)')}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            Refresh
          </button>

          {/* GitHub Repository Link */}
          <a
            href="https://github.com/adityasystems99/SENTINEL"
            target="_blank"
            rel="noopener noreferrer"
            title="View SENTINEL Repository on GitHub"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(0, 242, 254, 0.08)',
              border: '1px solid rgba(0, 242, 254, 0.25)',
              color: 'var(--text-primary)',
              padding: '8px 14px',
              borderRadius: '10px',
              fontSize: '0.82rem',
              fontWeight: '600',
              textDecoration: 'none',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-cyan)';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 242, 254, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(0, 242, 254, 0.25)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <Github size={15} color="var(--accent-cyan)" />
            <span>GitHub</span>
          </a>
        </div>
      </div>
    </header>
  );
}
