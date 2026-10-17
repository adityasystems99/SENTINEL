import React, { useState, useEffect } from 'react';
import {
  Share2,
  ChevronLeft,
  ShieldAlert,
  Layers,
  Network,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Compass,
  Activity,
  Maximize2,
} from 'lucide-react';
import { fetchRadarTopology, analyzeRadarImpact } from '../../api/client';

export default function DependencyRadarWorkspace({ project, onBackToDashboard }) {
  const [topology, setTopology] = useState(null);
  const [selectedService, setSelectedService] = useState('inventory-service');
  const [impactReport, setImpactReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTopologyAndAnalyze(selectedService);
  }, []);

  async function loadTopologyAndAnalyze(serviceName) {
    setLoading(true);
    setError(null);
    try {
      const topo = await fetchRadarTopology(600);
      setTopology(topo);
      
      const target = serviceName || (topo?.nodes?.[0]?.service || 'inventory-service');
      setSelectedService(target);

      setAnalyzing(true);
      const report = await analyzeRadarImpact(target, 600);
      setImpactReport(report);
    } catch (err) {
      setError(err.message || 'Failed to load dependency radar');
    } finally {
      setLoading(false);
      setAnalyzing(false);
    }
  }

  async function handleSelectService(serviceName) {
    setSelectedService(serviceName);
    setAnalyzing(true);
    setError(null);
    try {
      const report = await analyzeRadarImpact(serviceName, 600);
      setImpactReport(report);
    } catch (err) {
      setError(err.message || `Failed to analyze impact for ${serviceName}`);
    } finally {
      setAnalyzing(false);
    }
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'failing':
        return (
          <span className="badge badge-critical" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertCircle size={12} /> Failing
          </span>
        );
      case 'at_risk':
        return (
          <span className="badge badge-medium" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={12} /> At Risk
          </span>
        );
      case 'healthy':
        return (
          <span className="badge badge-low" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={12} /> Healthy
          </span>
        );
      default:
        return (
          <span className="badge" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(167, 139, 250, 0.15)', color: '#c4b5fd' }}>
            <HelpCircle size={12} /> Unknown
          </span>
        );
    }
  };

  const getPriorityBadge = (prio) => {
    switch (prio) {
      case 1:
        return <span className="badge badge-critical">Priority 1 (Target)</span>;
      case 2:
        return <span className="badge badge-high">Priority 2 (Direct Cascade)</span>;
      case 3:
        return <span className="badge badge-medium">Priority 3 (Transitive)</span>;
      default:
        return <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-secondary)' }}>Priority {prio} (Watch)</span>;
    }
  };

  // Node positions on a clean layout for the 5 demo services
  const nodePositions = {
    'web-gateway': { x: 100, y: 150 },
    'auth-service': { x: 340, y: 70 },
    'order-service': { x: 340, y: 230 },
    'inventory-service': { x: 580, y: 170 },
    'payment-service': { x: 580, y: 290 },
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
            <div style={{ background: 'rgba(167, 139, 250, 0.15)', padding: '6px 8px', borderRadius: '8px', color: '#a78bfa' }}>
              <Share2 size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.1rem', fontWeight: '800' }}>
                  Feature 4 — Dependency & Impact Radar
                </h2>
                <span className="badge badge-medium" style={{ color: '#a78bfa', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
                  What else breaks?
                </span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Workspace'}</strong> · Directed Service Topology & Cascading Blast-Radius
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => loadTopologyAndAnalyze(selectedService)}
          disabled={loading || analyzing}
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
          <RefreshCw size={14} className={loading || analyzing ? 'spin' : ''} /> Refresh Topology
        </button>
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
            onClick={() => loadTopologyAndAnalyze(selectedService)}
            style={{ background: 'transparent', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '0.8rem' }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Interactive Topology Graph Canvas */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} color="#a78bfa" />
            <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Interactive Service Dependency Topology</h3>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Click any service node below to inspect its cascading blast radius
          </div>
        </div>

        {/* Visual Graph Area */}
        <div
          style={{
            width: '100%',
            height: '340px',
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <svg style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#a78bfa" opacity="0.7" />
              </marker>
            </defs>

            {/* Render Edges */}
            {topology?.edges?.map((edge, idx) => {
              const srcPos = nodePositions[edge.source];
              const tgtPos = nodePositions[edge.target];
              if (!srcPos || !tgtPos) return null;
              const isSelectedPath = edge.target === selectedService || edge.source === selectedService;
              return (
                <g key={idx}>
                  <line
                    x1={srcPos.x + 60}
                    y1={srcPos.y + 20}
                    x2={tgtPos.x + 60}
                    y2={tgtPos.y + 20}
                    stroke={isSelectedPath ? '#c4b5fd' : 'rgba(255, 255, 255, 0.15)'}
                    strokeWidth={isSelectedPath ? 2.5 : 1.5}
                    strokeDasharray={edge.evidence_source === 'configured_demo_topology' ? '4,4' : 'none'}
                    markerEnd="url(#arrow)"
                  />
                  {edge.error_count > 0 && (
                    <text
                      x={(srcPos.x + tgtPos.x) / 2 + 50}
                      y={(srcPos.y + tgtPos.y) / 2 + 10}
                      fill="#f87171"
                      fontSize="10"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {edge.error_count} errs
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Render Interactive Node Cards */}
          {topology?.nodes?.map((node) => {
            const pos = nodePositions[node.service] || { x: 200, y: 150 };
            const isSelected = selectedService === node.service;
            const isFailing = node.status === 'failing';
            return (
              <div
                key={node.service}
                onClick={() => handleSelectService(node.service)}
                style={{
                  position: 'absolute',
                  left: `${pos.x}px`,
                  top: `${pos.y}px`,
                  width: '140px',
                  padding: '10px 12px',
                  background: isSelected
                    ? 'rgba(167, 139, 250, 0.25)'
                    : isFailing
                    ? 'rgba(239, 68, 68, 0.15)'
                    : 'rgba(20, 26, 38, 0.85)',
                  border: isSelected
                    ? '2px solid #a78bfa'
                    : isFailing
                    ? '1.5px solid #f87171'
                    : '1px solid var(--border)',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  boxShadow: isSelected ? '0 0 15px rgba(167, 139, 250, 0.4)' : 'none',
                  transition: 'all 0.2s ease',
                  userSelect: 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: '700', color: isSelected ? '#fff' : 'var(--text-primary)' }}>
                    {node.service}
                  </span>
                  {node.error_count > 0 ? (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f87171' }} />
                  ) : (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }} />
                  )}
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                  {node.tier}
                </div>
                {node.error_count > 0 && (
                  <div style={{ fontSize: '0.68rem', color: '#f87171', fontWeight: 'bold', marginTop: '2px' }}>
                    {node.error_count} errors
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Component Impact Analysis */}
      {impactReport && (
        <div>
          {/* Overview Metrics Bar */}
          <div
            className="glass-panel"
            style={{
              padding: '20px 24px',
              marginBottom: '24px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              alignItems: 'center',
            }}
          >
            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Suspected Failure Point
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                <strong style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>
                  {impactReport.suspected_component}
                </strong>
                {getStatusBadge(impactReport.impacted_components?.[0]?.status)}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Blast Radius (Dependents)
              </span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#ffd36e', marginTop: '2px' }}>
                {impactReport.impacted_components?.length - 1 || 0} Connected Services
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Observed Active Failures
              </span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#f87171', marginTop: '2px' }}>
                {impactReport.impacted_components?.filter((c) => c.observed_failure).length} Services
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Topology Confidence
              </span>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--accent)', marginTop: '2px' }}>
                {Math.round(impactReport.confidence * 100)}%
              </div>
            </div>
          </div>

          {/* Impacted Components List */}
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <ShieldAlert size={18} color="#f87171" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>
                Cascading Impact Breakdown & Investigation Priority
              </h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {impactReport.impacted_components?.map((comp, idx) => (
                <div
                  key={comp.service}
                  style={{
                    background: comp.observed_failure ? 'rgba(239, 68, 68, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                    border: comp.observed_failure ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid var(--border)',
                    borderRadius: '10px',
                    padding: '16px 18px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <strong style={{ fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                        [{comp.service}]
                      </strong>
                      {getStatusBadge(comp.status)}
                      <span className="badge" style={{ fontSize: '0.72rem' }}>
                        {comp.relationship.replace('_', ' ').toUpperCase()} ({comp.distance} hop{comp.distance === 1 ? '' : 's'})
                      </span>
                    </div>
                    <div>
                      {getPriorityBadge(comp.priority)}
                    </div>
                  </div>

                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '0 0 8px 0', lineHeight: '1.5' }}>
                    <strong>Impact Rationale:</strong> {comp.reason}
                  </p>

                  <div style={{ fontSize: '0.78rem', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ArrowRight size={13} />
                    <span><strong>Recommended Action:</strong> {comp.recommended_action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Grid: Dependency Paths & Supporting Evidence */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            {/* Dependency Call Cascades */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Layers size={18} color="var(--accent)" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Cascading Dependency Paths</h3>
              </div>

              {impactReport.dependency_paths?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {impactReport.dependency_paths.map((path, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'rgba(0, 0, 0, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontFamily: 'monospace',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {path.join(' ➔ ')}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>No upstream callers detected.</p>
              )}
            </div>

            {/* Suggested Investigation Steps */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Compass size={18} color="#ffd36e" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Suggested Investigation Steps</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {impactReport.suggested_investigation_steps?.map((step, i) => (
                  <p key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: '1.5' }}>
                    {step}
                  </p>
                ))}
              </div>
            </div>
          </div>

          {/* Limitations Notice */}
          <div className="glass-panel" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              <HelpCircle size={15} />
              <strong style={{ fontSize: '0.82rem' }}>Impact Radar Scope & Analysis Limitations</strong>
            </div>
            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              {impactReport.limitations?.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
