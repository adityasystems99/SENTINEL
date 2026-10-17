import React, { useState } from 'react';
import { GitGraph, Info } from 'lucide-react';

export default function IncidentGraph({ nodes = [], edges = [] }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!nodes || nodes.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p style={{ fontSize: '0.85rem' }}>No graph data available for this incident</p>
      </div>
    );
  }

  // Simple layout: arrange nodes in layers by service or timestamp
  const width = 720;
  const height = 360;
  const padding = 60;

  // Group nodes by service
  const services = Array.from(new Set(nodes.map((n) => n.service)));
  const serviceXMap = {};
  services.forEach((svc, index) => {
    serviceXMap[svc] = padding + (index * (width - 2 * padding)) / Math.max(1, services.length - 1);
  });

  // Calculate Y based on timestamp
  const minTime = Math.min(...nodes.map((n) => n.timestamp));
  const maxTime = Math.max(...nodes.map((n) => n.timestamp));
  const timeSpan = Math.max(0.01, maxTime - minTime);

  const nodePositions = {};
  nodes.forEach((n) => {
    const x = serviceXMap[n.service] || width / 2;
    const normY = (n.timestamp - minTime) / timeSpan;
    const y = padding + normY * (height - 2 * padding);
    nodePositions[n.id] = { x, y };
  });

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <GitGraph size={18} color="#3b82f6" />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>NetworkX Incident Topology Graph</h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {nodes.length} nodes · {edges.length} causal edges
        </span>
      </div>

      <div style={{ position: 'relative', background: 'rgba(0, 0, 0, 0.4)', borderRadius: '12px', border: '1px solid var(--border)', overflow: 'hidden' }}>
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,0.4)" />
            </marker>
            <marker id="arrow-error" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
            </marker>
          </defs>

          {/* Service Column Labels */}
          {services.map((svc) => (
            <g key={svc}>
              <line
                x1={serviceXMap[svc]}
                y1={20}
                x2={serviceXMap[svc]}
                y2={height - 20}
                stroke="rgba(255,255,255,0.05)"
                strokeDasharray="4 4"
              />
              <text
                x={serviceXMap[svc]}
                y={25}
                fill="var(--text-muted)"
                fontSize="11"
                textAnchor="middle"
                fontWeight="600"
              >
                {svc}
              </text>
            </g>
          ))}

          {/* Edges */}
          {edges.map((e, idx) => {
            const src = nodePositions[e.source];
            const dst = nodePositions[e.target];
            if (!src || !dst) return null;

            const isErrorEdge = e.relation.includes('failure') || e.relation.includes('error');
            const strokeColor = isErrorEdge ? '#ef4444' : 'rgba(255, 255, 255, 0.25)';

            return (
              <line
                key={idx}
                x1={src.x}
                y1={src.y}
                x2={dst.x}
                y2={dst.y}
                stroke={strokeColor}
                strokeWidth={isErrorEdge ? 2 : 1.2}
                markerEnd={isErrorEdge ? 'url(#arrow-error)' : 'url(#arrow)'}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((n) => {
            const pos = nodePositions[n.id];
            if (!pos) return null;

            const isSelected = selectedNode?.id === n.id;
            const isError = n.is_error;
            const isDeploy = n.event_type === 'deployment';

            const fillColor = isDeploy ? '#f59e0b' : isError ? '#ef4444' : '#3b82f6';

            return (
              <g
                key={n.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => setSelectedNode(n)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  r={isSelected ? 14 : 10}
                  fill={fillColor}
                  fillOpacity={0.85}
                  stroke={isSelected ? '#ffffff' : 'rgba(255,255,255,0.3)'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <title>{`[${n.service}] ${n.message}`}</title>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Popover */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              right: '12px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '10px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backdropFilter: 'blur(8px)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`badge ${selectedNode.is_error ? 'badge-critical' : 'badge-medium'}`}>
                  {selectedNode.level}
                </span>
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                  [{selectedNode.service}]
                </strong>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(selectedNode.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {selectedNode.message}
              </p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.8rem', padding: '4px' }}
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
