import React, { useState } from 'react';
import {
  BookOpen,
  FileText,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldAlert,
  Search,
  Sparkles,
  Layers,
} from 'lucide-react';

export default function HistoricalIntelligencePanel({ intelligence }) {
  const [activeTab, setActiveTab] = useState('evidence'); // 'evidence' | 'synthesis'
  const [expandedChunk, setExpandedChunk] = useState({});

  const toggleChunk = (chunkId) => {
    setExpandedChunk((prev) => ({
      ...prev,
      [chunkId]: !prev[chunkId],
    }));
  };

  if (!intelligence) {
    return null;
  }

  const hasEvidence = intelligence.historical_evidence && intelligence.historical_evidence.length > 0;

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: 'rgba(115, 217, 245, 0.15)', padding: '6px', borderRadius: '8px', color: 'var(--accent)' }}>
            <BookOpen size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>
                Historical Incident Intelligence (RAG Layer)
              </h3>
              <span className="badge badge-low" style={{ fontSize: '0.7rem' }}>
                {intelligence.synthesizer_mode === 'llm_augmented' ? 'LLM Augmented' : 'Deterministic Hybrid RAG'}
              </span>
            </div>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
              Cross-references live telemetry with historical postmortems and troubleshooting runbooks
            </p>
          </div>
        </div>

        {/* Tab Toggle */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(0, 0, 0, 0.3)', padding: '4px', borderRadius: '8px' }}>
          <button
            onClick={() => setActiveTab('evidence')}
            style={{
              background: activeTab === 'evidence' ? 'rgba(115, 217, 245, 0.15)' : 'transparent',
              border: activeTab === 'evidence' ? '1px solid rgba(115, 217, 245, 0.3)' : 'none',
              color: activeTab === 'evidence' ? 'var(--accent)' : 'var(--text-secondary)',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '0.76rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Retrieved Precedents ({intelligence.historical_evidence?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('synthesis')}
            style={{
              background: activeTab === 'synthesis' ? 'rgba(115, 217, 245, 0.15)' : 'transparent',
              border: activeTab === 'synthesis' ? '1px solid rgba(115, 217, 245, 0.3)' : 'none',
              color: activeTab === 'synthesis' ? 'var(--accent)' : 'var(--text-secondary)',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '0.76rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Structured Synthesis
          </button>
        </div>
      </div>

      {/* Tab 1: Retrieved Historical Evidence */}
      {activeTab === 'evidence' && (
        <div>
          {hasEvidence ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {intelligence.historical_evidence.map((item) => {
                const isExpanded = !!expandedChunk[item.chunk_id];
                const scorePercent = Math.round(item.similarity_score * 100);
                return (
                  <div
                    key={item.chunk_id}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border)',
                      borderRadius: '10px',
                      padding: '14px 16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                            {item.doc_id}
                          </span>
                          <strong style={{ fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                            {item.title}
                          </strong>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                          <span className="badge" style={{ fontSize: '0.68rem' }}>
                            {item.category.replace('_', ' ').toUpperCase()}
                          </span>
                          {item.affected_service && (
                            <span className="badge badge-medium" style={{ fontSize: '0.68rem' }}>
                              Service: {item.affected_service}
                            </span>
                          )}
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            Source: <code>{item.source_path}</code>
                          </span>
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Relevance:</span>
                        <div style={{ fontSize: '1.1rem', fontWeight: '800', color: scorePercent >= 70 ? '#34d399' : '#ffd36e' }}>
                          {scorePercent}%
                        </div>
                      </div>
                    </div>

                    {/* Relevance Reason */}
                    <div style={{ fontSize: '0.76rem', color: 'var(--accent)', marginBottom: '8px' }}>
                      Relevance Factor: {item.relevance_reason}
                    </div>

                    {/* Expandable Excerpt */}
                    <div style={{ marginTop: '8px' }}>
                      <button
                        onClick={() => toggleChunk(item.chunk_id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-secondary)',
                          fontSize: '0.74rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: 0,
                          marginBottom: '6px',
                        }}
                      >
                        {isExpanded ? (
                          <>Hide Excerpt <ChevronUp size={13} /></>
                        ) : (
                          <>View Runbook Excerpt <ChevronDown size={13} /></>
                        )}
                      </button>

                      {isExpanded && (
                        <pre
                          style={{
                            background: 'rgba(0, 0, 0, 0.45)',
                            border: '1px solid var(--border)',
                            padding: '12px',
                            borderRadius: '8px',
                            fontSize: '0.74rem',
                            fontFamily: 'monospace',
                            color: '#73D9F5',
                            lineHeight: '1.4',
                            whiteSpace: 'pre-wrap',
                            overflowX: 'auto',
                            margin: 0,
                          }}
                        >
                          {item.excerpt}
                        </pre>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '30px 16px', color: 'var(--text-muted)' }}>
              <HelpCircle size={28} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
              <p style={{ fontSize: '0.84rem' }}>
                No historical incidents or runbooks matched the current error signature above relevance threshold.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Structured Investigation Synthesis */}
      {activeTab === 'synthesis' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Optional LLM Brief */}
          {intelligence.llm_synthesis && (
            <div style={{ background: 'rgba(115, 217, 245, 0.08)', border: '1px solid rgba(115, 217, 245, 0.25)', borderRadius: '10px', padding: '14px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent)', fontSize: '0.82rem', fontWeight: '700', marginBottom: '6px' }}>
                <Sparkles size={14} />
                <span>LLM Developer Brief</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', margin: 0, lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                {intelligence.llm_synthesis}
              </p>
            </div>
          )}

          {/* Observed Facts */}
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '14px 16px' }}>
            <h4 style={{ fontSize: '0.86rem', fontWeight: '700', color: '#34d399', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              1. Observed Telemetry Facts (Ground Truth)
            </h4>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>
              {intelligence.observed_facts?.map((fact, idx) => (
                <li key={idx}>{fact}</li>
              ))}
            </ul>
          </div>

          {/* Root-Cause Hypotheses */}
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '14px 16px' }}>
            <h4 style={{ fontSize: '0.86rem', fontWeight: '700', color: '#ffd36e', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              2. Algorithmic Root-Cause Hypotheses (Ranked)
            </h4>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>
              {intelligence.root_cause_hypotheses?.map((hyp, idx) => (
                <li key={idx}>{hyp}</li>
              ))}
            </ul>
          </div>

          {/* Recommended Investigation */}
          <div style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border)', borderRadius: '8px', padding: '14px 16px' }}>
            <h4 style={{ fontSize: '0.86rem', fontWeight: '700', color: 'var(--accent)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              3. Recommended Diagnostic & Mitigation Steps
            </h4>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>
              {intelligence.recommended_investigation?.map((act, idx) => (
                <li key={idx}>{act}</li>
              ))}
            </ul>
          </div>

          {/* Uncertainty Disclosures */}
          <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f87171', fontSize: '0.82rem', fontWeight: '700', marginBottom: '6px' }}>
              <ShieldAlert size={14} />
              <span>Uncertainty Disclosures & Caveats</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.76rem', color: '#fca5a5', lineHeight: '1.5' }}>
              {intelligence.uncertainty_disclosures?.map((unc, idx) => (
                <li key={idx}>{unc}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
