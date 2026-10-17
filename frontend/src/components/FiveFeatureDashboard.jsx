import React from 'react';
import {
  Compass,
  FileCheck2,
  Radio,
  Share2,
  RotateCcw,
  ArrowRight,
  FolderArchive,
  FileCode,
  ShieldCheck,
  ChevronLeft,
} from 'lucide-react';

export default function FiveFeatureDashboard({
  project,
  onSelectFeature,
  onBackToEntry,
}) {
  const features = [
    {
      id: 'compatibility',
      question: 'Can I use it?',
      title: 'Project Compatibility & Integration Readiness',
      description: 'Inspect available technologies, telemetry sources, prerequisites, and framework integration requirements.',
      icon: <Compass size={28} color="#73D9F5" />,
      accentColor: '#73D9F5',
      badge: 'Readiness Scan',
      status: 'Ready to Inspect',
    },
    {
      id: 'promise_audit',
      question: 'Have I built what I promised?',
      title: 'Promise vs. Reality Code Audit',
      description: 'Compare project proposal specifications with actual extracted source code and AST implementations.',
      icon: <FileCheck2 size={28} color="#ffd36e" />,
      accentColor: '#ffd36e',
      badge: 'Spec Auditor',
      status: 'Workspace Available',
    },
    {
      id: 'incidents',
      question: 'Why is my application failing?',
      title: 'Live Incident Investigation',
      description: 'Collect telemetry, construct NetworkX causal incident graphs, rank root causes, and inspect timelines.',
      icon: <Radio size={28} color="#ff6ea9" />,
      accentColor: '#ff6ea9',
      badge: 'Active Engine',
      status: 'Live & Operational',
    },
    {
      id: 'dependency_radar',
      question: 'What else could break?',
      title: 'Dependency & Impact Radar',
      description: 'Analyze service dependencies and trace spans to map downstream blast radius and affected microservices.',
      icon: <Share2 size={28} color="#a78bfa" />,
      accentColor: '#a78bfa',
      badge: 'Topology Radar',
      status: 'Graph Indexed',
    },
    {
      id: 'fix_validation',
      question: 'Does my fix actually work?',
      title: 'Replay Lab & Fix Validation',
      description: 'Reproduce failures in controlled sandboxes, test candidate patches, and compare before/after telemetry.',
      icon: <RotateCcw size={28} color="#34d399" />,
      accentColor: '#34d399',
      badge: 'Validation Lab',
      status: 'Test Runner Ready',
    },
  ];

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Bar: Project Summary & Back */}
      <div
        className="glass-panel"
        style={{
          padding: '18px 24px',
          marginBottom: '28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            onClick={onBackToEntry}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text-secondary)',
              padding: '6px 10px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.8rem',
            }}
          >
            <ChevronLeft size={16} /> Switch Project
          </button>

          <div style={{ width: '1px', height: '28px', background: 'var(--border)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FolderArchive size={22} color="var(--accent)" />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: '800', letterSpacing: '-0.01em' }}>
                  {project?.name || 'Demo Project'}
                </h2>
                <span className="badge badge-low">{project?.status || 'ready'}</span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                ID: <code>{project?.project_id || 'demo'}</code> · {project?.file_count || 0} source files ·{' '}
                {project?.detected_frameworks?.join(', ') || 'Multi-tier Microservices'}
              </p>
            </div>
          </div>
        </div>

        {/* Project Metrics Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'rgba(0, 0, 0, 0.35)',
            padding: '8px 16px',
            borderRadius: '10px',
            border: '1px solid var(--border)',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FileCode size={15} color="var(--accent)" />
            <span>Files: <strong style={{ color: 'var(--text-primary)' }}>{project?.file_count || 0}</strong></span>
          </div>
          <span>•</span>
          <div>
            Size: <strong style={{ color: 'var(--text-primary)' }}>{(((project?.extracted_size_bytes || 0) / 1024)).toFixed(1)} KB</strong>
          </div>
          {project?.excluded_items_count > 0 && (
            <>
              <span>•</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#34d399' }}>
                <ShieldCheck size={14} />
                <span>{project.excluded_items_count} excluded</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Five-Feature Grid */}
      <div style={{ marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '6px', letterSpacing: '-0.02em' }}>
          Select Developer Intelligence Workspace
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Each workspace provides focused investigation into project compatibility, specification compliance, active incident root-causes, downstream risk, and fix validation.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '20px',
        }}
      >
        {features.map((feat) => (
          <div
            key={feat.id}
            tabIndex={0}
            role="button"
            className="feature-card"
            onClick={() => onSelectFeature(feat.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectFeature(feat.id);
              }
            }}
            style={{
              minHeight: '220px',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div
                  style={{
                    background: `rgba(255, 255, 255, 0.04)`,
                    border: `1px solid rgba(255, 255, 255, 0.08)`,
                    padding: '12px',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {feat.icon}
                </div>
                <span className="badge badge-medium" style={{ borderColor: `${feat.accentColor}40`, color: feat.accentColor }}>
                  {feat.badge}
                </span>
              </div>

              <div style={{ fontSize: '0.85rem', fontWeight: '700', color: feat.accentColor, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                {feat.question}
              </div>

              <h4 style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--text-primary)', marginBottom: '8px', lineHeight: '1.3' }}>
                {feat.title}
              </h4>

              <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                {feat.description}
              </p>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '20px',
                paddingTop: '14px',
                borderTop: '1px solid var(--border)',
              }}
            >
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                {feat.status}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: feat.accentColor, fontSize: '0.82rem', fontWeight: '700' }}>
                <span>Open Workspace</span>
                <ArrowRight size={15} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
