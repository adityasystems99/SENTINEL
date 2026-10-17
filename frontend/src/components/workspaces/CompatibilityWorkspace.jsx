import React from 'react';
import {
  Compass,
  ChevronLeft,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Terminal,
  Server,
  Layers,
} from 'lucide-react';

export default function CompatibilityWorkspace({ project, onBackToDashboard }) {
  const frameworks = project?.detected_frameworks || [];
  const hasPython = frameworks.includes('Python');
  const hasNode = frameworks.includes('Node.js');
  const hasDocker = frameworks.includes('Docker');

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
                Project: <strong>{project?.name || 'Active Project'}</strong> · Tech Stack & Instrumentation Inspector
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Detected Tech Stack */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Server size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Detected Technologies</h3>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
            {frameworks.length > 0 ? (
              frameworks.map((f) => (
                <span
                  key={f}
                  style={{
                    background: 'rgba(115, 217, 245, 0.12)',
                    border: '1px solid rgba(115, 217, 245, 0.3)',
                    color: 'var(--text-primary)',
                    padding: '6px 14px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                  }}
                >
                  {f}
                </span>
              ))
            ) : (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Generic / Unspecified runtime
              </span>
            )}
          </div>

          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
            SENTINEL automatically scans manifest files (<code>package.json</code>, <code>requirements.txt</code>, <code>pyproject.toml</code>, <code>Dockerfile</code>) to identify languages, frameworks, and runtime constraints.
          </p>
        </div>

        {/* Telemetry Integration Checklist */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Layers size={18} color="#34d399" />
            <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Telemetry Readiness Checklist</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              <CheckCircle2 size={16} color="#34d399" style={{ marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.85rem' }}>HTTP Telemetry Ingestion Endpoint</strong>
                <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                  Backend is ready to receive JSON spans and logs at <code>POST /api/telemetry/ingest</code>.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              <CheckCircle2 size={16} color="#34d399" style={{ marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.85rem' }}>Isolated Workspace Storage</strong>
                <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                  Source files are isolated and separated from telemetry records.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
              <AlertTriangle size={16} color="#ffd36e" style={{ marginTop: '2px' }} />
              <div>
                <strong style={{ fontSize: '0.85rem' }}>OpenTelemetry / Trace SDK Instrumentation</strong>
                <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                  Ensure your application attaches <code>trace_id</code> and <code>span_id</code> to outgoing calls.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Code Snippet */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Terminal size={18} color="var(--accent)" />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Recommended Instrumentation Hook</h3>
        </div>

        <pre
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid var(--border)',
            padding: '16px',
            borderRadius: '10px',
            fontSize: '0.82rem',
            color: '#73D9F5',
            overflowX: 'auto',
          }}
        >
{`// Example: Emitting telemetry events to SENTINEL
fetch('http://localhost:8000/api/telemetry/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    events: [{
      service: '${project?.name || "my-service"}',
      level: 'INFO',
      event_type: 'trace',
      message: 'Request processed successfully',
      trace_id: 'tr-abc123',
      span_id: 'sp-001'
    }]
  })
});`}
        </pre>
      </div>
    </div>
  );
}
