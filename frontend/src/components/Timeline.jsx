import React from 'react';
import { Clock, AlertTriangle, Info, Terminal } from 'lucide-react';

export default function Timeline({ nodes = [] }) {
  if (!nodes || nodes.length === 0) {
    return null;
  }

  // Sort chronologically
  const sorted = [...nodes].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
        <Clock size={18} color="#06b6d4" />
        <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Chronological Event Stream</h3>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '340px', overflowY: 'auto' }}>
        {sorted.map((ev, i) => {
          const isError = ev.is_error;
          const isDeploy = ev.event_type === 'deployment';
          const icon = isError ? <AlertTriangle size={14} color="#ef4444" /> : isDeploy ? <Terminal size={14} color="#f59e0b" /> : <Info size={14} color="#3b82f6" />;

          return (
            <div
              key={ev.id || i}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: '8px',
                background: isError ? 'rgba(239, 68, 68, 0.05)' : isDeploy ? 'rgba(245, 158, 11, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                border: isError ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid var(--border)',
              }}
            >
              <div style={{ marginTop: '2px' }}>{icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <strong style={{ fontSize: '0.8rem', color: isError ? '#f87171' : 'var(--text-primary)' }}>
                      [{ev.service}]
                    </strong>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {ev.event_type}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                  {ev.message}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
