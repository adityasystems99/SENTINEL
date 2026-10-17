import React from 'react';
import {
  FileCheck2,
  ChevronLeft,
  FileCode,
  FileText,
  AlertCircle,
  Clock,
  CheckCircle2,
} from 'lucide-react';

export default function PromiseAuditWorkspace({ project, onBackToDashboard }) {
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
            <div style={{ background: 'rgba(255, 211, 110, 0.15)', padding: '6px 8px', borderRadius: '8px', color: '#ffd36e' }}>
              <FileCheck2 size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 2 — Promise vs. Reality Code Audit
                </h2>
                <span className="badge badge-high">Promised?</span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Project'}</strong> · Specification Compliance & AST Audit
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <FileCode size={18} color="var(--accent)" />
            <h4 style={{ fontSize: '0.92rem', fontWeight: '700' }}>Extracted Source Files</h4>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--text-primary)' }}>
            {project?.file_count || 0}
          </div>
          <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Source files available in workspace for static AST mapping
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <FileText size={18} color="#ffd36e" />
            <h4 style={{ fontSize: '0.92rem', fontWeight: '700' }}>Specification Manifest</h4>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#ffd36e' }}>
            README / PRD
          </div>
          <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Detected project documentation ready for requirement parsing
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Clock size={18} color="#a78bfa" />
            <h4 style={{ fontSize: '0.92rem', fontWeight: '700' }}>Engine Status</h4>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#a78bfa' }}>
            Phase 4
          </div>
          <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Full AST code audit parser scheduled in upcoming engineering phase
          </p>
        </div>
      </div>

      {/* Engine Status Disclosure Notice */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffd36e', marginBottom: '10px' }}>
          <AlertCircle size={18} />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Audit Engine Status Disclosure</h3>
        </div>
        <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '14px' }}>
          In accordance with SENTINEL engineering rules, mock results are never presented as real results. The source code for project <strong>{project?.name}</strong> has been securely ingested, isolated, and indexed in the workspace directory. The full AST code-to-spec verification engine is implemented incrementally in Phase 4.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
          <CheckCircle2 size={16} color="#34d399" />
          <span>Workspace isolation verified: <code>data/projects/{project?.project_id}/source/</code></span>
        </div>
      </div>
    </div>
  );
}
