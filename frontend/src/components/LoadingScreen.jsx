import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function LoadingScreen({ message = 'Connecting to SENTINEL Intelligence Engine...' }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle at center, #0e1626 0%, #080D18 100%)',
        color: 'var(--text-primary)',
        padding: '24px',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '72px',
          height: '72px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: '2px solid rgba(115, 217, 245, 0.2)',
            borderTopColor: 'var(--accent)',
            animation: 'spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite',
          }}
        />
        <ShieldAlert size={36} color="var(--accent)" />
      </div>

      <h2 style={{ fontSize: '1.4rem', fontWeight: '800', letterSpacing: '-0.02em', marginBottom: '8px' }}>
        SENTINEL
      </h2>
      <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', maxWidth: '400px' }}>
        {message}
      </p>
    </div>
  );
}
