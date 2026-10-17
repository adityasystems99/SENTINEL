import React from 'react';
import { Target, CheckCircle, AlertOctagon, HelpCircle, ArrowRight } from 'lucide-react';

export default function RootCauseCard({ incident }) {
  if (!incident || !incident.root_cause_ranking || incident.root_cause_ranking.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <HelpCircle size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
        <p style={{ fontSize: '0.85rem' }}>Select an incident to view root-cause analysis</p>
      </div>
    );
  }

  const top = incident.root_cause_ranking[0];
  const confidenceBadge =
    top.confidence === 'HIGH' ? 'badge-critical' : top.confidence === 'MEDIUM' ? 'badge-high' : 'badge-medium';

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Target size={20} color="#f87171" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Root Cause Identification</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>NetworkX Algorithmic Confidence:</span>
          <span className={`badge ${confidenceBadge}`}>{top.confidence} ({Math.round(top.score * 100)}%)</span>
        </div>
      </div>

      {/* Primary Suspect Card */}
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <div>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#f87171', fontWeight: '700' }}>
              PRIMARY SUSPECT SERVICE
            </span>
            <h4 style={{ fontSize: '1.15rem', fontWeight: '800', color: 'var(--text-primary)', marginTop: '2px' }}>
              [{top.service}]
            </h4>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Causality Score</span>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#f87171' }}>{top.score}</div>
          </div>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', background: 'rgba(0,0,0,0.3)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', fontFamily: 'var(--font-mono)' }}>
          {top.message}
        </p>

        {/* Reasons */}
        <div style={{ marginTop: '12px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
            Supporting Graph Evidence:
          </span>
          <ul style={{ listStyle: 'none', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {top.reasons.map((r, i) => (
              <li key={i} style={{ fontSize: '0.78rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f87171' }} />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended Actions */}
      {incident.recommended_actions && incident.recommended_actions.length > 0 && (
        <div style={{ background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.25)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#60a5fa', marginBottom: '6px', fontSize: '0.8rem', fontWeight: '600' }}>
            <CheckCircle size={14} />
            <span>Recommended Mitigation Action:</span>
          </div>
          {incident.recommended_actions.map((act, i) => (
            <div key={i} style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: '500' }}>
              • {act}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
