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
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px', border: '1px solid rgba(0, 242, 254, 0.15)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <GitGraph size={18} color="var(--accent-cyan)" />
          <h3 style={{ fontSize: '1rem', fontWeight: '700' }}>NetworkX Incident Topology Graph</h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {nodes.length} nodes · {edges.length} causal edges
        </span>
      </div>

      <div
        style={{
          position: 'relative',
          background: 'radial-gradient(circle at center, #0e1526 0%, #060913 100%)',
          borderRadius: '12px',
          border: '1px solid rgba(115, 217, 245, 0.18)',
          overflow: 'hidden',
          boxShadow: 'inset 0 0 30px rgba(0,0,0,0.6)',
        }}
      >
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(115, 217, 245, 0.4)" />
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
                stroke="rgba(115, 217, 245, 0.08)"
                strokeDasharray="4 4"
              />
              <text
                x={serviceXMap[svc]}
                y={25}
                fill="var(--text-secondary)"
                fontSize="11"
                textAnchor="middle"
                fontWeight="700"
                fontFamily="var(--font-mono)"
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
            const strokeColor = isErrorEdge ? '#ef4444' : 'rgba(115, 217, 245, 0.35)';

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

            const fillColor = isDeploy ? '#f59e0b' : isError ? '#ef4444' : '#00f2fe';

            return (
              <g
                key={n.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => setSelectedNode(n)}
                style={{ cursor: 'pointer' }}
              >
                {/* Glow ring */}
                <circle
                  r={isSelected ? 16 : 12}
                  fill={fillColor}
                  fillOpacity={0.2}
                  filter="blur(2px)"
                />
                <circle
                  r={isSelected ? 13 : 9}
                  fill={fillColor}
                  fillOpacity={0.9}
                  stroke={isSelected ? '#ffffff' : 'rgba(255,255,255,0.4)'}
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
              background: 'rgba(6, 9, 19, 0.95)',
              border: '1px solid rgba(0, 242, 254, 0.3)',
              borderRadius: '10px',
              padding: '12px 16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backdropFilter: 'blur(12px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.7)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`badge ${selectedNode.is_error ? 'badge-critical' : 'badge-medium'}`}>
                  {selectedNode.level}
                </span>
                <strong style={{ fontSize: '0.84rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
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
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.9rem',
                cursor: 'pointer',
                padding: '4px 8px',
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
