import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  ChevronLeft,
  FileCode,
  FileText,
  AlertCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  Upload,
  RefreshCw,
  Search,
  ArrowRight,
  Filter,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { runAudit, runAuditWithFile, fetchAuditReport } from '../../api/client';

export default function PromiseAuditWorkspace({ project, onBackToDashboard }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);

  // Input form state
  const [mode, setMode] = useState('text'); // 'text' | 'file' | 'auto'
  const [requirementsText, setRequirementsText] = useState('');
  const [acceptanceCriteria, setAcceptanceCriteria] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [expandedSnippet, setExpandedSnippet] = useState({});

  const projectId = project?.project_id;

  useEffect(() => {
    if (!projectId) return;
    loadExistingAudit();
  }, [projectId]);

  async function loadExistingAudit() {
    setInitialLoading(true);
    setError(null);
    try {
      const existing = await fetchAuditReport(projectId);
      if (existing) {
        setReport(existing);
      }
    } catch (err) {
      console.warn('No cached audit report:', err);
    } finally {
      setInitialLoading(false);
    }
  }

  async function handleExecuteAudit() {
    setError(null);
    setLoading(true);

    try {
      let result;
      if (mode === 'file') {
        if (!selectedFile) {
          throw new Error('Please select a requirements document (.md, .txt, .json, .yaml)');
        }
        result = await runAuditWithFile(projectId, selectedFile, acceptanceCriteria);
      } else if (mode === 'auto') {
        result = await runAudit(projectId, '', acceptanceCriteria, true);
      } else {
        if (!requirementsText.trim()) {
          throw new Error('Please enter requirements text or select auto-detect / file upload.');
        }
        result = await runAudit(projectId, requirementsText, acceptanceCriteria, false);
      }
      setReport(result);
    } catch (err) {
      setError(err.message || 'Audit execution failed');
    } finally {
      setLoading(false);
    }
  }

  const toggleSnippet = (reqId) => {
    setExpandedSnippet((prev) => ({
      ...prev,
      [reqId]: !prev[reqId],
    }));
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'implemented':
        return (
          <span className="badge badge-low" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} /> Implemented
          </span>
        );
      case 'partially_implemented':
        return (
          <span className="badge badge-medium" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={13} /> Partially Implemented
          </span>
        );
      case 'missing':
        return (
          <span className="badge badge-critical" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <XCircle size={13} /> Missing
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

  const getPriorityBadge = (prio) => {
    switch (prio) {
      case 'CRITICAL':
        return <span className="badge badge-critical">Critical</span>;
      case 'HIGH':
        return <span className="badge badge-high">High</span>;
      case 'MEDIUM':
        return <span className="badge badge-medium">Medium</span>;
      default:
        return <span className="badge badge-low">Low</span>;
    }
  };

  const filteredFindings = report?.findings?.filter((f) => {
    if (activeFilter === 'all') return true;
    return f.status === activeFilter;
  }) || [];

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
                Project: <strong>{project?.name || projectId}</strong> · Specification Compliance & AST Inspection
              </p>
            </div>
          </div>
        </div>

        {report && (
          <button
            onClick={() => setReport(null)}
            className="btn-secondary"
            style={{
              padding: '8px 16px',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} /> New Audit
          </button>
        )}
      </div>

      {/* Error Banner */}
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
            onClick={() => setError(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fca5a5',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Initial Loading */}
      {initialLoading ? (
        <div className="glass-panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <RefreshCw size={32} className="spin" color="#ffd36e" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '6px' }}>Loading Audit Records</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>Retrieving existing specification findings...</p>
        </div>
      ) : !report ? (
        /* Requirements Submission Form */
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: '700', marginBottom: '6px' }}>
              Compare Requirements Against Real Source Code
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Submit a requirements document, user stories, or feature checklist. SENTINEL parses each item and checks concrete AST implementations, stubs, and tests across your isolated workspace.
            </p>
          </div>

          {/* Mode Switcher */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <button
              onClick={() => setMode('text')}
              style={{
                background: mode === 'text' ? 'rgba(255, 211, 110, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                border: mode === 'text' ? '1px solid #ffd36e' : '1px solid var(--border)',
                color: mode === 'text' ? '#ffd36e' : 'var(--text-secondary)',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '0.84rem',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <FileText size={15} /> Paste Requirements Text
            </button>
            <button
              onClick={() => setMode('file')}
              style={{
                background: mode === 'file' ? 'rgba(255, 211, 110, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                border: mode === 'file' ? '1px solid #ffd36e' : '1px solid var(--border)',
                color: mode === 'file' ? '#ffd36e' : 'var(--text-secondary)',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '0.84rem',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Upload size={15} /> Upload Spec Document
            </button>
            <button
              onClick={() => setMode('auto')}
              style={{
                background: mode === 'auto' ? 'rgba(255, 211, 110, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                border: mode === 'auto' ? '1px solid #ffd36e' : '1px solid var(--border)',
                color: mode === 'auto' ? '#ffd36e' : 'var(--text-secondary)',
                borderRadius: '8px',
                padding: '8px 16px',
                fontSize: '0.84rem',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Search size={15} /> Auto-Detect From Workspace
            </button>
          </div>

          {/* Form Content by Mode */}
          {mode === 'text' && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
                Requirements Specification (Markdown, Bullet Points, or PRD)
              </label>
              <textarea
                rows={10}
                value={requirementsText}
                onChange={(e) => setRequirementsText(e.target.value)}
                placeholder={`Example:\n\n# User Authentication\n- Must hash passwords with sha256 algorithms\n- Must issue secure session tokens\n\n# Stripe Payment Gateway\n- Must process credit card payments via Stripe SDK\n\n# Cloud Infrastructure\n- Must maintain 99.99% high availability SLA`}
                style={{
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  padding: '12px 14px',
                  fontFamily: 'monospace',
                  fontSize: '0.82rem',
                  lineHeight: '1.6',
                  resize: 'vertical',
                }}
              />
            </div>
          )}

          {mode === 'file' && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
                Upload Requirements Document (.md, .txt, .json, .yaml, .rst)
              </label>
              <div
                style={{
                  border: '2px dashed var(--border)',
                  borderRadius: '10px',
                  padding: '30px 20px',
                  textAlign: 'center',
                  background: 'rgba(0, 0, 0, 0.2)',
                }}
              >
                <FileCode size={36} color="#ffd36e" style={{ margin: '0 auto 12px', opacity: 0.8 }} />
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  {selectedFile ? (
                    <strong style={{ color: 'var(--accent)' }}>{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</strong>
                  ) : (
                    'Select a markdown specification or requirements file to inspect'
                  )}
                </p>
                <input
                  type="file"
                  id="spec-file-input"
                  accept=".md,.txt,.json,.yaml,.yml,.rst,.csv"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  onClick={() => document.getElementById('spec-file-input').click()}
                  className="btn-secondary"
                  style={{ padding: '8px 18px', fontSize: '0.82rem' }}
                >
                  {selectedFile ? 'Change File' : 'Browse Document'}
                </button>
              </div>
            </div>
          )}

          {mode === 'auto' && (
            <div
              style={{
                background: 'rgba(255, 211, 110, 0.05)',
                border: '1px solid rgba(255, 211, 110, 0.2)',
                borderRadius: '8px',
                padding: '20px',
                marginBottom: '20px',
              }}
            >
              <h4 style={{ fontSize: '0.92rem', fontWeight: '700', color: '#ffd36e', marginBottom: '6px' }}>
                Automatic Workspace Document Discovery
              </h4>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.5' }}>
                SENTINEL will automatically scan the project workspace for specification manifests like <code>README.md</code>, <code>SPEC.md</code>, <code>PRD.md</code>, or <code>REQUIREMENTS.md</code> and parse their requirement items.
              </p>
            </div>
          )}

          {/* Acceptance Criteria (Optional) */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
              Optional Acceptance Criteria / Guardrails
            </label>
            <input
              type="text"
              value={acceptanceCriteria}
              onChange={(e) => setAcceptanceCriteria(e.target.value)}
              placeholder="e.g. All API endpoints must return structured JSON errors with HTTP status codes"
              style={{
                width: '100%',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                padding: '10px 14px',
                fontSize: '0.84rem',
              }}
            />
          </div>

          <button
            onClick={handleExecuteAudit}
            disabled={loading}
            className="btn-primary"
            style={{
              padding: '10px 24px',
              fontSize: '0.9rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            {loading ? 'Performing AST Audit...' : 'Run Promise vs. Reality Audit'}
          </button>
        </div>
      ) : (
        /* Completed Audit Report View */
        <div>
          {/* Compliance Scoreboard */}
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              marginBottom: '24px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Compliance Score
              </span>
              <div style={{ fontSize: '2.2rem', fontWeight: '800', color: report.compliance_score >= 70 ? '#34d399' : report.compliance_score >= 40 ? '#ffd36e' : '#f87171', marginTop: '4px' }}>
                {report.compliance_score}%
              </div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {report.source_spec}
              </span>
            </div>

            <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
              <span style={{ fontSize: '0.74rem', color: '#34d399', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={13} /> Implemented
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {report.implemented_count}
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Satisfied with logic</span>
            </div>

            <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
              <span style={{ fontSize: '0.74rem', color: '#ffd36e', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <AlertTriangle size={13} /> Partially Done
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {report.partially_implemented_count}
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Stubs or placeholders</span>
            </div>

            <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
              <span style={{ fontSize: '0.74rem', color: '#f87171', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <XCircle size={13} /> Missing
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {report.missing_count}
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>No code found</span>
            </div>

            <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '16px' }}>
              <span style={{ fontSize: '0.74rem', color: '#c4b5fd', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <HelpCircle size={13} /> Unverified
              </span>
              <div style={{ fontSize: '1.6rem', fontWeight: '700', color: 'var(--text-primary)', marginTop: '2px' }}>
                {report.unverified_count}
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Static limits / SLA</span>
            </div>
          </div>

          {/* Filter Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              {[
                { id: 'all', label: `All (${report.total_requirements})` },
                { id: 'implemented', label: `Implemented (${report.implemented_count})` },
                { id: 'partially_implemented', label: `Partial (${report.partially_implemented_count})` },
                { id: 'missing', label: `Missing (${report.missing_count})` },
                { id: 'unverified', label: `Unverified (${report.unverified_count})` },
              ].map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => setActiveFilter(btn.id)}
                  style={{
                    background: activeFilter === btn.id ? 'rgba(255, 255, 255, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border)',
                    color: activeFilter === btn.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                    borderRadius: '6px',
                    padding: '5px 12px',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                  }}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {/* Findings List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '28px' }}>
            {filteredFindings.map((finding) => (
              <div
                key={finding.requirement_id}
                className="glass-panel"
                style={{
                  padding: '20px',
                  borderLeft:
                    finding.status === 'implemented'
                      ? '4px solid #34d399'
                      : finding.status === 'partially_implemented'
                      ? '4px solid #ffd36e'
                      : finding.status === 'missing'
                      ? '4px solid #f87171'
                      : '4px solid #a78bfa',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                        {finding.requirement_id}
                      </span>
                      <h4 style={{ fontSize: '0.98rem', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
                        {finding.title}
                      </h4>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
                      {finding.description}
                    </p>
                  </div>
                  <div>
                    {getStatusBadge(finding.status)}
                  </div>
                </div>

                {/* Evidence & Reasoning */}
                <div style={{ background: 'rgba(0, 0, 0, 0.25)', borderRadius: '8px', padding: '12px', margin: '12px 0' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.78rem' }}>
                    <div>
                      <strong style={{ color: 'var(--text-secondary)' }}>Analysis Reasoning:</strong>
                      <p style={{ margin: '4px 0 0', color: 'var(--text-primary)' }}>{finding.reasoning}</p>
                    </div>
                    <div>
                      <strong style={{ color: 'var(--text-secondary)' }}>Recommended Next Action:</strong>
                      <p style={{ margin: '4px 0 0', color: 'var(--accent)' }}>{finding.recommended_next_action}</p>
                    </div>
                  </div>
                </div>

                {/* Supporting Code Locations */}
                {finding.supporting_files && finding.supporting_files.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        Supporting Files ({finding.supporting_files.length})
                      </span>
                      <button
                        onClick={() => toggleSnippet(finding.requirement_id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--accent)',
                          fontSize: '0.74rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        {expandedSnippet[finding.requirement_id] ? (
                          <>Hide Code <ChevronUp size={12} /></>
                        ) : (
                          <>View Code <ChevronDown size={12} /></>
                        )}
                      </button>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                      {finding.supporting_files.map((loc, i) => (
                        <span key={i} style={{ background: 'rgba(115, 217, 245, 0.08)', border: '1px solid rgba(115, 217, 245, 0.2)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.74rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                          {loc.file_path} {loc.line_start ? `:L${loc.line_start}-${loc.line_end}` : ''}
                        </span>
                      ))}
                    </div>

                    {expandedSnippet[finding.requirement_id] && finding.supporting_files[0]?.snippet && (
                      <pre
                        style={{
                          background: 'rgba(0, 0, 0, 0.4)',
                          border: '1px solid var(--border)',
                          padding: '12px',
                          borderRadius: '6px',
                          fontSize: '0.76rem',
                          color: '#73D9F5',
                          overflowX: 'auto',
                          marginTop: '8px',
                          lineHeight: '1.4',
                        }}
                      >
                        {finding.supporting_files[0].snippet}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Prioritized Remaining Work List (Roadmap) */}
          {report.prioritized_roadmap && report.prioritized_roadmap.length > 0 && (
            <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Clock size={18} color="#ffd36e" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>
                  Prioritized Implementation Roadmap ({report.prioritized_roadmap.length} items)
                </h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {report.prioritized_roadmap.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {getPriorityBadge(item.priority)}
                      <div>
                        <strong style={{ fontSize: '0.86rem', color: 'var(--text-primary)' }}>
                          {item.title}
                        </strong>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '2px 0 0' }}>
                          {item.action}
                        </p>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Est. Effort: <strong>{item.estimated_effort}</strong>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis Limitations */}
          <div className="glass-panel" style={{ padding: '20px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--text-secondary)' }}>
              <HelpCircle size={16} />
              <h4 style={{ fontSize: '0.86rem', fontWeight: '700' }}>Audit Verification Limitations</h4>
            </div>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              {report.limitations?.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
