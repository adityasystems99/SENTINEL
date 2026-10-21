import React from 'react';
import ParticleVortex from './ParticleVortex';
import SentinelLogo from './SentinelLogo';

export default function LoadingScreen({ message = 'Connecting to SENTINEL Intelligence Engine...' }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#060913',
        color: 'var(--text-primary)',
        padding: '24px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Cinematic 3D Particle Vortex Background */}
      <ParticleVortex mode="hero" />

      {/* Foreground Content */}
      <div
        className="glass-panel"
        style={{
          position: 'relative',
          zIndex: 1,
          padding: '40px 48px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: '460px',
          border: '1px solid rgba(0, 242, 254, 0.2)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 242, 254, 0.1)',
        }}
      >
        <div style={{ marginBottom: '24px' }}>
          <SentinelLogo size={64} glowing={true} animated={true} />
        </div>

        <h2
          style={{
            fontSize: '1.6rem',
            fontWeight: '900',
            letterSpacing: '0.12em',
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #ffffff 0%, #73D9F5 50%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          SENTINEL
        </h2>

        <p
          style={{
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            marginBottom: '20px',
            lineHeight: '1.5',
          }}
        >
          {message}
        </p>

        {/* Cyber Progress Indicator */}
        <div
          style={{
            width: '180px',
            height: '3px',
            background: 'rgba(255, 255, 255, 0.08)',
            borderRadius: '999px',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: '45%',
              background: 'linear-gradient(90deg, #8b5cf6, #00f2fe)',
              borderRadius: '999px',
              animation: 'loadSlide 1.6s ease-in-out infinite alternate',
            }}
          />
        </div>
      </div>

      <style>{`
        @keyframes loadSlide {
          0% { left: 0%; }
          100% { left: 55%; }
        }
      `}</style>
    </div>
  );
}
