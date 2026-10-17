import React from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';

export default function StartProjectButton({ onClick, disabled, loading }) {
  return (
    <button
      type="button"
      className="start-project-btn"
      onClick={onClick}
      disabled={disabled || loading}
      aria-label="Start Project"
    >
      {/* 34px circular dark icon disc containing centered arrow and animated ring */}
      <span className="start-icon-disc">
        {/* Masked Conic Gradient Ring */}
        <span className="start-project-ring" aria-hidden="true" />

        {/* Centered arrow above the ring at z-index: 2 */}
        <span className="start-arrow">
          {loading ? (
            <Loader2 size={16} className="spin" color="var(--accent)" />
          ) : (
            <ArrowRight size={17} strokeWidth={2.5} />
          )}
        </span>
      </span>

      {/* Uppercase, widely spaced monospace label */}
      <span>{loading ? 'INITIALIZING...' : 'START PROJECT'}</span>
    </button>
  );
}
