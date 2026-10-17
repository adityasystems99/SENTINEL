import React, { useState, useEffect } from 'react';
import {
  Compass,
  ChevronLeft,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Terminal,
  Server,
  Layers,
  RefreshCw,
  AlertCircle,
  ShieldCheck,
  HelpCircle,
  ArrowRight,
  ListFilter,
  Check,
  XCircle,
} from 'lucide-react';
import { assessCompatibility, fetchCompatibilityReport } from '../../api/client';

export default function CompatibilityWorkspace({ project, onBackToDashboard }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);

  const projectId = project?.project_id;

  useEffect(() => {
    if (!projectId) return;
    loadExistingReport();
  }, [projectId]);

  async function loadExistingReport() {
    setInitialLoading(true);
    setError(null);
    try {
      const existing = await fetchCompatibilityReport(projectId);
      if (existing) {
        setReport(existing);
      }
    } catch (err) {
      console.warn('No cached compatibility report:', err);
    } finally {
      setInitialLoading(false);
    }
  }

  async function handleRunAssessment() {
    setLoading(true);
    setError(null);
    try {
      const result = await assessCompatibility(projectId);
      setReport(result);
    } catch (err) {
      setError(err.message || 'Failed to complete compatibility assessment');
    } finally {
      setLoading(false);
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'compatible':
        return (
          <span className="badge badge-low" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} /> Compatible
          </span>
        );
      case 'partially_ready':
        return (
          <span className="badge badge-medium" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={13} /> Partially Ready
          </span>
        );
      case 'needs_configuration':
        return (
          <span className="badge badge-high" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertCircle size={13} /> Needs Configuration
          </span>
        );
      default:
        return (
          <span className="badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(167, 139, 250, 0.2)', color: '#c4b5fd', border: '1px solid rgba(167, 139, 250, 0.4)' }}>
            <HelpCircle size={13} /> Unverified
          </span>
        );
    }
  };

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header Bar */}
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
              cursor: 'pointer',
            }}
          >
            <ChevronLeft size={16} /> Back to Dashboard
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(115, 217, 245, 0.15)', padding: '6px 8px', borderRadius: '8px', color: 'var(--accent)' }}>
              <Compass size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 1 — Project Compatibility & Integration Readiness
                </h2>
                <span className="badge badge-medium">Can I use it?</span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || projectId}</strong> · Safe Static Analysis Engine
              </p>
            </div>
          </div>
        </div>

        <div>
          <button
            onClick={handleRunAssessment}
            disabled={loading}
            className="btn-primary"
            style={{
              padding: '8px 18px',
              fontSize: '0.84rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
            {loading ? 'Analyzing Workspace...' : report ? 'Re-Run Assessment' : 'Run Compatibility Assessment'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            marginBottom: '24px',
            borderLeft: '4px solid #f87171',
            background: 'rgba(239, 68, 68, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={20} color="#f87171" />
            <span style={{ fontSize: '0.86rem', color: '#fca5a5' }}>{error}</span>
          </div>
          <button
            onClick={handleRunAssessment}
            style={{
              background: 'rgba(248, 113, 113, 0.2)',
              border: '1px solid rgba(248, 113, 113, 0.4)',
              color: '#fff',
              borderRadius: '6px',
              padding: '4px 10px',
              fontSize: '0.78rem',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading State */}
      {initialLoading ? (
        <div className="glass-panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <RefreshCw size={32} className="spin" color="var(--accent)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '6px' }}>Loading Compatibility Data</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Checking for existing inspection reports...</p>
        </div>
      ) : !report && !loading ? (
        /* Empty State */
        <div className="glass-panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <Compass size={48} color="var(--accent)" style={{ margin: '0 auto 16px', opacity: 0.8 }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '8px' }}>
            Workspace Ingested & Ready for Static Inspection
          </h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', maxWidth: '580px', margin: '0 auto 24px', lineHeight: '1.6' }}>
            SENTINEL will inspect file structures, entry points, package manifests, route bindings, and telemetry instrumentation without installing dependencies or executing code.
          </p>
          <button
            onClick={handleRunAssessment}
            className="btn-primary"
            style={{
              padding: '10px 24px',
              fontSize: '0.9rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
            }}
          >
            <Compass size={18} /> Start Static Compatibility Assessment
          </button>
        </div>
      ) : report ? (
        /* Completed Assessment Report */
        <div>
          {/* Status Overview Card */}
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              marginBottom: '24px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '20px',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Overall Readiness
              </span>
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                {getStatusBadge(report.overall_status)}
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  ({Math.round(report.confidence * 100)}% confidence)
                </span>
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Telemetry Readiness
              </span>
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                {report.telemetry_readiness?.status === 'ready' ? (
                  <span className="badge badge-low" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle2 size={13} /> Ready
                  </span>
                ) : report.telemetry_readiness?.status === 'partial' ? (
                  <span className="badge badge-medium" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <AlertTriangle size={13} /> Partial Instrumentation
                  </span>
                ) : (
                  <span className="badge badge-high" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <AlertCircle size={13} /> Needs Setup
                  </span>
                )}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Discovered Endpoints
              </span>
              <div style={{ marginTop: '6px', fontSize: '1.4rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                {report.detected_routes?.length || 0}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Entry Points
              </span>
              <div style={{ marginTop: '6px', fontSize: '1.4rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                {report.entry_points?.length || 0}
              </div>
            </div>
          </div>

          {/* Grid: Detected Technologies & Telemetry Readiness */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            {/* Detected Technologies */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Server size={18} color="var(--accent)" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Detected Technologies & Manifests</h3>
              </div>

              {report.detected_technologies && report.detected_technologies.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {report.detected_technologies.map((tech, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                        padding: '12px 14px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{tech.name}</strong>
                          <span className="badge" style={{ fontSize: '0.7rem', padding: '2px 6px' }}>{tech.category}</span>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          Evidence: <code>{tech.evidence_file}</code> {tech.version_hint && `(${tech.version_hint})`}
                        </div>
                      </div>
                      <span className="badge badge-low" style={{ fontSize: '0.72rem' }}>
                        {tech.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>No package manifests detected.</p>
              )}
            </div>

            {/* Telemetry Instrumentation */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Layers size={18} color="#34d399" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Telemetry & Health Instrumentation</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.84rem', color: 'var(--text-primary)' }}>OpenTelemetry Tracing SDK</span>
                  {report.telemetry_readiness?.has_opentelemetry ? (
                    <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={12} /> Detected</span>
                  ) : (
                    <span className="badge badge-high" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><XCircle size={12} /> Missing</span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.84rem', color: 'var(--text-primary)' }}>Structured Logging Hook</span>
                  {report.telemetry_readiness?.has_structured_logging ? (
                    <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={12} /> Configured</span>
                  ) : (
                    <span className="badge badge-medium" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={12} /> Unverified</span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.84rem', color: 'var(--text-primary)' }}>Liveness / Health Route (/health)</span>
                  {report.telemetry_readiness?.has_health_endpoint ? (
                    <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={12} /> Detected</span>
                  ) : (
                    <span className="badge badge-high" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><XCircle size={12} /> Missing</span>
                  )}
                </div>
              </div>

              {report.telemetry_readiness?.evidence && report.telemetry_readiness.evidence.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Evidence Locations</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                    {report.telemetry_readiness.evidence.map((ev, i) => (
                      <span key={i} style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {ev}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Grid: Endpoints & Setup Steps */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            {/* Discovered Routes */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Terminal size={18} color="var(--accent)" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Detected Routes & Entry Points</h3>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Application Entry Points</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                  {report.entry_points && report.entry_points.length > 0 ? (
                    report.entry_points.map((ep, idx) => (
                      <span key={idx} style={{ background: 'rgba(115, 217, 245, 0.1)', border: '1px solid rgba(115, 217, 245, 0.3)', color: '#73D9F5', padding: '3px 8px', borderRadius: '4px', fontSize: '0.76rem' }}>
                        {ep}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>None identified</span>
                  )}
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>API Endpoints</span>
                <div style={{ maxHeight: '200px', overflowY: 'auto', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {report.detected_routes && report.detected_routes.length > 0 ? (
                    report.detected_routes.map((rt, idx) => (
                      <div key={idx} style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '4px 10px', borderRadius: '4px', fontSize: '0.78rem', fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                        {rt}
                      </div>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>No static route annotations found</span>
                  )}
                </div>
              </div>
            </div>

            {/* Recommended Setup Steps */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <ShieldCheck size={18} color="#ffd36e" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Recommended Setup Actions</h3>
              </div>

              {report.recommended_setup_steps && report.recommended_setup_steps.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {report.recommended_setup_steps.map((step, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                      <span style={{ background: 'rgba(255, 211, 110, 0.2)', color: '#ffd36e', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: '700', flexShrink: 0 }}>
                        {idx + 1}
                      </span>
                      <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.5' }}>
                        {step}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>Project meets all standard integration prerequisites.</p>
              )}
            </div>
          </div>

          {/* Missing Prerequisites & Limitations */}
          <div className="glass-panel" style={{ padding: '20px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--text-secondary)' }}>
              <HelpCircle size={16} />
              <h4 style={{ fontSize: '0.86rem', fontWeight: '700' }}>Static Analysis Limitations & Scope</h4>
            </div>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              {report.limitations?.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}
