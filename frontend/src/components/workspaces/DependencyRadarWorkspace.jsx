import React, { useState, useEffect, useMemo } from 'react';
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
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sliders,
} from 'lucide-react';
import { fetchRadarTopology, analyzeRadarImpact } from '../../api/client';

export default function DependencyRadarWorkspace({ project, onBackToDashboard }) {
  const [topology, setTopology] = useState(null);
  const [selectedService, setSelectedService] = useState('inventory-service');
  const [hoveredNode, setHoveredNode] = useState(null);
  const [impactReport, setImpactReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  // Graph interactive controls
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'failing' | 'at_risk' | 'healthy'
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });

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
          <span
            className="badge"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              background: 'rgba(167, 139, 250, 0.15)',
              color: '#c4b5fd',
            }}
          >
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
        return (
          <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-secondary)' }}>
            Priority {prio} (Watch)
          </span>
        );
    }
  };

  // Dynamic Clustered Force/Orbital Layout inspired by Reference 3 (glyphtrail)
  const nodeLayout = useMemo(() => {
    const rawNodes = topology?.nodes || [];
    const positions = {};
    const center = { x: 420, y: 220 };

    // Group nodes or arrange in orbital shell
    const n = rawNodes.length;
    if (n === 0) return positions;

    // Define preset coordinates for high readability, plus radial fallback for dynamically ingested services
    const defaultCoords = {
      'web-gateway': { x: 140, y: 220, tierColor: '#f59e0b', ring: 1 },
      'auth-service': { x: 380, y: 110, tierColor: '#00f2fe', ring: 1 },
      'order-service': { x: 420, y: 310, tierColor: '#00f2fe', ring: 1 },
      'inventory-service': { x: 680, y: 160, tierColor: '#ef4444', ring: 2 },
      'payment-service': { x: 690, y: 310, tierColor: '#a78bfa', ring: 2 },
    };

    rawNodes.forEach((node, idx) => {
      if (defaultCoords[node.service]) {
        positions[node.service] = defaultCoords[node.service];
      } else {
        // Radial distribution
        const angle = (idx / n) * Math.PI * 2;
        const radius = 180 + (idx % 2) * 60;
        positions[node.service] = {
          x: center.x + Math.cos(angle) * radius,
          y: center.y + Math.sin(angle) * radius,
          tierColor: '#38bdf8',
          ring: 2,
        };
      }
    });

    return positions;
  }, [topology]);

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    if (!topology?.nodes) return [];
    return topology.nodes.filter((node) => {
      const matchesSearch = !searchQuery || node.service.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'failing' && node.status === 'failing') ||
        (statusFilter === 'at_risk' && node.status === 'at_risk') ||
        (statusFilter === 'healthy' && node.status === 'healthy');
      return matchesSearch && matchesStatus;
    });
  }, [topology, searchQuery, statusFilter]);

  return (
    <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '24px 20px', position: 'relative', zIndex: 1 }}>
      {/* Header Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          border: '1px solid rgba(167, 139, 250, 0.25)',
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
              fontWeight: '600',
            }}
          >
            <ChevronLeft size={16} /> Back to Dashboard
          </button>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                background: 'rgba(167, 139, 250, 0.15)',
                padding: '8px',
                borderRadius: '10px',
                color: '#a78bfa',
                border: '1px solid rgba(167, 139, 250, 0.3)',
              }}
            >
              <Share2 size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: '800' }}>Feature 4 — Dependency & Impact Radar</h2>
                <span className="badge badge-medium" style={{ color: '#a78bfa', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
                  CODE TOPOLOGY INTELLIGENCE
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Project: <strong>{project?.name || 'Active Workspace'}</strong> · NetworkX Directed Graph & Blast-Radius Engine
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => loadTopologyAndAnalyze(selectedService)}
          disabled={loading || analyzing}
          style={{
            padding: '8px 16px',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(167, 139, 250, 0.12)',
            border: '1px solid rgba(167, 139, 250, 0.35)',
            color: '#c4b5fd',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600',
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
            marginBottom: '20px',
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
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fca5a5',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Reference 3: High-Tech Code Intelligence Graph Canvas (glyphtrail Style) */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        {/* Graph Controls Bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Network size={20} color="#00f2fe" />
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: '800' }}>Local Software Intelligence & Dependency Graph</h3>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                {topology?.nodes?.length || 0} entities · {topology?.edges?.length || 0} directed dependency relationships
              </span>
            </div>
          </div>

          {/* Search & Filters */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'rgba(6, 9, 19, 0.6)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '4px 10px',
              }}
            >
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search entity..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.78rem',
                  outline: 'none',
                  width: '120px',
                }}
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'rgba(6, 9, 19, 0.6)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
                borderRadius: '8px',
                padding: '5px 10px',
                fontSize: '0.78rem',
                outline: 'none',
              }}
            >
              <option value="all">All States</option>
              <option value="failing">Failing Only</option>
              <option value="at_risk">At Risk</option>
              <option value="healthy">Healthy</option>
            </select>

            {/* Zoom Controls */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '2px',
                background: 'rgba(6, 9, 19, 0.6)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '2px',
              }}
            >
              <button
                onClick={() => setZoomLevel((z) => Math.min(1.5, z + 0.1))}
                title="Zoom In"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  padding: '4px 6px',
                  cursor: 'pointer',
                }}
              >
                <ZoomIn size={14} />
              </button>
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.1))}
                title="Zoom Out"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  padding: '4px 6px',
                  cursor: 'pointer',
                }}
              >
                <ZoomOut size={14} />
              </button>
              <button
                onClick={() => {
                  setZoomLevel(1);
                  setPanOffset({ x: 0, y: 0 });
                }}
                title="Reset View"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  padding: '4px 6px',
                  cursor: 'pointer',
                }}
              >
                <RotateCcw size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Visual Graph Area (glyphtrail style) */}
        <div
          style={{
            width: '100%',
            height: '420px',
            background: 'radial-gradient(circle at center, #0e1526 0%, #060913 100%)',
            border: '1px solid rgba(0, 242, 254, 0.2)',
            borderRadius: '14px',
            position: 'relative',
            overflow: 'hidden',
            boxShadow: 'inset 0 0 40px rgba(0, 0, 0, 0.8)',
          }}
        >
          {/* Subtle Grid Pattern */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage:
                'radial-gradient(circle, rgba(115, 217, 245, 0.1) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              opacity: 0.4,
              pointerEvents: 'none',
            }}
          />

          <svg
            style={{
              width: '100%',
              height: '100%',
              position: 'absolute',
              top: 0,
              left: 0,
              transform: `scale(${zoomLevel}) translate(${panOffset.x}px, ${panOffset.y}px)`,
              transformOrigin: 'center center',
              transition: 'transform 0.2s ease',
            }}
            viewBox="0 0 840 440"
          >
            <defs>
              {/* Glowing Arrow Markers */}
              <marker
                id="radarArrow"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#00f2fe" opacity="0.8" />
              </marker>

              <marker
                id="radarArrowError"
                viewBox="0 0 10 10"
                refX="22"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" opacity="0.9" />
              </marker>

              {/* Edge Gradient */}
              <linearGradient id="edgeGradNormal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f2fe" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.4" />
              </linearGradient>

              <linearGradient id="edgeGradError" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0.9" />
              </linearGradient>
            </defs>

            {/* Ambient Background Orbital Concentric Rings */}
            <circle cx="420" cy="220" r="140" fill="none" stroke="rgba(115, 217, 245, 0.04)" strokeDasharray="6 6" />
            <circle cx="420" cy="220" r="280" fill="none" stroke="rgba(115, 217, 245, 0.03)" strokeDasharray="8 8" />

            {/* Render Smooth Curved Bezier Edges */}
            {topology?.edges?.map((edge, idx) => {
              const srcPos = nodeLayout[edge.source];
              const tgtPos = nodeLayout[edge.target];
              if (!srcPos || !tgtPos) return null;

              const isSelectedPath = edge.target === selectedService || edge.source === selectedService;
              const hasErrors = edge.error_count > 0;

              // Quadratic Bezier curve control point with slight bow
              const midX = (srcPos.x + tgtPos.x) / 2;
              const midY = (srcPos.y + tgtPos.y) / 2 - 25;
              const pathData = `M ${srcPos.x} ${srcPos.y} Q ${midX} ${midY} ${tgtPos.x} ${tgtPos.y}`;

              return (
                <g key={idx}>
                  {/* Outer Glow Line for Selected Path */}
                  {isSelectedPath && (
                    <path
                      d={pathData}
                      fill="none"
                      stroke={hasErrors ? 'rgba(239, 68, 68, 0.35)' : 'rgba(0, 242, 254, 0.35)'}
                      strokeWidth="6"
                    />
                  )}

                  {/* Main Curved Line */}
                  <path
                    d={pathData}
                    fill="none"
                    stroke={
                      hasErrors
                        ? 'url(#edgeGradError)'
                        : isSelectedPath
                        ? '#00f2fe'
                        : 'rgba(115, 217, 245, 0.2)'
                    }
                    strokeWidth={isSelectedPath ? 2.5 : 1.4}
                    strokeDasharray={isSelectedPath ? '6 3' : 'none'}
                    markerEnd={hasErrors ? 'url(#radarArrowError)' : 'url(#radarArrow)'}
                    className={isSelectedPath ? 'animated-flow-edge' : ''}
                  />

                  {/* Error badge along edge */}
                  {hasErrors && (
                    <g transform={`translate(${midX}, ${midY + 12})`}>
                      <rect x="-24" y="-8" width="48" height="16" rx="8" fill="#1e1014" stroke="#ef4444" strokeWidth="1" />
                      <text x="0" y="3" fill="#f87171" fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                        {edge.error_count} errs
                      </text>
                    </g>
                  )}
                </g>
              );
            })}

            {/* Render Circular Nodes with glyphtrail style */}
            {filteredNodes.map((node) => {
              const pos = nodeLayout[node.service] || { x: 420, y: 220 };
              const isSelected = selectedService === node.service;
              const isHovered = hoveredNode?.service === node.service;
              const isFailing = node.status === 'failing';
              const isAtRisk = node.status === 'at_risk';

              // Sizing based on degree or failures
              const baseRadius = isSelected ? 22 : 18;

              // Color scheme
              let nodeColor = '#00f2fe';
              if (isFailing) nodeColor = '#ef4444';
              else if (isAtRisk) nodeColor = '#f59e0b';
              else if (node.tier === 'data') nodeColor = '#a78bfa';
              else if (node.tier === 'ingress') nodeColor = '#38bdf8';

              return (
                <g
                  key={node.service}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => handleSelectService(node.service)}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Concentric Pulsating Ring for Failing or Selected Nodes */}
                  {(isSelected || isFailing) && (
                    <circle
                      r={baseRadius + 10}
                      fill="none"
                      stroke={nodeColor}
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      opacity="0.6"
                      className="spin"
                    />
                  )}

                  {/* Outer Glow Halo */}
                  <circle
                    r={baseRadius + 5}
                    fill={nodeColor}
                    fillOpacity={isSelected ? 0.25 : 0.12}
                    filter="blur(2px)"
                  />

                  {/* Core Node Circle */}
                  <circle
                    r={baseRadius}
                    fill="#060913"
                    stroke={nodeColor}
                    strokeWidth={isSelected ? 3 : 2}
                  />

                  {/* Center Dot Indicator */}
                  <circle
                    r={isSelected ? 7 : 5}
                    fill={nodeColor}
                    className={isFailing ? 'sentinel-core-pulse' : ''}
                  />

                  {/* Node Title Label */}
                  <text
                    y={baseRadius + 18}
                    fill={isSelected ? '#ffffff' : 'var(--text-primary)'}
                    fontSize="11"
                    fontWeight={isSelected ? '800' : '600'}
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {node.service}
                  </text>

                  {/* Tier / Error Sublabel */}
                  <text
                    y={baseRadius + 30}
                    fill={isFailing ? '#f87171' : 'var(--text-muted)'}
                    fontSize="9.5"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {isFailing ? `${node.error_count} ERRORS` : node.tier?.toUpperCase()}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Interactive Inspection Popover on Hover or Selection */}
          {(hoveredNode || selectedService) && (
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                right: '16px',
                background: 'rgba(6, 9, 19, 0.88)',
                border: '1px solid rgba(0, 242, 254, 0.3)',
                borderRadius: '12px',
                padding: '12px 18px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
                maxWidth: '300px',
                pointerEvents: 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '0.88rem', color: '#fff', fontFamily: 'monospace' }}>
                  {hoveredNode?.service || selectedService}
                </strong>
                {getStatusBadge(hoveredNode?.status || 'failing')}
              </div>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', margin: 0 }}>
                Click node to recalculate cascading blast radius and inspect downstream paths.
              </p>
            </div>
          )}
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
              border: '1px solid rgba(0, 242, 254, 0.18)',
            }}
          >
            <div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Suspected Failure Point
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                <strong style={{ fontSize: '1.2rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>
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
                {Math.max(0, (impactReport.impacted_components?.length || 1) - 1)} Connected Services
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
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--accent-cyan)', marginTop: '2px' }}>
                {Math.round(impactReport.confidence * 100)}%
              </div>
            </div>
          </div>

          {/* Impacted Components List */}
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <ShieldAlert size={18} color="#f87171" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: '800' }}>Cascading Impact Breakdown & Investigation Priority</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {impactReport.impacted_components?.map((comp) => (
                <div
                  key={comp.service}
                  style={{
                    background: comp.observed_failure ? 'rgba(239, 68, 68, 0.08)' : 'rgba(6, 9, 19, 0.45)',
                    border: comp.observed_failure
                      ? '1px solid rgba(239, 68, 68, 0.35)'
                      : '1px solid rgba(115, 217, 245, 0.15)',
                    borderRadius: '12px',
                    padding: '16px 20px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      flexWrap: 'wrap',
                      gap: '10px',
                      marginBottom: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <strong style={{ fontSize: '1rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                        [{comp.service}]
                      </strong>
                      {getStatusBadge(comp.status)}
                      <span className="badge" style={{ fontSize: '0.72rem' }}>
                        {comp.relationship.replace('_', ' ').toUpperCase()} ({comp.distance} hop
                        {comp.distance === 1 ? '' : 's'})
                      </span>
                    </div>
                    <div>{getPriorityBadge(comp.priority)}</div>
                  </div>

                  <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', margin: '0 0 10px 0', lineHeight: '1.5' }}>
                    <strong>Impact Rationale:</strong> {comp.reason}
                  </p>

                  <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ArrowRight size={14} />
                    <span>
                      <strong>Recommended Action:</strong> {comp.recommended_action}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Grid: Dependency Paths & Supporting Evidence */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px', marginBottom: '24px' }}>
            {/* Dependency Call Cascades */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Layers size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>Cascading Dependency Paths</h3>
              </div>

              {impactReport.dependency_paths?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {impactReport.dependency_paths.map((path, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'rgba(6, 9, 19, 0.6)',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontSize: '0.82rem',
                        fontFamily: 'monospace',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border)',
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

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {impactReport.suggested_investigation_steps?.map((step, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '8px',
                      fontSize: '0.82rem',
                      color: 'var(--text-secondary)',
                      lineHeight: '1.5',
                    }}
                  >
                    <span style={{ color: '#ffd36e', fontWeight: 'bold' }}>{i + 1}.</span>
                    <span>{step}</span>
                  </div>
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

      <style>{`
        @keyframes flowDash {
          to {
            stroke-dashoffset: -30;
          }
        }
        .animated-flow-edge {
          animation: flowDash 1.2s linear infinite;
        }
      `}</style>
    </div>
  );
}
