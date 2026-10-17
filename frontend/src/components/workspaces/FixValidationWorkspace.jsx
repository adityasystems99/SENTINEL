import React from 'react';
import {
  RotateCcw,
  ChevronLeft,
  CheckCircle2,
  Clock,
  FlaskConical,
  Activity,
  AlertCircle,
} from 'lucide-react';

export default function FixValidationWorkspace({ project, onBackToDashboard }) {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={onBackToDashboard}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-secondary)',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
            }}
          >
            <ChevronLeft size={16} /> Back to Dashboard
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(52, 211, 153, 0.15)', padding: '6px 8px', borderRadius: '8px', color: '#34d399' }}>
              <RotateCcw size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 5 — Replay Lab & Fix Validation
                </h2>
                <span className="badge badge-low">Does my fix work?</span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Project'}</strong> · Before/After Telemetry Differential
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Methodology */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <FlaskConical size={18} color="#34d399" />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Controlled Fix Verification Methodology</h3>
        </div>
        <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '18px' }}>
          SENTINEL validates bug fixes by replaying the exact failure scenario in an isolated sandbox, comparing application telemetry before and after the fix, and generating a statistical recovery verdict:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px' }}>
            <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#f87171', marginBottom: '6px' }}>
              1. Pre-Fix Baseline Run
            </div>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
              Replays incident trigger; records baseline error counts, stack traces, and p95 response latencies.
            </p>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px' }}>
            <div style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--accent)', marginBottom: '6px' }}>
              2. Candidate Patch Sandbox
            </div>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
              Applies developer fix in an isolated test environment without altering production code.
            </p>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.35)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px' }}>
            <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#34d399', marginBottom: '6px' }}>
              3. Telemetry Delta Verdict
            </div>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
              Verifies zero regressions and issues verdict: <code>SUPPORTED</code>, <code>UNSUPPORTED</code>, or <code>INCONCLUSIVE</code>.
            </p>
          </div>
        </div>
      </div>

      {/* Engine Status Notice */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399', marginBottom: '8px' }}>
          <CheckCircle2 size={18} />
          <h4 style={{ fontSize: '0.92rem', fontWeight: '700' }}>Replay Lab Architecture Status</h4>
        </div>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
          Failure reproduction can be demonstrated live in Feature 3 using the failure injection harness (`db_pool_exhaustion`, `recover`). Automated patch diffing is scheduled for Phase 6.
        </p>
      </div>
    </div>
  );
}
