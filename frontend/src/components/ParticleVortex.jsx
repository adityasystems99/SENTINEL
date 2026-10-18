import React, { useEffect, useRef } from 'react';

/**
 * Cinematic Particle Vortex (Reference 1)
 *
 * Renders an organic 3D logarithmic spiral particle vortex converging toward
 * a gravitational singularity, with glowing cyan-blue-violet illumination,
 * spatial perspective depth, particle trail persistence, and subtle pointer tracking.
 *
 * Automatically respects prefers-reduced-motion and provides an accessible fallback.
 */
export default function ParticleVortex({ mode = 'hero', className = '', style = {} }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    // Check reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    let prefersReducedMotion = mediaQuery.matches;
    const handleMotionChange = (e) => {
      prefersReducedMotion = e.matches;
    };
    mediaQuery.addEventListener?.('change', handleMotionChange);

    // Vortex particle configuration based on mode
    const isHero = mode === 'hero';
    const PARTICLE_COUNT = isHero ? 1400 : 700;
    const FOV = 400; // Field of view for 3D projection

    // Track mouse / pointer with smooth interpolation
    let targetRotX = 0;
    let targetRotY = 0;
    let currentRotX = 0;
    let currentRotY = 0;

    const handlePointerMove = (e) => {
      const clientX = e.clientX ?? (e.touches && e.touches[0]?.clientX) ?? width / 2;
      const clientY = e.clientY ?? (e.touches && e.touches[0]?.clientY) ?? height / 2;
      const normX = (clientX - width / 2) / (width / 2);
      const normY = (clientY - height / 2) / (height / 2);
      targetRotY = normX * 0.45; // Yaw
      targetRotX = -normY * 0.35; // Pitch
    };

    window.addEventListener('mousemove', handlePointerMove, { passive: true });
    window.addEventListener('touchmove', handlePointerMove, { passive: true });

    // Handle resize
    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth || window.innerWidth;
      height = canvas.height = canvas.parentElement.clientHeight || window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Initialize 3D particles along logarithmic orbital spiral arms
    const particles = new Float32Array(PARTICLE_COUNT * 8);
    // Stride: 0:radius, 1:theta (angle), 2:z, 3:radialSpeed, 4:angularSpeed, 5:size, 6:hue, 7:alpha

    const ARMS = 3;
    const MAX_RADIUS = Math.max(width, height) * 0.75;
    const MIN_RADIUS = 18;

    function initParticle(i) {
      const offset = i * 8;
      // Exponential distribution for gravitational density near the core
      const t = Math.random();
      const r = MIN_RADIUS + Math.pow(t, 1.8) * (MAX_RADIUS - MIN_RADIUS);
      const armOffset = ((i % ARMS) * (2 * Math.PI)) / ARMS;
      // Logarithmic spiral angle theta = log(r) * b + armOffset + scatter
      const theta = Math.log(Math.max(r, 1)) * 2.2 + armOffset + (Math.random() - 0.5) * 0.6;
      // Z-depth distribution with funnel shape (flaring outward, funneling inward)
      const funnelDepth = (1 - r / MAX_RADIUS) * 120 - 40;
      const z = funnelDepth + (Math.random() - 0.5) * (r * 0.35);

      // Inward pull speed + orbital angular speed (Keplerian-like: faster near center)
      const speedFactor = 1 / Math.sqrt(Math.max(r, 20));
      const radialSpeed = 0.4 + speedFactor * 4.2;
      const angularSpeed = 0.006 + speedFactor * 0.045;

      const size = 0.8 + Math.random() * (isHero ? 2.2 : 1.6);

      // Color palette: Outer = violet (265-285), Mid = electric blue (215-235), Core = cyan/white (185-195)
      const normalizedR = (r - MIN_RADIUS) / (MAX_RADIUS - MIN_RADIUS);
      let hue = 188 + normalizedR * 85 + (Math.random() - 0.5) * 20;

      const alpha = 0.3 + Math.random() * 0.65;

      particles[offset + 0] = r;
      particles[offset + 1] = theta;
      particles[offset + 2] = z;
      particles[offset + 3] = radialSpeed;
      particles[offset + 4] = angularSpeed;
      particles[offset + 5] = size;
      particles[offset + 6] = hue;
      particles[offset + 7] = alpha;
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      initParticle(i);
    }

    // Main animation loop
    let globalAngle = 0;

    function render() {
      // Clear with persistence trail effect
      // Hero mode has deeper trails; ambient mode clears more cleanly
      ctx.fillStyle = isHero
        ? 'rgba(6, 9, 19, 0.22)'
        : 'rgba(8, 13, 24, 0.45)';
      ctx.fillRect(0, 0, width, height);

      // Smooth pointer rotation interpolation
      currentRotX += (targetRotX - currentRotX) * 0.05;
      currentRotY += (targetRotY - currentRotY) * 0.05;

      const cosY = Math.cos(currentRotY);
      const sinY = Math.sin(currentRotY);
      const cosX = Math.cos(currentRotX);
      const sinX = Math.sin(currentRotX);

      const centerX = width / 2;
      const centerY = height / 2;

      // Base time step (slow down if reduced-motion is requested)
      const dt = prefersReducedMotion ? 0.15 : 1.0;
      globalAngle += 0.002 * dt;

      // Draw subtle gravitational core glow
      const coreGradient = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        isHero ? 140 : 80
      );
      coreGradient.addColorStop(0, isHero ? 'rgba(115, 217, 245, 0.28)' : 'rgba(59, 130, 246, 0.12)');
      coreGradient.addColorStop(0.3, isHero ? 'rgba(99, 102, 241, 0.14)' : 'rgba(99, 102, 241, 0.06)');
      coreGradient.addColorStop(0.7, 'rgba(139, 92, 246, 0.04)');
      coreGradient.addColorStop(1, 'rgba(6, 9, 19, 0)');

      ctx.fillStyle = coreGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, isHero ? 140 : 80, 0, Math.PI * 2);
      ctx.fill();

      // Render & update particles
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const offset = i * 8;
        let r = particles[offset + 0];
        let theta = particles[offset + 1];
        let z = particles[offset + 2];
        const radialSpeed = particles[offset + 3];
        const angularSpeed = particles[offset + 4];
        const baseSize = particles[offset + 5];
        const hue = particles[offset + 6];
        const alpha = particles[offset + 7];

        // Gravitational dynamics: inwards spiral
        r -= radialSpeed * dt;
        theta += angularSpeed * dt;

        // Respawn at outer edge when sucked into the singularity
        if (r < MIN_RADIUS) {
          r = MAX_RADIUS * (0.85 + Math.random() * 0.15);
          theta = Math.random() * Math.PI * 2;
          z = (Math.random() - 0.5) * 80;
        }

        particles[offset + 0] = r;
        particles[offset + 1] = theta;
        particles[offset + 2] = z;

        // 3D Cartesian coordinates in vortex space
        const worldX = r * Math.cos(theta);
        const worldY = r * Math.sin(theta) * 0.55; // Elliptical inclination
        const worldZ = z + Math.sin(theta * 2 + globalAngle) * 15;

        // Apply interactive 3D rotation matrix
        // 1. Rotate around Y (yaw)
        const x1 = worldX * cosY + worldZ * sinY;
        const z1 = -worldX * sinY + worldZ * cosY;
        // 2. Rotate around X (pitch)
        const y2 = worldY * cosX - z1 * sinX;
        const z2 = worldY * sinX + z1 * cosX;

        // Perspective 3D projection
        const depth = z2 + FOV;
        if (depth <= 20) continue; // Behind camera

        const scale = FOV / depth;
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;

        // Skip off-screen particles
        if (screenX < -20 || screenX > width + 20 || screenY < -20 || screenY > height + 20) {
          continue;
        }

        // Depth-scaled size and opacity
        const particleSize = Math.max(0.6, baseSize * scale);
        const normalizedR = (r - MIN_RADIUS) / (MAX_RADIUS - MIN_RADIUS);

        // Brightness and glow increase as particles approach singularity
        const coreIntensity = (1 - normalizedR) * 0.45;
        const finalAlpha = Math.min(1.0, (alpha + coreIntensity) * (isHero ? 0.95 : 0.45));
        const lightness = 60 + (1 - normalizedR) * 30;

        ctx.beginPath();
        ctx.arc(screenX, screenY, particleSize, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${hue}, 95%, ${lightness}%, ${finalAlpha})`;
        ctx.fill();

        // Extra halo for core particles
        if (r < 90 && isHero && i % 3 === 0) {
          ctx.beginPath();
          ctx.arc(screenX, screenY, particleSize * 2.2, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${hue}, 100%, 75%, ${finalAlpha * 0.35})`;
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    }

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('resize', handleResize);
      mediaQuery.removeEventListener?.('change', handleMotionChange);
    };
  }, [mode]);

  return (
    <div
      className={`particle-vortex-container ${className}`}
      style={{
        position: mode === 'ambient' ? 'fixed' : 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: mode === 'ambient' ? 0 : 0,
        overflow: 'hidden',
        background: 'transparent',
        ...style,
      }}
      aria-hidden="true"
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
        }}
      />
    </div>
  );
}
