import React from 'react';
import { AlertCircle, ChevronRight, ShieldCheck } from 'lucide-react';

export default function IncidentList({ incidents, selectedId, onSelect, onAnalyze, isAnalyzing }) {
  return (
    <div className="glass-panel" style={{ padding: '20px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700' }}>Active Incidents</h3>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          style={{
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            border: 'none',
            color: '#fff',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontWeight: '600',
            boxShadow: '0 2px 10px rgba(59,130,246,0.3)'
          }}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Now'}
        </button>
      </div>

      {incidents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px 12px', color: 'var(--text-muted)' }}>
          <ShieldCheck size={36} color="#10b981" style={{ margin: '0 auto 10px', opacity: 0.8 }} />
          <p style={{ fontSize: '0.85rem', fontWeight: '500' }}>No incidents detected</p>
          <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>
            System healthy. Use the failure harness above to inject chaos.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {incidents.map((inc) => {
            const isSelected = inc.incident_id === selectedId;
            const badgeClass = inc.severity === 'CRITICAL' ? 'badge-critical' : inc.severity === 'HIGH' ? 'badge-high' : 'badge-medium';

            return (
              <div
                key={inc.incident_id}
                onClick={() => onSelect(inc.incident_id)}
                style={{
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: isSelected ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid var(--border)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: isSelected ? '0 0 16px rgba(59, 130, 246, 0.2)' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <span className={`badge ${badgeClass}`}>{inc.severity}</span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {new Date(inc.detected_at * 1000).toLocaleTimeString()}
                  </span>
                </div>

                <div style={{ fontSize: '0.82rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {inc.title}
                </div>

                {inc.top_suspect_service && (
                  <div style={{ fontSize: '0.75rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <AlertCircle size={12} />
                    <span>Suspect: [{inc.top_suspect_service}]</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
