import React from 'react';

/**
 * Sentinel Geometric Intelligence Mark
 *
 * An iconic, high-tech emblem featuring a faceted cyber-shield,
 * glowing neural vertex interconnects, and an animated pulsating singularity.
 * Seamlessly pairs with the cinematic particle vortex and enterprise security theme.
 */
export default function SentinelLogo({ size = 36, glowing = true, animated = false, className = '' }) {
  return (
    <div
      className={`sentinel-logo ${className}`}
      style={{
        position: 'relative',
        width: size,
        height: size,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
      aria-label="Sentinel Intelligence Mark"
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          filter: glowing ? 'drop-shadow(0 0 10px rgba(0, 210, 255, 0.45))' : 'none',
          transition: 'filter 0.3s ease',
        }}
      >
        <defs>
          <linearGradient id="shieldGrad" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#00f2fe" />
            <stop offset="50%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>

          <linearGradient id="facetGrad" x1="12" y1="12" x2="36" y2="36" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#73D9F5" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.1" />
          </linearGradient>

          <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="40%" stopColor="#73D9F5" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Outer Hexagonal Shield Boundary */}
        <polygon
          points="24,3 43,12 43,33 24,45 5,33 5,12"
          stroke="url(#shieldGrad)"
          strokeWidth="2.2"
          strokeLinejoin="round"
          fill="rgba(10, 15, 29, 0.75)"
        />

        {/* Internal Geometric Facet Lines */}
        <polygon
          points="24,10 37,17 37,31 24,38 11,31 11,17"
          stroke="url(#facetGrad)"
          strokeWidth="1.2"
          strokeLinejoin="round"
          fill="url(#facetGrad)"
        />

        {/* Neural Rays Connecting Facets to Core */}
        <line x1="24" y1="10" x2="24" y2="24" stroke="#73D9F5" strokeWidth="1.2" strokeOpacity="0.8" />
        <line x1="37" y1="17" x2="24" y2="24" stroke="#38bdf8" strokeWidth="1.2" strokeOpacity="0.6" />
        <line x1="37" y1="31" x2="24" y2="24" stroke="#818cf8" strokeWidth="1.2" strokeOpacity="0.6" />
        <line x1="24" y1="38" x2="24" y2="24" stroke="#a78bfa" strokeWidth="1.2" strokeOpacity="0.8" />
        <line x1="11" y1="31" x2="24" y2="24" stroke="#818cf8" strokeWidth="1.2" strokeOpacity="0.6" />
        <line x1="11" y1="17" x2="24" y2="24" stroke="#38bdf8" strokeWidth="1.2" strokeOpacity="0.6" />

        {/* Center Gravitational Node */}
        <circle cx="24" cy="24" r="4.5" fill="url(#coreGlow)" />
        <circle
          cx="24"
          cy="24"
          r="2.2"
          fill="#ffffff"
          className={animated ? 'sentinel-core-pulse' : ''}
        />
      </svg>
    </div>
  );
}
