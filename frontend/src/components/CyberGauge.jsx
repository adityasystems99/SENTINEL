import React from 'react';

/**
 * CyberGauge (Reference 2 Inspiration)
 *
 * High-precision circular telemetry gauge with glowing gradient track,
 * animated arc, and centralized percentage or metric readout.
 */
export default function CyberGauge({
  value = 100,
  max = 100,
  label = 'Health',
  size = 72,
  strokeWidth = 6,
  colorScheme = 'cyan', // 'cyan' | 'violet' | 'emerald' | 'coral'
  suffix = '%',
}) {
  const percentage = Math.max(0, Math.min(100, Math.round((value / max) * 100)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const colorMap = {
    cyan: {
      gradient: ['#00f2fe', '#38bdf8'],
      glow: 'rgba(0, 242, 254, 0.4)',
      text: '#73D9F5',
    },
    violet: {
      gradient: ['#c084fc', '#8b5cf6'],
      glow: 'rgba(168, 85, 247, 0.4)',
      text: '#c4b5fd',
    },
    emerald: {
      gradient: ['#34d399', '#10b981'],
      glow: 'rgba(16, 185, 129, 0.4)',
      text: '#6ee7b7',
    },
    coral: {
      gradient: ['#f87171', '#ef4444'],
      glow: 'rgba(239, 68, 68, 0.4)',
      text: '#fca5a5',
    },
  };

  const currentTheme = colorMap[colorScheme] || colorMap.cyan;
  const gradientId = `gaugeGrad_${colorScheme}_${label.replace(/\s+/g, '')}`;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={currentTheme.gradient[0]} />
              <stop offset="100%" stopColor={currentTheme.gradient[1]} />
            </linearGradient>
          </defs>

          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            fill="none"
          />

          {/* Animated Value Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={`url(#${gradientId})`}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="none"
            style={{
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
              filter: `drop-shadow(0 0 4px ${currentTheme.glow})`,
            }}
          />
        </svg>

        {/* Central Readout */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: size <= 64 ? '0.78rem' : '0.92rem',
            fontWeight: '800',
            fontFamily: 'var(--font-mono)',
            color: currentTheme.text,
          }}
        >
          {percentage}{suffix}
        </div>
      </div>

      {label && (
        <span
          style={{
            fontSize: '0.72rem',
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            fontWeight: '600',
            textAlign: 'center',
          }}
        >
          {label}
        </span>
      )}
    </div>
  );
}
