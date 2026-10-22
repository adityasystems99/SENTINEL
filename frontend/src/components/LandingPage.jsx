import React, { useEffect, useRef } from 'react';

export default function LandingPage({ onLaunchConsole }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;

    let animFrameId = null;
    let stepInterval = null;
    let isCleanedUp = false;

    const rm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const $ = (s) => root.querySelector(s);
    const $$ = (s) => Array.prototype.slice.call(root.querySelectorAll(s));
    const lerp = (a, b, t) => a + (b - a) * t;
    const cl = (v, a, b) => Math.min(b, Math.max(a, v));
    const H = () => window.innerHeight;
    const W = () => window.innerWidth;

    // 1. Marquee
    const logos = ['Northwind', 'Halcyon Labs', 'Ostrava', 'Kestrel', 'Lumen & Co', 'Parallax', 'Fieldwork', 'Atlas Nine'];
    const mt = $('#mt');
    if (mt) {
      const lh = logos.map((l) => `<span>${l}</span>`).join('');
      mt.innerHTML = lh + lh;
    }

    // 2. Platform horizontal scroll
    const plat = [
      ['01', 'TOPOLOGY', 'Live Incident Mesh', 'Explore distributed causal graphs and real-time telemetry topology.', 'p-mesh'],
      ['02', 'MODELS', 'Model-Agnostic RAG', 'Index runbooks and post-mortems with hybrid semantic search.', 'p-models'],
      ['03', 'REVIEW', 'Human Checkpoints', 'Pause automated remediation for human validation before production mutations.', 'p-checkpoints'],
      ['04', 'EDGE', 'Edge Ingestion', 'Sub-20ms streaming telemetry ingest for OpenTelemetry spans and logs.', 'p-edge'],
      ['05', 'RADAR', 'Architectural Radar', 'Map service dependencies and pinpoint risk hotspots before release.', 'p-versions'],
      ['06', 'TRUST', 'SOC 2 & Code Audits', 'Automated binary inspection, tenant isolation, and verified audit trails.', 'p-trust']
    ];
    const track = $('#track');
    if (track) {
      track.innerHTML = plat.map((c) =>
        `<article class="pc glass"><div class="img" style="background-image:url(/assets/${c[4]}.webp),linear-gradient(160deg,#1a1622,#0b0910)"></div><div class="shade"></div><div class="pt"><span>${c[0]}</span><span>${c[1]}</span></div><div><h3>${c[2]}</h3><p>${c[3]}</p></div></article>`
      ).join('');
    }

    // 3. Stacking Cards
    const ang = [0, 1, 2, 3, 4, 5, 6].map((i) => {
      const a = (i / 7) * 6.283 - 1.57;
      return [200 + Math.cos(a) * 105, 150 + Math.sin(a) * 95];
    });
    const hub = `<svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${ang.map((p, i) =>
      `<path class="hl" d="M200 150L${p[0]} ${p[1]}"/><path class="hp" pathLength="100" style="animation-delay:${i * 0.3}s" d="M200 150L${p[0]} ${p[1]}"/><circle cx="${p[0]}" cy="${p[1]}" r="9" fill="#15111c" stroke="#a58bff"/>`
    ).join('')}<circle cx="200" cy="150" r="20" fill="#15111c" stroke="#ff7a3d" stroke-width="2"/></svg>`;

    const chart = '<svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><path class="hl" d="M40 240H370M40 180H370M40 120H370M40 60H370"/><path class="chart" pathLength="100" d="M40 70 C100 60 120 90 170 110 S250 190 370 225"/></svg><span class="pl" style="right:12%;bottom:22%">−63% MTTR</span>';

    const gauge = '<svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><circle cx="200" cy="140" r="64" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="10"/><circle id="gc" cx="200" cy="140" r="64" fill="none" stroke="#ff7a3d" stroke-width="10" stroke-linecap="round" pathLength="100" stroke-dasharray="0 100" transform="rotate(-90 200 140)"/><text id="gt" x="200" y="148" text-anchor="middle" fill="#f2eff7" font-size="30" font-family="Geist" font-weight="500">0%</text><text x="200" y="232" text-anchor="middle" fill="#8d879a" font-size="11" font-family="Geist Mono" letter-spacing="1.5">BUDGET USED · CAP $500</text></svg><span class="pl" style="left:10%;bottom:8%">PII ✓</span><span class="pl" style="left:38%;bottom:8%">SPEND ✓</span><span class="pl" style="left:68%;bottom:8%;color:#a58bff">REVIEW 2</span>';

    const tl = `<svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${[
      [50, 160, '#ff7a3d'],
      [110, 120, '#a58bff'],
      [160, 150, '#ff7a3d'],
      [90, 170, '#a58bff'],
      [190, 110, '#ff7a3d']
    ].map((b, i) => `<rect x="${60 + b[0] * 0.6}" y="${70 + i * 34}" width="${b[1]}" height="16" rx="8" fill="${b[2]}" opacity=".75"/>`).join('')}<g class="scrub"><rect x="60" y="56" width="2" height="190" fill="#fff"/></g></svg>`;

    const steps = [
      ['01', 'Connect', 'Plug in the agents and telemetry you already run.', 's-connect', hub],
      ['02', 'Route', 'Context and traces travel with the task.', 's-route', chart],
      ['03', 'Guard', 'Policies and boundaries at every hop.', 's-guard', gauge],
      ['04', 'Trace', 'Replay any incident, step by step.', 's-trace', tl]
    ];
    const stack = $('#stack');
    if (stack) {
      stack.innerHTML = steps.map((s, i) =>
        `<article class="sc glass" style="top:calc(13vh + ${i * 20}px)"><div class="cp"><div class="n">${s[0]} / ${s[1].toUpperCase()}</div><div><h3>${s[1]}</h3><p>${s[2]}</p></div></div><div class="vp" style="background-image:url(/assets/${s[3]}.webp),linear-gradient(160deg,#1a1622,#0b0910)">${s[4]}</div><div class="ov"></div></article>`
      ).join('');
    }

    // 4. Reveal words
    const words = 'Distributed systems are getting more complex every month. The gaps between them are where work quietly breaks. SENTINEL closes those gaps.'.split(' ');
    const revp = $('#revp');
    if (revp) {
      revp.innerHTML = words.map((w) => `<span class="w${w === 'between' ? ' serif' : ''}">${w}</span>`).join(' ');
    }

    // 5. Stats
    const sd = [
      [18, 'ms', 'median triage latency', 0],
      [2.4, 'B', 'telemetry events routed', 1],
      [61, '%', 'fewer failed runs', 0],
      [900, '+', 'teams in beta', 0]
    ];
    const sg = $('#sg');
    if (sg) {
      sg.innerHTML = `<svg width="0" height="0"><defs><linearGradient id="sg"><stop offset="0" stop-color="#ff7a3d"/><stop offset="1" stop-color="#a58bff"/></linearGradient></defs></svg>` +
        sd.map((s, i) =>
          `<div class="st glass"><b data-n="${s[0]}" data-d="${s[3]}" data-s="${s[1]}">0${s[1]}</b><span>${s[2]}</span><svg viewBox="0 0 100 36" preserveAspectRatio="none" aria-hidden="true"><path pathLength="100" d="M0 30 L15 24 L30 27 L45 16 L60 19 L78 8 L100 ${4 + i}"/></svg></div>`
        ).join('');
    }

    // 6. Hero 3D flow window
    const NODES = [
      ['Anomaly detected', 'telemetry ingest', 7, 52],
      ['Root cause ranked', 'causal graph', 38, 30],
      ['Runbook generated', 'writer agent', 38, 74],
      ['Ask a human', 'waiting · 2 min', 70, 52, 1]
    ];
    const fb = $('#fbody');
    const cards = [];
    if (fb) {
      fb.querySelectorAll('.node, .fbase').forEach((el) => el.remove());
      NODES.forEach((n) => {
        const h = `<b>${n[0]}</b><small>${n[4] ? '<i class="spin"></i>' : ''}${n[1]}</small>`;
        const p = document.createElement('div');
        p.className = 'fbase';
        p.style.cssText = `left:${n[2]}%;top:${n[3]}%`;
        p.innerHTML = h;
        fb.appendChild(p);

        const c = document.createElement('div');
        c.className = 'node';
        c.style.cssText = `left:${n[2]}%;top:${n[3]}%`;
        c.innerHTML = h;
        fb.appendChild(c);
        cards.push(c);
      });
    }

    const routes = [[0, 1, 3], [0, 2, 3]];
    let ri = 0, si = 0;
    const tix = ['db-deadlock', 'login-loop', 'billing-dispute', 'api-timeout', 'pod-eviction'];
    let runs = [], tk = 4410;

    function setOn(i) {
      cards.forEach((c, k) => c.classList.toggle('on', k === i));
    }

    function step() {
      if (isCleanedUp) return;
      const r = routes[ri];
      setOn(r[si]);
      si++;
      if (si > r.length) {
        si = 0;
        ri = 1 - ri;
        tk += 1 + Math.floor(Math.random() * 7);
        const ms = 18 + Math.floor(Math.random() * 22);
        const d = new Date();
        runs.unshift(`<div><span>${d.toTimeString().slice(0, 8)}</span><span>#${tk} ${tix[tk % 5]}</span><em>${ms}ms ✓</em></div>`);
        runs = runs.slice(0, 3);
        const runsEl = $('#runs');
        if (runsEl) runsEl.innerHTML = runs.join('');
        const c2 = $('#c2');
        if (c2) c2.textContent = ms;
        const c1 = $('#c1');
        if (c1) c1.textContent = (1284 + tk - 4410).toLocaleString('en-US');
      }
    }

    let hv = true;
    function run() {
      if (!stepInterval && !rm) stepInterval = setInterval(step, 900);
    }
    function halt() {
      clearInterval(stepInterval);
      stepInterval = null;
    }

    if (rm) setOn(3);

    const heroObserver = new IntersectionObserver((e) => {
      hv = e[0].isIntersecting;
      hv ? run() : halt();
    });
    const heroEl = $('#hero');
    if (heroEl) heroObserver.observe(heroEl);

    const stage = $('#stage');
    const rig = $('#rig');
    const layers = $$('.layer').map((l, i) => ({ el: l, d: +l.dataset.depth, x: 0, y: 0, e: 0.06 + i * 0.025 }));
    let tx = 0, ty = 0, cx = 0, cy = 0, idle = 0, touch = false;
    const gl = $('#glare');

    const handlePointerMove = (e) => {
      if (!stage || e.pointerType === 'touch') return;
      const r = stage.getBoundingClientRect();
      tx = cl(((e.clientX - r.left) / r.width) * 2 - 1, -1, 1);
      ty = cl(((e.clientY - r.top) / r.height) * 2 - 1, -1, 1);
      idle = 0;
    };
    window.addEventListener('pointermove', handlePointerMove, { passive: true });

    const handleTouchStart = () => { touch = true; };
    window.addEventListener('touchstart', handleTouchStart, { passive: true });

    function hero(t) {
      if (!hv || rm || !rig) return;
      idle++;
      if (touch || idle > 90) {
        tx = Math.sin(t / 2800) * 0.3;
        ty = Math.cos(t / 3300) * 0.2;
      }
      cx = lerp(cx, tx, 0.07);
      cy = lerp(cy, ty, 0.07);
      const sc = cl(sy / H(), 0, 1);

      rig.style.transform = `rotateY(${-16 * (1 - sc * 0.5) + cx * 13}deg) rotateX(${7 - cy * 9}deg) translateY(${sc * -40}px)`;

      layers.forEach((l, i) => {
        l.x = lerp(l.x, cx, l.e);
        l.y = lerp(l.y, cy, l.e);
        const k = l.d / 100;
        l.el.style.transform = `translate3d(${l.x * k * 40}px,${l.y * k * 30}px,${l.d}px)`;
        if (i === 0) {
          cards.forEach((c, j) => {
            c.style.setProperty('--px', `${l.x * (16 + j * 4)}px`);
            c.style.setProperty('--py', `${l.y * (12 + j * 3)}px`);
          });
          if (gl) {
            gl.style.setProperty('--gx', `${50 + l.x * 50}%`);
            gl.style.setProperty('--gy', `${50 + l.y * 50}%`);
          }
        }
      });
    }

    if (rm && rig) rig.style.transform = 'rotateY(-16deg) rotateX(7deg)';

    // 7. Scroll calculations
    const vid = $('#bgVideo');
    const veil = $('#veil');
    let sy = window.scrollY;
    const plS = $('#platform');
    const pfill = $('#pfill');
    let dist = 0;
    const scEls = $$('.sc');
    const wEls = $$('#revp .w');
    const revS = $('#rev');

    function size() {
      if (!track || !plS) return;
      dist = Math.max(0, track.scrollWidth - W());
      plS.style.height = `${H() + dist}px`;
    }
    window.addEventListener('resize', size);
    size();

    function scroll() {
      sy = rm ? window.scrollY : lerp(sy, window.scrollY, 0.075);
      if (!rm && vid) {
        vid.style.transform = `translate3d(${Math.sin(sy / 700) * 7 + Math.sin(sy / 1900) * 3}vw,${Math.sin(sy / 1300) * -2}vh,0) scale(${1.02 + Math.abs(Math.sin(sy / 1600)) * 0.04}) rotate(${Math.sin(sy / 1100) * -1.2}deg)`;
      }
      if (vid) vid.style.opacity = 0.6 * (1 - cl(sy / H(), 0, 1) * 0.6);
      if (veil) veil.style.opacity = cl((sy - H() * 0.12) / (H() * 0.45), 0, 1) * 0.97;

      if (plS && track) {
        const r = plS.getBoundingClientRect();
        const p = cl(-r.top / Math.max(1, r.height - H()), 0, 1);
        track.style.transform = `translate3d(${-p * dist}px,0,0)`;
        if (pfill) pfill.style.width = `${p * 100}%`;
      }

      scEls.forEach((c, i) => {
        const n = scEls[i + 1];
        let pp = 0;
        if (n) {
          const top = parseFloat(getComputedStyle(n).top);
          const tp = n.getBoundingClientRect().top;
          pp = cl(1 - (tp - top) / c.offsetHeight, 0, 1);
        }
        const depth = scEls.length - 1 - i || 1;
        c.style.transform = `scale(${1 - pp * 0.035 * depth})`;
        if (c.lastChild) c.lastChild.style.opacity = pp * 0.55;
      });

      if (revS) {
        const rr = revS.getBoundingClientRect();
        const rp = cl(-rr.top / Math.max(1, rr.height - H()), 0, 1);
        const lit = rm ? words.length : Math.floor(rp * words.length * 1.15);
        wEls.forEach((w, i) => w.classList.toggle('l', i < lit));
      }
    }

    function count(el) {
      const n = +el.dataset.n;
      const d = +el.dataset.d;
      const s = el.dataset.s;
      const t0 = performance.now();
      if (rm) {
        el.textContent = n.toFixed(d) + s;
        return;
      }
      (function f(t) {
        const k = cl((t - t0) / 1600, 0, 1);
        el.textContent = (n * (1 - Math.pow(1 - k, 3))).toFixed(d) + s;
        if (k < 1) requestAnimationFrame(f);
      })(t0);
    }

    function runGauge(v) {
      const gc = v.querySelector('#gc');
      const gt = v.querySelector('#gt');
      if (!gc) return;
      const t0 = performance.now();
      (function f(t) {
        const k = rm ? 1 : cl((t - t0) / 1800, 0, 1);
        const val = 72 * (1 - Math.pow(1 - k, 3));
        gc.setAttribute('stroke-dasharray', `${val} 100`);
        gt.textContent = `${Math.round(val)}%`;
        if (k < 1) requestAnimationFrame(f);
      })(t0);
    }

    const io = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        e.target.classList.add('in');
        const b = e.target.querySelector('b');
        if (b) count(b);
        if (e.target.classList.contains('vp')) runGauge(e.target);
      });
    }, { threshold: 0.35 });

    $$('.st,.vp').forEach((x) => io.observe(x));

    function loop(t) {
      if (isCleanedUp) return;
      scroll();
      hero(t || 0);
      animFrameId = requestAnimationFrame(loop);
    }
    animFrameId = requestAnimationFrame(loop);

    return () => {
      isCleanedUp = true;
      if (animFrameId) cancelAnimationFrame(animFrameId);
      halt();
      heroObserver.disconnect();
      io.disconnect();
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('resize', size);
    };
  }, []);

  return (
    <div ref={containerRef} className="sentinel-landing-container">
      <style>{`
        .sentinel-landing-container {
          --bg: #07060a;
          --bg-2: #0e0c13;
          --text: #f2eff7;
          --muted: #8d879a;
          --line: rgba(255,255,255,.09);
          --accent: #ff7a3d;
          --accent-2: #a58bff;
          --ok: #7be3a6;
          --glass: linear-gradient(155deg,rgba(255,255,255,.085),rgba(255,255,255,.025) 45%,rgba(255,255,255,.04));
          --glass-border: rgba(255,255,255,.12);
          --glass-blur: blur(22px) saturate(150%);
          --radius: 22px;
          --gutter: clamp(16px,4vw,48px);
          --maxw: 1280px;
          background: var(--bg);
          color: var(--text);
          font-family: 'Geist', system-ui, sans-serif;
          min-height: 100vh;
          overflow-x: hidden;
          position: relative;
        }
        .sentinel-landing-container::after {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 100;
          opacity: .05;
          background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E");
        }
        .sentinel-landing-container a { color: inherit; text-decoration: none; }
        .sentinel-landing-container button { font: inherit; color: inherit; cursor: pointer; border: 0; background: none; }
        .sentinel-landing-container .serif { font-family: 'Instrument Serif', serif; font-style: italic; font-weight: 400; color: var(--accent); }
        .sentinel-landing-container .mono { font-family: 'Geist Mono', monospace; }
        .sentinel-landing-container .glass {
          background: var(--glass);
          border: 1px solid var(--glass-border);
          backdrop-filter: var(--glass-blur);
          -webkit-backdrop-filter: var(--glass-blur);
          box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 30px 70px -20px rgba(0,0,0,.7);
        }
        .sentinel-landing-container .wrap { max-width: var(--maxw); margin: 0 auto; padding: 0 var(--gutter); }
        .sentinel-landing-container .eyebrow {
          font: 500 12px 'Geist Mono', monospace;
          letter-spacing: .14em;
          text-transform: uppercase;
          color: var(--accent);
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .sentinel-landing-container .eyebrow::before { content: ""; width: 22px; height: 1px; background: currentColor; }
        .sentinel-landing-container h2 {
          font-weight: 500;
          font-size: clamp(30px, 4.2vw, 58px);
          line-height: 1.05;
          letter-spacing: -.03em;
          margin-top: 18px;
          max-width: 18em;
        }
        .sentinel-landing-container .btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 14px 24px;
          border-radius: 999px;
          font-weight: 500;
          font-size: 15px;
          transition: transform .3s, box-shadow .3s;
        }
        .sentinel-landing-container .btn:hover { transform: translateY(-2px); }
        .sentinel-landing-container .btn.solid {
          background: #f2eff7;
          color: #07060a;
          box-shadow: 0 10px 30px -8px rgba(255,122,61,.5);
        }
        .sentinel-landing-container .btn.ghost { border-radius: 999px; }
        .sentinel-landing-container #bgVideo {
          position: fixed;
          top: -4vh;
          left: -12vw;
          width: 124vw;
          height: 108vh;
          object-fit: cover;
          opacity: .6;
          z-index: 0;
          pointer-events: none;
          -webkit-mask-image: linear-gradient(90deg, rgba(0,0,0,.35) 0%, rgba(0,0,0,.6) 35%, #000 70%);
          mask-image: linear-gradient(90deg, rgba(0,0,0,.35) 0%, rgba(0,0,0,.6) 35%, #000 70%);
          will-change: transform;
        }
        .sentinel-landing-container #veil {
          position: fixed;
          inset: 0;
          background: #07060a;
          opacity: 0;
          z-index: 1;
          pointer-events: none;
        }
        .sentinel-landing-container main, .sentinel-landing-container footer, .sentinel-landing-container nav {
          position: relative;
          z-index: 2;
        }
        .sentinel-landing-container nav {
          position: fixed;
          top: 14px;
          left: var(--gutter);
          right: var(--gutter);
          z-index: 50;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 12px 10px 20px;
          border-radius: 999px;
          max-width: var(--maxw);
          margin: 0 auto;
        }
        .sentinel-landing-container .logo {
          display: flex;
          align-items: center;
          gap: 10px;
          font-weight: 600;
          letter-spacing: -.02em;
          font-size: 18px;
        }
        .sentinel-landing-container .logo i {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: conic-gradient(var(--accent), var(--accent-2), var(--accent));
          -webkit-mask: radial-gradient(circle, transparent 5px, #000 6px);
          mask: radial-gradient(circle, transparent 5px, #000 6px);
        }
        .sentinel-landing-container .links {
          display: flex;
          gap: 30px;
          font-size: 14px;
          color: var(--muted);
        }
        .sentinel-landing-container .links a:hover { color: var(--text); }
        .sentinel-landing-container .nbtn {
          padding: 9px 18px;
          border-radius: 999px;
          background: var(--text);
          color: var(--bg);
          font-size: 14px;
          font-weight: 500;
          transition: transform .2s ease;
        }
        .sentinel-landing-container .nbtn:hover { transform: scale(1.04); }

        /* hero */
        .sentinel-landing-container .hero {
          position: relative;
          min-height: 100svh;
          display: grid;
          grid-template-columns: 1.05fr 1fr;
          align-items: center;
          gap: 20px;
          max-width: var(--maxw);
          margin: 0 auto;
          padding: 120px var(--gutter) 60px;
        }
        .sentinel-landing-container .hero::before {
          content: "";
          position: absolute;
          inset: 0;
          background: radial-gradient(ellipse 55% 60% at 18% 52%, rgba(7,6,10,.78), transparent 75%);
          pointer-events: none;
          z-index: -1;
        }
        .sentinel-landing-container .pill {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 7px 14px;
          border-radius: 999px;
          font: 500 12px 'Geist Mono', monospace;
          letter-spacing: .06em;
          text-transform: uppercase;
        }
        .sentinel-landing-container .dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--ok);
          box-shadow: 0 0 10px var(--ok);
          animation: blink 1.4s infinite;
        }
        @keyframes blink { 50% { opacity: .25; } }
        .sentinel-landing-container h1 {
          font-weight: 500;
          font-size: clamp(44px, 6.4vw, 100px);
          line-height: .98;
          letter-spacing: -.04em;
          margin: 26px 0 24px;
        }
        .sentinel-landing-container h1 .ln { display: block; overflow: hidden; padding-bottom: .08em; }
        .sentinel-landing-container h1 .ln > span {
          display: block;
          transform: translateY(105%);
          animation: rise 1.1s cubic-bezier(.2,.8,.2,1) forwards;
        }
        .sentinel-landing-container h1 .ln:nth-child(2) > span { animation-delay: .1s; }
        .sentinel-landing-container h1 .ln:nth-child(3) > span { animation-delay: .2s; }
        @keyframes rise { to { transform: none; } }
        .sentinel-landing-container .lede {
          color: var(--muted);
          font-size: clamp(16px, 1.35vw, 19px);
          max-width: 34em;
        }
        .sentinel-landing-container .cta-row {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
          margin: 34px 0;
        }
        .sentinel-landing-container .meta {
          display: flex;
          gap: 28px;
          flex-wrap: wrap;
          font: 400 13px 'Geist Mono', monospace;
          color: var(--muted);
        }
        .sentinel-landing-container .meta b { color: var(--text); font-weight: 500; }
        .sentinel-landing-container .stage {
          perspective: 1497px;
          height: clamp(360px, 34vw, 440px);
          margin-right: calc(-1 * var(--gutter) - 6vw);
          position: relative;
        }
        .sentinel-landing-container .rig, .sentinel-landing-container .layer {
          position: absolute;
          inset: 0;
          transform-style: preserve-3d;
          will-change: transform;
        }
        .sentinel-landing-container .flow {
          position: absolute;
          top: -2%;
          left: 0;
          width: 106%;
          height: 115%;
          border-radius: 18px;
          background: linear-gradient(160deg, rgba(26,22,34,.96), rgba(11,9,16,.95) 45%, rgba(15,13,21,.96));
          border: 1px solid var(--glass-border);
          box-shadow: inset 0 1px 0 rgba(255,255,255,.14), 0 40px 80px -20px #000;
          overflow: hidden;
          -webkit-mask-image: linear-gradient(90deg, #000 70%, transparent);
          mask-image: linear-gradient(90deg, #000 70%, transparent);
        }
        .sentinel-landing-container .fbar {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 11px 16px;
          border-bottom: 1px solid var(--line);
          font-size: 12.5px;
        }
        .sentinel-landing-container .fbar span:nth-child(2) {
          color: var(--muted);
          font-family: 'Geist Mono', monospace;
          font-size: 11px;
        }
        .sentinel-landing-container .live {
          margin-left: auto;
          display: inline-flex;
          gap: 6px;
          align-items: center;
          padding: 3px 9px;
          border-radius: 99px;
          background: rgba(123,227,166,.12);
          color: var(--ok);
          font: 500 10px 'Geist Mono', monospace;
          letter-spacing: .1em;
        }
        .sentinel-landing-container .fbody {
          position: absolute;
          inset: 41px 0 0;
          background-image: radial-gradient(rgba(255,255,255,.1) 1px, transparent 1.2px);
          background-size: 18px 18px;
        }
        .sentinel-landing-container .tools {
          position: absolute;
          top: 12px;
          left: 12px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding: 4px;
          border-radius: 9px;
          background: rgba(255,255,255,.05);
          border: 1px solid var(--line);
          font-size: 13px;
        }
        .sentinel-landing-container .tools i {
          width: 26px;
          height: 26px;
          display: grid;
          place-items: center;
          font-style: normal;
          border-radius: 6px;
        }
        .sentinel-landing-container .tools i:first-child { background: rgba(255,255,255,.1); }
        .sentinel-landing-container .zoom {
          position: absolute;
          bottom: 10px;
          left: 12px;
          font: 11px 'Geist Mono', monospace;
          color: var(--muted);
          padding: 3px 8px;
          border: 1px solid var(--line);
          border-radius: 6px;
        }
        .sentinel-landing-container .wires { position: absolute; inset: 0; width: 100%; height: 100%; }
        .sentinel-landing-container .wires path { fill: none; vector-effect: non-scaling-stroke; }
        .sentinel-landing-container .w { stroke: rgba(255,255,255,.16); stroke-width: 1.2; }
        .sentinel-landing-container .pu {
          stroke-width: 2.2;
          stroke-dasharray: 7 93;
          stroke-dashoffset: 100;
          animation: pul 2.4s linear infinite;
          filter: drop-shadow(0 0 4px currentColor);
        }
        @keyframes pul { to { stroke-dashoffset: 0; } }
        .sentinel-landing-container .wl {
          position: absolute;
          font: 10px 'Geist Mono', monospace;
          color: var(--muted);
          padding: 1px 6px;
          border-radius: 5px;
          background: var(--bg-2);
          border: 1px solid var(--line);
        }
        .sentinel-landing-container .node, .sentinel-landing-container .fbase {
          position: absolute;
          width: 23%;
          padding: 12px 11px;
          border-radius: 9px;
        }
        .sentinel-landing-container .node {
          background: linear-gradient(160deg, #241f2e, #15111c);
          border: 1px solid rgba(255,255,255,.14);
          transform: translate(calc(-14px + var(--px,0px)), calc(-50% - 30px + var(--py,0px)));
          box-shadow: -10px 32px 34px -12px rgba(0,0,0,.8);
          transition: border-color .3s, box-shadow .3s;
        }
        .sentinel-landing-container .node.on {
          border-color: var(--accent);
          box-shadow: -10px 32px 34px -12px rgba(0,0,0,.8), 0 0 22px rgba(255,122,61,.4);
        }
        .sentinel-landing-container .node b { display: block; font-weight: 500; font-size: 12px; }
        .sentinel-landing-container .node small {
          display: flex;
          align-items: center;
          gap: 6px;
          font: 10px 'Geist Mono', monospace;
          color: var(--muted);
          margin-top: 2px;
        }
        .sentinel-landing-container .fbase {
          transform: translateY(-50%);
          border: 1px dashed rgba(255,255,255,.14);
          background: rgba(255,255,255,.02);
          box-shadow: inset 0 2px 14px rgba(0,0,0,.6);
        }
        .sentinel-landing-container .fbase * { visibility: hidden; }
        .sentinel-landing-container .fbase::before, .sentinel-landing-container .fbase::after {
          content: "";
          position: absolute;
          top: 50%;
          width: 7px;
          height: 7px;
          margin-top: -3.5px;
          border-radius: 50%;
          background: #2a2433;
          border: 1px solid rgba(255,255,255,.25);
        }
        .sentinel-landing-container .fbase::before { left: -4px; }
        .sentinel-landing-container .fbase::after { right: -4px; }
        .sentinel-landing-container .spin {
          width: 9px;
          height: 9px;
          border-radius: 50%;
          border: 1.5px solid var(--accent-2);
          border-top-color: transparent;
          animation: sp 1s linear infinite;
        }
        @keyframes sp { to { transform: rotate(360deg); } }
        .sentinel-landing-container .runs {
          position: absolute;
          left: 44%;
          bottom: 7%;
          width: 30%;
          font: 10px 'Geist Mono', monospace;
          color: var(--muted);
          transform: translateX(-50%);
        }
        .sentinel-landing-container .runs h6 { font: inherit; letter-spacing: .12em; margin-bottom: 4px; }
        .sentinel-landing-container .runs div {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          padding: 2px 0;
          border-top: 1px solid var(--line);
        }
        .sentinel-landing-container .runs em { font-style: normal; color: var(--ok); }
        .sentinel-landing-container .glare {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(circle 220px at var(--gx,50%) var(--gy,30%), rgba(255,255,255,.1), transparent 70%);
        }
        .sentinel-landing-container .chip {
          position: absolute;
          padding: 8px 14px;
          border-radius: 999px;
          font: 12px 'Geist Mono', monospace;
          white-space: nowrap;
        }
        .sentinel-landing-container .chip i { font-style: normal; color: var(--ok); }
        .sentinel-landing-container .chip1 { left: 46%; top: -3%; }
        .sentinel-landing-container .chip2 { left: -6%; bottom: -17%; }

        /* marquee */
        .sentinel-landing-container .marq {
          position: relative;
          overflow: hidden;
          border-block: 1px solid var(--line);
          padding: 26px 0;
          background: rgba(7,6,10,.6);
        }
        .sentinel-landing-container .mt {
          display: flex;
          width: max-content;
          animation: mq 40s linear infinite;
        }
        .sentinel-landing-container .mt span {
          padding: 0 40px;
          font: 500 20px 'Geist', sans-serif;
          letter-spacing: -.02em;
          color: var(--muted);
          white-space: nowrap;
        }
        @keyframes mq { to { transform: translateX(-50%); } }

        /* platform */
        .sentinel-landing-container .plat { position: relative; background: var(--bg); }
        .sentinel-landing-container .pin {
          position: sticky;
          top: 0;
          height: 100svh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 34px;
        }
        .sentinel-landing-container .phead { padding: 0 var(--gutter); max-width: var(--maxw); margin: 0 auto; width: 100%; }
        .sentinel-landing-container .track { display: flex; gap: 22px; padding: 0 var(--gutter); width: max-content; will-change: transform; }
        .sentinel-landing-container .pc {
          position: relative;
          flex: 0 0 min(78vw, 380px);
          aspect-ratio: 4/5;
          border-radius: var(--radius);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: 22px;
        }
        .sentinel-landing-container .pc .img {
          position: absolute;
          inset: 0;
          background-size: cover;
          background-position: center;
          transform: scale(1.02);
          transition: transform 1.2s;
        }
        .sentinel-landing-container .pc:hover .img { transform: scale(1.08); }
        .sentinel-landing-container .pc .shade {
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(7,6,10,.7) 0, transparent 25%, transparent 45%, rgba(7,6,10,.92) 82%);
        }
        .sentinel-landing-container .pc > *:not(.img):not(.shade) { position: relative; }
        .sentinel-landing-container .pt { display: flex; justify-content: space-between; font: 12px 'Geist Mono', monospace; color: var(--muted); }
        .sentinel-landing-container .pt span:last-child {
          padding: 3px 10px;
          border: 1px solid var(--line);
          border-radius: 99px;
          letter-spacing: .1em;
        }
        .sentinel-landing-container .pc h3 { font-weight: 500; font-size: 26px; letter-spacing: -.02em; }
        .sentinel-landing-container .pc p { color: #b9b3c6; font-size: 14.5px; margin-top: 6px; }
        .sentinel-landing-container .pbar { height: 1px; background: var(--line); margin: 0 var(--gutter); max-width: var(--maxw); }
        .sentinel-landing-container .pbar i {
          display: block;
          height: 100%;
          width: 0;
          background: linear-gradient(90deg, var(--accent), var(--accent-2));
        }

        /* how */
        .sentinel-landing-container .how { padding: 120px 0 140px; background: var(--bg); }
        .sentinel-landing-container .stack { margin-top: 60px; display: flex; flex-direction: column; gap: 6vh; }
        .sentinel-landing-container .sc {
          position: sticky;
          min-height: min(66vh, 540px);
          border-radius: var(--radius);
          display: grid;
          grid-template-columns: 1fr 1fr;
          overflow: hidden;
          background: var(--bg-2);
          transform-origin: center top;
        }
        .sentinel-landing-container .sc .ov { position: absolute; inset: 0; background: #07060a; opacity: 0; pointer-events: none; z-index: 3; }
        .sentinel-landing-container .sc .cp {
          padding: clamp(24px, 4vw, 56px);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          gap: 30px;
          position: relative;
          z-index: 1;
        }
        .sentinel-landing-container .sc .n { font: 12px 'Geist Mono', monospace; color: var(--accent); letter-spacing: .12em; }
        .sentinel-landing-container .sc h3 { font-weight: 500; font-size: clamp(34px, 4vw, 56px); letter-spacing: -.03em; }
        .sentinel-landing-container .sc p { color: var(--muted); font-size: 18px; margin-top: 10px; }
        .sentinel-landing-container .vp {
          position: relative;
          margin: 14px;
          border-radius: 16px;
          overflow: hidden;
          border: 1px solid var(--line);
          background-size: cover;
          background-position: center;
        }
        .sentinel-landing-container .vp::before { content: ""; position: absolute; inset: 0; background: linear-gradient(rgba(7,6,10,.35), rgba(7,6,10,.6)); }
        .sentinel-landing-container .vp svg { position: absolute; inset: 0; width: 100%; height: 100%; }
        .sentinel-landing-container .vp .pl {
          position: absolute;
          padding: 5px 11px;
          border-radius: 99px;
          font: 500 11px 'Geist Mono', monospace;
          background: rgba(7,6,10,.7);
          border: 1px solid var(--glass-border);
          color: var(--ok);
        }
        .sentinel-landing-container .hl { stroke: rgba(255,255,255,.16); stroke-width: 1; fill: none; }
        .sentinel-landing-container .hp { stroke: var(--accent); stroke-width: 2.4; fill: none; stroke-dasharray: 6 94; animation: pul 2.2s linear infinite; }
        .sentinel-landing-container .chart {
          fill: none;
          stroke: var(--accent);
          stroke-width: 2.5;
          stroke-dasharray: 100;
          stroke-dashoffset: 100;
          transition: stroke-dashoffset 2s ease;
        }
        .sentinel-landing-container .in .chart { stroke-dashoffset: 0; }
        .sentinel-landing-container .scrub { animation: scr 5s linear infinite; }
        @keyframes scr { from { transform: translateX(0); } to { transform: translateX(250px); } }

        /* reveal */
        .sentinel-landing-container .rev { height: 220vh; position: relative; background: var(--bg); }
        .sentinel-landing-container .rev .pin { align-items: center; justify-content: center; }
        .sentinel-landing-container .rev p {
          max-width: 960px;
          padding: 0 var(--gutter);
          font-weight: 500;
          font-size: clamp(28px, 4.4vw, 62px);
          line-height: 1.12;
          letter-spacing: -.03em;
          text-align: center;
        }
        .sentinel-landing-container .rev .w { opacity: .12; transition: opacity .4s; stroke: none; }
        .sentinel-landing-container .rev .w.l { opacity: 1; }

        /* stats */
        .sentinel-landing-container .stats {
          position: relative;
          background: var(--bg);
          padding: clamp(96px, 14vh, 150px) 0 clamp(80px, 12vh, 130px);
        }
        .sentinel-landing-container .stats::before, .sentinel-landing-container .stats::after {
          content: "";
          position: absolute;
          left: 0;
          right: 0;
          pointer-events: none;
        }
        .sentinel-landing-container .stats::before { bottom: 100%; height: 120px; background: linear-gradient(transparent, var(--bg)); }
        .sentinel-landing-container .stats::after { top: 100%; height: 100px; background: linear-gradient(var(--bg), transparent); }
        .sentinel-landing-container .sg { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
        .sentinel-landing-container .st { border-radius: var(--radius); padding: 28px 24px 20px; }
        .sentinel-landing-container .st b {
          display: block;
          font-weight: 500;
          font-size: clamp(40px, 4.4vw, 64px);
          letter-spacing: -.04em;
          line-height: 1;
        }
        .sentinel-landing-container .st span { display: block; color: var(--muted); font-size: 14px; margin: 8px 0 18px; }
        .sentinel-landing-container .st svg { width: 100%; height: 36px; overflow: visible; }
        .sentinel-landing-container .st path {
          fill: none;
          stroke: url(#sg);
          stroke-width: 2;
          stroke-dasharray: 100;
          stroke-dashoffset: 100;
          transition: stroke-dashoffset 1.8s ease;
        }
        .sentinel-landing-container .st.in path { stroke-dashoffset: 0; }

        /* cta */
        .sentinel-landing-container .cta { padding: 60px 0 120px; position: relative; background: var(--bg); }
        .sentinel-landing-container .cp2 {
          border-radius: 32px;
          overflow: hidden;
          position: relative;
          text-align: center;
          padding: clamp(70px, 12vw, 150px) 24px;
          background: url(/assets/bg-cta.webp) center bottom/cover, var(--bg-2);
        }
        .sentinel-landing-container .cp2::before {
          content: "";
          position: absolute;
          inset: 0;
          background: radial-gradient(ellipse at center, rgba(7,6,10,.7), rgba(7,6,10,.35) 70%);
        }
        .sentinel-landing-container .cp2 > * { position: relative; }
        .sentinel-landing-container .cp2 .eyebrow { justify-content: center; }
        .sentinel-landing-container .cp2 h2 { margin: 18px auto 34px; }
        .sentinel-landing-container .cp2 .cta-row { justify-content: center; margin: 0; }

        /* footer */
        .sentinel-landing-container footer {
          background: #050408;
          border-top: 1px solid var(--line);
          padding: 80px 0 30px;
          overflow: hidden;
        }
        .sentinel-landing-container .fg { display: grid; grid-template-columns: 1.6fr repeat(4, 1fr); gap: 40px; }
        .sentinel-landing-container .fg p { color: var(--muted); font-size: 14.5px; max-width: 26em; margin: 14px 0 20px; }
        .sentinel-landing-container .fg h4 {
          font: 500 11px 'Geist Mono', monospace;
          letter-spacing: .14em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 16px;
        }
        .sentinel-landing-container .fg li { list-style: none; margin: 9px 0; font-size: 14.5px; }
        .sentinel-landing-container .fg li a { color: #cfc9da; }
        .sentinel-landing-container .fg li a:hover { color: var(--accent); }
        .sentinel-landing-container .wm { width: 100%; margin: 60px 0 10px; display: block; }
        .sentinel-landing-container .wm text { font: 600 230px 'Geist', sans-serif; letter-spacing: -6px; }
        .sentinel-landing-container .wb { fill: rgba(255,255,255,.035); stroke: rgba(255,255,255,.16); stroke-width: 1; }
        .sentinel-landing-container .wd {
          fill: none;
          stroke: rgba(255,255,255,.55);
          stroke-width: 2;
          stroke-dasharray: .1 16;
          stroke-linecap: round;
          animation: wd 6s linear infinite;
        }
        .sentinel-landing-container .wr {
          fill: none;
          stroke: url(#wg);
          stroke-width: 3;
          stroke-dasharray: 90 420;
          stroke-linecap: round;
          animation: wr 7s linear infinite;
          filter: drop-shadow(0 0 6px var(--accent));
        }
        @keyframes wd { to { stroke-dashoffset: -161; } }
        @keyframes wr { to { stroke-dashoffset: -1020; } }
        .sentinel-landing-container .fb {
          display: flex;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 16px;
          border-top: 1px solid var(--line);
          padding-top: 24px;
          color: var(--muted);
          font-size: 13.5px;
        }
        .sentinel-landing-container .fb div { display: flex; gap: 22px; }
        .sentinel-landing-container .fb a:hover { color: var(--text); }

        @media(max-width:1000px){
          .sentinel-landing-container .hero { grid-template-columns: 1fr; }
          .sentinel-landing-container .stage { height: 380px; margin-right: 0; }
          .sentinel-landing-container .sg { grid-template-columns: repeat(2, 1fr); }
        }
        @media(max-width:900px){
          .sentinel-landing-container .fg { grid-template-columns: 1fr 1fr; }
          .sentinel-landing-container .fg > div:first-child { grid-column: 1/-1; }
        }
        @media(max-width:760px){
          .sentinel-landing-container .links { display: none; }
          .sentinel-landing-container .sc { grid-template-columns: 1fr; }
          .sentinel-landing-container .vp { order: -1; min-height: 260px; }
        }
        @media(max-width:560px){
          .sentinel-landing-container .stage { height: 300px; }
          .sentinel-landing-container .flow { width: 150%; }
          .sentinel-landing-container .chip { display: none; }
        }
      `}</style>

      <video id="bgVideo" autoPlay muted loop playsInline poster="/assets/hero-poster.jpg" aria-hidden="true">
        <source src="/assets/hero.webm" type="video/webm" />
        <source src="/assets/hero.mp4" type="video/mp4" />
      </video>
      <div id="veil" aria-hidden="true"></div>

      <nav className="glass" aria-label="Main">
        <a className="logo" href="#top"><i></i>SENTINEL</a>
        <div className="links">
          <a href="#how">How it works</a>
          <a href="#platform">Platform</a>
          <a href="#customers">Customers</a>
          <a href="#docs">Docs</a>
        </div>
        <button type="button" className="nbtn" onClick={onLaunchConsole}>
          Launch Console
        </button>
      </nav>

      <main id="top">
        <section className="hero" id="hero">
          <div>
            <span className="pill glass"><span className="dot"></span>Now in public beta</span>
            <h1>
              <span className="ln"><span>Every signal,</span></span>
              <span className="ln"><span>one <em className="serif">clean</em></span></span>
              <span className="ln"><span>resolution.</span></span>
            </h1>
            <p className="lede">
              SENTINEL ingests telemetry, correlates distributed incident graphs, and ranks root causes in real time, so nothing gets dropped between steps and every decision stays traceable.
            </p>
            <div className="cta-row">
              <button type="button" className="btn solid" onClick={onLaunchConsole}>Start investigating →</button>
              <a className="btn ghost glass" href="#how">See how it works</a>
            </div>
            <div className="meta">
              <span><b>18ms</b> median triage</span>
              <span><b>99.4%</b> run success</span>
              <span><b>900+</b> teams</span>
            </div>
          </div>

          <div className="stage" id="stage" aria-hidden="true">
            <div className="rig" id="rig">
              <div className="layer" data-depth="0">
                <div className="flow">
                  <div className="fbar">
                    <span>Incident triage</span>
                    <span>4 services · 1 anomaly</span>
                    <span className="live"><span className="dot"></span>LIVE</span>
                  </div>
                  <div className="fbody" id="fbody">
                    <div className="tools"><i>↖</i><i>⟲</i></div>
                    <div className="zoom">100%</div>
                    <svg className="wires" viewBox="0 0 100 100" preserveAspectRatio="none">
                      <g>
                        <path className="w" d="M28 52 C33 52 32 30 38 30" />
                        <path className="w" d="M28 52 C33 52 32 74 38 74" />
                        <path className="w" d="M59 30 C65 30 64 52 70 52" />
                        <path className="w" d="M59 74 C65 74 64 52 70 52" />
                      </g>
                      <path className="pu" style={{ color: '#ff7a3d', stroke: '#ff7a3d' }} pathLength="100" d="M28 52 C33 52 32 30 38 30" />
                      <path className="pu" style={{ color: '#a58bff', stroke: '#a58bff', animationDelay: '.6s' }} pathLength="100" d="M28 52 C33 52 32 74 38 74" />
                      <path className="pu" style={{ color: '#ff7a3d', stroke: '#ff7a3d', animationDelay: '1.2s' }} pathLength="100" d="M59 30 C65 30 64 52 70 52" />
                      <path className="pu" style={{ color: '#a58bff', stroke: '#a58bff', animationDelay: '1.8s' }} pathLength="100" d="M59 74 C65 74 64 52 70 52" />
                    </svg>
                    <span className="wl" style={{ left: '29%', top: '30%' }}>critical</span>
                    <span className="wl" style={{ left: '29%', top: '68%' }}>warning</span>
                    <div className="runs">
                      <h6>LAST INCIDENTS</h6>
                      <div id="runs"></div>
                    </div>
                  </div>
                  <div className="glare" id="glare"></div>
                </div>
              </div>
              <div className="layer" data-depth="90">
                <div className="chip chip1 glass"><i>●</i> <span id="c1">1,284</span> incidents resolved today</div>
              </div>
              <div className="layer" data-depth="140">
                <div className="chip chip2 glass"><i>●</i> telemetry → root-cause · <span id="c2">18</span> ms</div>
              </div>
            </div>
          </div>
        </section>

        <div className="marq" id="customers" aria-label="Customers">
          <div className="mt" id="mt"></div>
        </div>

        <section className="plat" id="platform">
          <div className="pin">
            <div className="phead">
              <div className="eyebrow">Platform</div>
              <h2>Built for teams shipping mission-critical systems.</h2>
            </div>
            <div className="track" id="track"></div>
            <div className="pbar"><i id="pfill"></i></div>
          </div>
        </section>

        <section className="how" id="how">
          <div className="wrap">
            <div className="eyebrow">How it works</div>
            <h2>Four steps from scattered telemetry to a single system.</h2>
            <div className="stack" id="stack"></div>
          </div>
        </section>

        <section className="rev" id="rev">
          <div className="pin">
            <p id="revp" aria-label="Distributed systems are getting more complex every month. The gaps between them are where work quietly breaks. SENTINEL closes those gaps."></p>
          </div>
        </section>

        <section className="stats">
          <div className="wrap">
            <div className="sg" id="sg"></div>
          </div>
        </section>

        <section className="cta" id="cta">
          <div className="wrap">
            <div className="cp2 glass">
              <div className="eyebrow">Free during beta</div>
              <h2>Give your production systems a sentient guardrail.</h2>
              <div className="cta-row">
                <button type="button" className="btn solid" onClick={onLaunchConsole}>Launch Console →</button>
                <a className="btn ghost glass" href="#how">Talk to us</a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer id="docs">
        <div className="wrap">
          <div className="fg">
            <div>
              <a className="logo" href="#top"><i></i>SENTINEL</a>
              <p>The autonomous developer intelligence layer for distributed systems: telemetry, incident graphs, and root-cause ranking routed with a full audit trail.</p>
              <span className="pill glass"><span className="dot"></span>All systems normal</span>
            </div>
            <div>
              <h4>Product</h4>
              <ul>
                <li><a href="#how">How it works</a></li>
                <li><a href="#platform">Platform</a></li>
                <li><a href="#">Pricing</a></li>
                <li><a href="#">Changelog</a></li>
                <li><a href="#">Roadmap</a></li>
              </ul>
            </div>
            <div>
              <h4>Developers</h4>
              <ul>
                <li><a href="#docs">Docs</a></li>
                <li><a href="#">API reference</a></li>
                <li><a href="#">SDKs</a></li>
                <li><a href="#">MCP server</a></li>
                <li><a href="#">Status</a></li>
              </ul>
            </div>
            <div>
              <h4>Company</h4>
              <ul>
                <li><a href="#">About</a></li>
                <li><a href="#customers">Customers</a></li>
                <li><a href="#">Careers</a></li>
                <li><a href="#">Blog</a></li>
                <li><a href="#">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4>Legal</h4>
              <ul>
                <li><a href="#">Privacy</a></li>
                <li><a href="#">Terms</a></li>
                <li><a href="#">Security</a></li>
                <li><a href="#">DPA</a></li>
              </ul>
            </div>
          </div>

          <svg className="wm" viewBox="0 0 1200 230" aria-hidden="true">
            <defs>
              <linearGradient id="wg">
                <stop offset="0" stopColor="#ff7a3d" />
                <stop offset=".5" stopColor="#a58bff" />
                <stop offset="1" stopColor="#ff7a3d" />
              </linearGradient>
            </defs>
            <text className="wb" x="50%" y="180" textAnchor="middle">sentinel</text>
            <text className="wd" x="50%" y="180" textAnchor="middle">sentinel</text>
            <text className="wr" x="50%" y="180" textAnchor="middle">sentinel</text>
          </svg>

          <div className="fb">
            <span>© 2026 SENTINEL Systems. All rights reserved.</span>
            <div>
              <a href="#">X</a>
              <a href="https://github.com/adityasystems99/SENTINEL">GitHub</a>
              <a href="#">LinkedIn</a>
              <a href="#">Discord</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
