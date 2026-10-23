import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Upload,
  FileArchive,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Trash2,
  FolderOpen,
  ShieldCheck,
  Cpu,
  Layers,
  ArrowRight,
  Terminal,
  Activity,
} from 'lucide-react';
import { uploadProjectArchive, inspectProject } from '../api/client';

/* ------------------------------------------------------------------ */
/*  Static content                                                     */
/* ------------------------------------------------------------------ */

const CAPABILITIES = [
  {
    icon: Cpu,
    title: 'Compatibility Engine',
    question: 'Can I use it?',
    body: 'Tech stack inspection, telemetry hooks and framework readiness.',
  },
  {
    icon: ShieldCheck,
    title: 'Spec vs. Reality Audit',
    question: 'Have I built what I promised?',
    body: 'AST compliance comparison between specifications and implemented code.',
  },
  {
    icon: Activity,
    title: 'Live Incident RCA',
    question: 'Why is my application failing?',
    body: 'Graph-based root cause analysis across errors, traces and metrics.',
  },
  {
    icon: Layers,
    title: 'Dependency & Blast Radar',
    question: 'What else could break?',
    body: 'Service topologies and cascading microservice impact analysis.',
  },
  {
    icon: Terminal,
    title: 'Controlled Fix Validation',
    question: 'Does my fix actually work?',
    body: 'Before/after telemetry deltas and regression validation.',
  },
];

const STAGES = ['idle', 'selected', 'uploading', 'ready', 'inspecting'];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value >= 100 || i === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[i]}`;
}

function deriveProjectName(filename) {
  return filename
    .replace(/\.zip$/i, '')
    .replace(/[_]+/g, '-')
    .trim();
}

function validateFile(file) {
  if (!file) return 'No file was selected.';
  if (!/\.zip$/i.test(file.name)) {
    return `"${file.name}" is not a .zip archive. Compress the project folder into a .zip and try again.`;
  }
  if (file.size <= 0) {
    return `"${file.name}" is empty (0 bytes). Select an archive that contains your project files.`;
  }
  return null;
}

function errorMessage(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (err?.message) return err.message;
  return fallback;
}

function projectLabel(p) {
  return p?.name || p?.project_name || p?.title || p?.project_id || 'Untitled project';
}

function projectDate(p) {
  const raw = p?.created_at || p?.uploaded_at || p?.updated_at;
  if (!raw) return null;
  const d = new Date(raw);
  return Number.isNaN(d.getTime())
    ? null
    : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function ProjectEntry({
  existingProjects = [],
  onProjectReady,
  onSelectExisting,
}) {
  const [stage, setStage] = useState('idle');
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [progress, setProgress] = useState(0);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null); // { message, retry: 'upload' | 'inspect' | 'file' }
  const [dragging, setDragging] = useState(false);

  const inputRef = useRef(null);
  const dragDepth = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const busy = stage === 'uploading' || stage === 'inspecting';

  /* ---------------------------- file intake ---------------------------- */

  const acceptFile = useCallback((candidate) => {
    const problem = validateFile(candidate);
    if (problem) {
      setError({ message: problem, retry: 'file' });
      return;
    }
    setError(null);
    setFile(candidate);
    setProjectName(deriveProjectName(candidate.name));
    setMetadata(null);
    setProgress(0);
    setStage('selected');
  }, []);

  const onBrowse = () => {
    if (!busy) inputRef.current?.click();
  };

  const onInputChange = (e) => {
    const picked = e.target.files?.[0];
    if (picked) acceptFile(picked);
    e.target.value = '';
  };

  const onDragEnter = (e) => {
    e.preventDefault();
    if (busy || stage !== 'idle') return;
    dragDepth.current += 1;
    setDragging(true);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
  };

  const onDragLeave = (e) => {
    e.preventDefault();
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    dragDepth.current = 0;
    setDragging(false);
    if (busy || stage !== 'idle') return;
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped) acceptFile(dropped);
  };

  const reset = () => {
    if (busy) return;
    setStage('idle');
    setFile(null);
    setProjectName('');
    setProgress(0);
    setMetadata(null);
    setError(null);
  };

  /* ------------------------------- upload ------------------------------ */

  const runUpload = useCallback(async () => {
    if (!file) return;
    const name = projectName.trim() || deriveProjectName(file.name);
    setError(null);
    setProgress(0);
    setStage('uploading');
    try {
      const result = await uploadProjectArchive(file, name, (pct) => {
        if (mounted.current) setProgress(Math.max(0, Math.min(100, Math.round(pct))));
      });
      if (!mounted.current) return;
      const meta = result?.project ?? result;
      if (!meta?.project_id) {
        throw new Error('The server did not return a project ID for this archive.');
      }
      setMetadata(meta);
      setProgress(100);
      setStage('ready');
    } catch (err) {
      if (!mounted.current) return;
      setError({ message: errorMessage(err, 'Upload failed.'), retry: 'upload' });
      setStage('selected');
    }
  }, [file, projectName]);

  /* ------------------------------ inspect ------------------------------ */

  const runInspect = useCallback(async () => {
    if (!metadata?.project_id) return;
    setError(null);
    setStage('inspecting');
    try {
      const inspection = await inspectProject(metadata.project_id);
      if (!mounted.current) return;
      onProjectReady?.(metadata, inspection);
    } catch (err) {
      if (!mounted.current) return;
      setError({ message: errorMessage(err, 'Project inspection failed.'), retry: 'inspect' });
      setStage('ready');
    }
  }, [metadata, onProjectReady]);

  const retry = () => {
    if (!error) return;
    if (error.retry === 'upload') runUpload();
    else if (error.retry === 'inspect') runInspect();
    else {
      setError(null);
      inputRef.current?.click();
    }
  };

  /* ------------------------------ derived ------------------------------ */

  const stageIndex = STAGES.indexOf(stage);
  const statusText = useMemo(() => {
    switch (stage) {
      case 'selected':
        return 'Archive selected';
      case 'uploading':
        return `Uploading ${progress}%`;
      case 'ready':
        return 'Ready to inspect';
      case 'inspecting':
        return 'Inspecting project';
      default:
        return 'Awaiting archive';
    }
  }, [stage, progress]);

  /* ------------------------------ render ------------------------------- */

  return (
    <div className="pe-root">
      <style>{CSS}</style>

      <div className="pe-bg" aria-hidden="true">
        <div className="pe-mesh" />
        <div className="pe-grid" />
        <div className="pe-vignette" />
      </div>

      <header className="pe-topbar">
        <div className="pe-brand">
          <span className="pe-brand-mark" aria-hidden="true" />
          <span className="pe-brand-name">SENTINEL</span>
        </div>
        <div className="pe-status" role="status" aria-live="polite">
          <span className={`pe-dot pe-dot-${stage}`} aria-hidden="true" />
          <span className="pe-mono">{statusText}</span>
        </div>
      </header>

      <main className="pe-main">
        <section className="pe-hero">
          <h1 className="pe-title">See beyond the code.</h1>
          <p className="pe-lede">
            Upload your project archive and SENTINEL maps its structure, checks it against its
            specifications, and prepares the evidence you need to investigate failures and validate
            fixes.
          </p>
        </section>

        <div className="pe-columns">
          {/* ---------------------- Ingest column ---------------------- */}
          <section className="pe-ingest" aria-label="Project ingestion">
            <input
              ref={inputRef}
              type="file"
              accept=".zip,application/zip,application/x-zip-compressed"
              className="pe-hidden"
              onChange={onInputChange}
              tabIndex={-1}
            />

            <div className="pe-panel">
              <ol className="pe-steps" aria-label="Ingestion progress">
                {['Select', 'Upload', 'Inspect'].map((label, i) => {
                  const active =
                    (i === 0 && (stage === 'idle' || stage === 'selected')) ||
                    (i === 1 && stage === 'uploading') ||
                    (i === 2 && (stage === 'ready' || stage === 'inspecting'));
                  const done =
                    (i === 0 && stageIndex >= 2) ||
                    (i === 1 && stageIndex >= 3) ||
                    (i === 2 && false);
                  return (
                    <li
                      key={label}
                      className={`pe-step ${active ? 'is-active' : ''} ${done ? 'is-done' : ''}`}
                    >
                      <span className="pe-step-icon">
                        {done ? <CheckCircle2 size={14} /> : <span className="pe-step-dot" />}
                      </span>
                      {label}
                    </li>
                  );
                })}
              </ol>

              {stage === 'idle' && (
                <div
                  className={`pe-drop ${dragging ? 'is-dragging' : ''}`}
                  onDragEnter={onDragEnter}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  onClick={onBrowse}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onBrowse();
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  aria-label="Drop a project .zip archive here or press Enter to browse"
                >
                  <div className="pe-drop-icon">
                    <Upload size={22} strokeWidth={1.75} />
                  </div>
                  <div className="pe-drop-title">
                    {dragging ? 'Release to select archive' : 'Drop a project .zip here'}
                  </div>
                  <div className="pe-drop-sub">
                    Include source, configuration and any specification documents.
                  </div>
                  <button
                    type="button"
                    className="pe-btn pe-btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      onBrowse();
                    }}
                  >
                    <FolderOpen size={15} />
                    Browse files
                  </button>
                </div>
              )}

              {stage !== 'idle' && file && (
                <div className="pe-file" key={stage === 'selected' ? 'sel' : 'rest'}>
                  <div className="pe-file-row">
                    <div className="pe-file-icon">
                      <FileArchive size={20} strokeWidth={1.75} />
                    </div>
                    <div className="pe-file-meta">
                      <div className="pe-file-name" title={file.name}>
                        {file.name}
                      </div>
                      <div className="pe-file-sub pe-mono">
                        {formatBytes(file.size)}
                        <span className="pe-sep" />
                        {stage === 'selected' && 'not uploaded'}
                        {stage === 'uploading' && 'uploading'}
                        {(stage === 'ready' || stage === 'inspecting') && (
                          <span className="pe-ok">status: ready</span>
                        )}
                      </div>
                    </div>
                    {!busy && (
                      <button
                        type="button"
                        className="pe-icon-btn"
                        onClick={reset}
                        aria-label="Remove archive"
                        title="Remove archive"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>

                  {stage === 'selected' && (
                    <div className="pe-field">
                      <label htmlFor="pe-name" className="pe-label">
                        Project name
                      </label>
                      <input
                        id="pe-name"
                        className="pe-input"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        placeholder={deriveProjectName(file.name)}
                        maxLength={80}
                        spellCheck={false}
                        autoComplete="off"
                      />
                    </div>
                  )}

                  {(stage === 'uploading' || stage === 'ready' || stage === 'inspecting') && (
                    <div className="pe-progress-wrap">
                      <div
                        className="pe-progress"
                        role="progressbar"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={progress}
                        aria-label="Upload progress"
                      >
                        <div
                          className={`pe-progress-bar ${stage === 'uploading' ? 'is-live' : ''}`}
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <div className="pe-progress-meta pe-mono">
                        <span>{stage === 'uploading' ? 'Transferring archive' : 'Transfer complete'}</span>
                        <span>{progress}%</span>
                      </div>
                    </div>
                  )}

                  {metadata && (stage === 'ready' || stage === 'inspecting') && (
                    <dl className="pe-kv pe-mono">
                      <div>
                        <dt>project_id</dt>
                        <dd title={metadata.project_id}>{metadata.project_id}</dd>
                      </div>
                      <div>
                        <dt>name</dt>
                        <dd>{projectLabel(metadata)}</dd>
                      </div>
                    </dl>
                  )}

                  <div className="pe-actions">
                    {stage === 'selected' && (
                      <>
                        <button type="button" className="pe-btn pe-btn-ghost" onClick={reset}>
                          Choose another
                        </button>
                        <button
                          type="button"
                          className="pe-btn pe-btn-primary"
                          onClick={runUpload}
                          disabled={!projectName.trim()}
                        >
                          <Upload size={15} />
                          Upload archive
                        </button>
                      </>
                    )}
                    {stage === 'uploading' && (
                      <button type="button" className="pe-btn pe-btn-primary" disabled>
                        <RefreshCw size={15} className="pe-spin" />
                        Uploading
                      </button>
                    )}
                    {(stage === 'ready' || stage === 'inspecting') && (
                      <button
                        type="button"
                        className="pe-btn pe-btn-primary pe-btn-wide"
                        onClick={runInspect}
                        disabled={stage === 'inspecting'}
                      >
                        {stage === 'inspecting' ? (
                          <>
                            <RefreshCw size={15} className="pe-spin" />
                            Inspecting project
                          </>
                        ) : (
                          <>
                            Start project
                            <ArrowRight size={15} />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              )}

              {error && (
                <div className="pe-error" role="alert">
                  <AlertCircle size={16} className="pe-error-icon" />
                  <div className="pe-error-body">
                    <div className="pe-error-title">
                      {error.retry === 'file'
                        ? 'This file can’t be used'
                        : error.retry === 'upload'
                        ? 'Upload failed'
                        : 'Inspection failed'}
                    </div>
                    <div className="pe-error-text">{error.message}</div>
                  </div>
                  <button type="button" className="pe-btn pe-btn-small" onClick={retry}>
                    <RefreshCw size={13} />
                    {error.retry === 'file' ? 'Choose file' : 'Retry'}
                  </button>
                </div>
              )}
            </div>

            {existingProjects.length > 0 && (
              <div className="pe-existing">
                <div className="pe-section-head">
                  <h2>Continue with an existing project</h2>
                  <span className="pe-mono pe-muted">{existingProjects.length}</span>
                </div>
                <ul className="pe-list">
                  {existingProjects.map((p) => {
                    const date = projectDate(p);
                    return (
                      <li key={p.project_id}>
                        <button
                          type="button"
                          className="pe-row"
                          onClick={() => onSelectExisting?.(p.project_id)}
                          disabled={busy}
                        >
                          <span className="pe-row-icon">
                            <FolderOpen size={16} strokeWidth={1.75} />
                          </span>
                          <span className="pe-row-main">
                            <span className="pe-row-name">{projectLabel(p)}</span>
                            <span className="pe-row-sub pe-mono">
                              {p.project_id}
                              {date ? <span className="pe-sep" /> : null}
                              {date}
                            </span>
                          </span>
                          <ArrowRight size={15} className="pe-row-arrow" />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </section>

          {/* ------------------- Capabilities column ------------------- */}
          <aside className="pe-caps" aria-label="What SENTINEL provides">
            <div className="pe-section-head">
              <h2>What you get after ingestion</h2>
            </div>
            <ul className="pe-cap-list">
              {CAPABILITIES.map(({ icon: Icon, title, question, body }) => (
                <li key={title} className="pe-cap">
                  <span className="pe-cap-icon">
                    <Icon size={17} strokeWidth={1.75} />
                  </span>
                  <div className="pe-cap-text">
                    <div className="pe-cap-title">{title}</div>
                    <div className="pe-cap-q">{question}</div>
                    <div className="pe-cap-body">{body}</div>
                  </div>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      </main>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Scoped styles                                                      */
/* ------------------------------------------------------------------ */

const CSS = `
.pe-root {
  --bg-0: #090d16;
  --bg-1: #0d1117;
  --panel: rgba(17, 23, 34, 0.78);
  --panel-solid: #111722;
  --line: rgba(148, 163, 184, 0.14);
  --line-strong: rgba(148, 163, 184, 0.26);
  --text: #e6edf7;
  --text-2: #9aa7ba;
  --text-3: #66738a;
  --accent: #4cc9f0;
  --accent-soft: rgba(76, 201, 240, 0.12);
  --accent-line: rgba(76, 201, 240, 0.45);
  --ok: #3ddc97;
  --danger: #f87171;
  --font-sans: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "JetBrains Mono", "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  position: relative;
  min-height: 100vh;
  width: 100%;
  background: var(--bg-0);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.5;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}
.pe-root *, .pe-root *::before, .pe-root *::after { box-sizing: border-box; }
.pe-hidden { display: none; }
.pe-mono { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0; }
.pe-muted { color: var(--text-3); }

/* background */
.pe-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
.pe-mesh {
  position: absolute; inset: 0;
  background:
    radial-gradient(900px 520px at 12% -8%, rgba(56, 119, 190, 0.16), transparent 60%),
    radial-gradient(760px 480px at 92% 8%, rgba(76, 201, 240, 0.08), transparent 62%),
    radial-gradient(900px 600px at 50% 120%, rgba(60, 80, 140, 0.14), transparent 60%),
    linear-gradient(180deg, var(--bg-0), var(--bg-1));
}
.pe-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(to right, rgba(148, 163, 184, 0.045) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148, 163, 184, 0.045) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 30%, #000 30%, transparent 85%);
  -webkit-mask-image: radial-gradient(ellipse 80% 70% at 50% 30%, #000 30%, transparent 85%);
}
.pe-vignette {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at center, transparent 55%, rgba(5, 8, 14, 0.55) 100%);
}

/* top bar */
.pe-topbar {
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: space-between;
  max-width: 1160px; margin: 0 auto; padding: 22px 28px 0;
}
.pe-brand { display: flex; align-items: center; gap: 10px; }
.pe-brand-mark {
  width: 18px; height: 18px; border-radius: 5px;
  border: 1.5px solid var(--accent);
  background: linear-gradient(135deg, var(--accent-soft), transparent);
  position: relative;
}
.pe-brand-mark::after {
  content: ""; position: absolute; inset: 4px; border-radius: 2px; background: var(--accent);
  opacity: 0.85;
}
.pe-brand-name { font-weight: 600; letter-spacing: 0.14em; font-size: 13px; color: var(--text); }
.pe-status {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 11px; border-radius: 999px;
  border: 1px solid var(--line); background: rgba(13, 17, 23, 0.6);
  color: var(--text-2);
}
.pe-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-3); transition: background 0.25s, box-shadow 0.25s; }
.pe-dot-selected { background: var(--accent); }
.pe-dot-uploading, .pe-dot-inspecting { background: var(--accent); box-shadow: 0 0 0 0 var(--accent-line); animation: pe-pulse 1.6s ease-out infinite; }
.pe-dot-ready { background: var(--ok); box-shadow: 0 0 8px rgba(61, 220, 151, 0.55); }

/* layout */
.pe-main { position: relative; z-index: 1; max-width: 1160px; margin: 0 auto; padding: 56px 28px 72px; }
.pe-hero { max-width: 680px; margin-bottom: 40px; animation: pe-rise 0.6s ease both; }
.pe-title {
  margin: 0 0 14px; font-size: clamp(34px, 5vw, 52px); line-height: 1.05;
  font-weight: 650; letter-spacing: -0.025em; color: var(--text);
}
.pe-lede { margin: 0; color: var(--text-2); font-size: 16px; line-height: 1.6; max-width: 60ch; }
.pe-columns { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 36px; align-items: start; }

/* panel */
.pe-panel {
  position: relative;
  background: var(--panel); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--line); border-radius: 12px; padding: 18px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03) inset, 0 18px 40px -24px rgba(0, 0, 0, 0.7);
}

/* steps */
.pe-steps { list-style: none; margin: 0 0 16px; padding: 0 2px; display: flex; gap: 22px; }
.pe-step { display: flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-3); transition: color 0.25s; }
.pe-step-icon { display: inline-flex; width: 14px; height: 14px; align-items: center; justify-content: center; }
.pe-step-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: 0.55; }
.pe-step.is-active { color: var(--text); }
.pe-step.is-active .pe-step-dot { background: var(--accent); opacity: 1; }
.pe-step.is-done { color: var(--ok); }

/* dropzone */
.pe-drop {
  position: relative; display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: 44px 24px 38px; border-radius: 10px; cursor: pointer;
  border: 1px dashed var(--line-strong); background: rgba(9, 13, 22, 0.55);
  transition: border-color 0.2s, background 0.2s, box-shadow 0.25s;
  outline: none;
}
.pe-drop:hover { border-color: rgba(148, 163, 184, 0.4); background: rgba(13, 18, 28, 0.7); }
.pe-drop:focus-visible { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.pe-drop.is-dragging {
  border-style: solid; border-color: var(--accent);
  background: linear-gradient(180deg, rgba(76, 201, 240, 0.08), rgba(76, 201, 240, 0.02));
  box-shadow: 0 0 0 4px var(--accent-soft), 0 0 32px -6px var(--accent-line);
}
.pe-drop-icon {
  width: 46px; height: 46px; border-radius: 10px; display: grid; place-items: center; margin-bottom: 16px;
  color: var(--accent); background: var(--accent-soft); border: 1px solid rgba(76, 201, 240, 0.25);
  transition: transform 0.25s;
}
.pe-drop.is-dragging .pe-drop-icon { transform: translateY(-3px); }
.pe-drop-title { font-size: 15.5px; font-weight: 600; margin-bottom: 4px; }
.pe-drop-sub { color: var(--text-2); font-size: 13px; margin-bottom: 20px; max-width: 38ch; }

/* file card */
.pe-file { animation: pe-fade 0.3s ease both; }
.pe-file-row { display: flex; align-items: center; gap: 12px; }
.pe-file-icon {
  width: 40px; height: 40px; border-radius: 9px; display: grid; place-items: center; flex: none;
  color: var(--accent); background: var(--accent-soft); border: 1px solid rgba(76, 201, 240, 0.22);
}
.pe-file-meta { min-width: 0; flex: 1; }
.pe-file-name { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pe-file-sub { color: var(--text-3); display: flex; align-items: center; gap: 0; margin-top: 2px; }
.pe-sep { display: inline-block; width: 3px; height: 3px; border-radius: 50%; background: var(--text-3); margin: 0 8px; vertical-align: middle; }
.pe-ok { color: var(--ok); }
.pe-icon-btn {
  display: grid; place-items: center; width: 32px; height: 32px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; background: transparent; color: var(--text-3); transition: all 0.15s;
}
.pe-icon-btn:hover { color: var(--danger); background: rgba(248, 113, 113, 0.08); border-color: rgba(248, 113, 113, 0.2); }
.pe-icon-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.pe-field { margin-top: 18px; }
.pe-label { display: block; font-size: 12px; color: var(--text-2); margin-bottom: 6px; }
.pe-input {
  width: 100%; padding: 9px 12px; border-radius: 8px; color: var(--text);
  background: rgba(9, 13, 22, 0.8); border: 1px solid var(--line-strong);
  font-family: var(--font-mono); font-size: 13px; transition: border-color 0.15s, box-shadow 0.15s;
}
.pe-input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

/* progress */
.pe-progress-wrap { margin-top: 18px; }
.pe-progress { height: 6px; border-radius: 999px; background: rgba(148, 163, 184, 0.14); overflow: hidden; }
.pe-progress-bar {
  height: 100%; border-radius: inherit; width: 0;
  background: linear-gradient(90deg, #2f8fd0, var(--accent));
  transition: width 0.25s ease, background 0.3s;
  position: relative; overflow: hidden;
}
.pe-progress-bar.is-live::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transform: translateX(-100%); animation: pe-sheen 1.4s linear infinite;
}
.pe-progress-meta { display: flex; justify-content: space-between; color: var(--text-3); margin-top: 7px; }
.pe-progress-bar:not(.is-live) { background: linear-gradient(90deg, #2bb88a, var(--ok)); }

.pe-kv { margin: 16px 0 0; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--line); background: rgba(9, 13, 22, 0.55); display: grid; gap: 6px; }
.pe-kv > div { display: flex; gap: 14px; }
.pe-kv dt { color: var(--text-3); width: 82px; flex: none; }
.pe-kv dd { margin: 0; color: var(--text); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.pe-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

/* buttons */
.pe-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 9px 16px; border-radius: 8px; font: inherit; font-weight: 550; font-size: 13.5px;
  cursor: pointer; border: 1px solid transparent; transition: background 0.15s, border-color 0.15s, transform 0.1s, opacity 0.15s;
}
.pe-btn:active:not(:disabled) { transform: translateY(1px); }
.pe-btn:disabled { cursor: not-allowed; opacity: 0.55; }
.pe-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.pe-btn-primary { background: var(--accent); color: #04121b; }
.pe-btn-primary:hover:not(:disabled) { background: #6bd5f5; }
.pe-btn-wide { min-width: 180px; }
.pe-btn-secondary { background: rgba(148, 163, 184, 0.08); border-color: var(--line-strong); color: var(--text); }
.pe-btn-secondary:hover { background: rgba(148, 163, 184, 0.14); }
.pe-btn-ghost { background: transparent; color: var(--text-2); }
.pe-btn-ghost:hover { color: var(--text); background: rgba(148, 163, 184, 0.08); }
.pe-btn-small { padding: 6px 11px; font-size: 12.5px; background: rgba(248, 113, 113, 0.1); border-color: rgba(248, 113, 113, 0.3); color: #fecaca; flex: none; }
.pe-btn-small:hover { background: rgba(248, 113, 113, 0.18); }

/* error */
.pe-error {
  display: flex; align-items: flex-start; gap: 12px; margin-top: 16px; padding: 12px 14px; border-radius: 9px;
  background: rgba(248, 113, 113, 0.07); border: 1px solid rgba(248, 113, 113, 0.28);
  animation: pe-fade 0.25s ease both;
}
.pe-error-icon { color: var(--danger); margin-top: 2px; flex: none; }
.pe-error-body { flex: 1; min-width: 0; }
.pe-error-title { font-weight: 600; font-size: 13px; color: #fecaca; }
.pe-error-text { color: var(--text-2); font-size: 12.5px; margin-top: 2px; word-break: break-word; }

/* sections */
.pe-section-head { display: flex; align-items: baseline; justify-content: space-between; margin: 0 0 12px; }
.pe-section-head h2 { margin: 0; font-size: 13px; font-weight: 600; color: var(--text-2); letter-spacing: 0.01em; }

/* existing projects */
.pe-existing { margin-top: 28px; }
.pe-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.pe-row {
  width: 100%; display: flex; align-items: center; gap: 12px; padding: 11px 14px; text-align: left; cursor: pointer;
  background: rgba(17, 23, 34, 0.6); border: 1px solid var(--line); border-radius: 10px; color: var(--text);
  font: inherit; transition: border-color 0.15s, background 0.15s;
}
.pe-row:hover:not(:disabled) { border-color: var(--accent-line); background: rgba(20, 28, 42, 0.85); }
.pe-row:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.pe-row:disabled { opacity: 0.5; cursor: not-allowed; }
.pe-row-icon { color: var(--text-2); display: grid; place-items: center; flex: none; }
.pe-row-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.pe-row-name { font-weight: 550; font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pe-row-sub { color: var(--text-3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pe-row-arrow { color: var(--text-3); flex: none; transition: transform 0.15s, color 0.15s; }
.pe-row:hover:not(:disabled) .pe-row-arrow { color: var(--accent); transform: translateX(2px); }

/* capabilities */
.pe-caps { padding-top: 4px; }
.pe-cap-list { list-style: none; margin: 0; padding: 0; border-left: 1px solid var(--line); }
.pe-cap { display: flex; gap: 14px; padding: 14px 0 14px 18px; position: relative; }
.pe-cap + .pe-cap { border-top: 1px solid rgba(148, 163, 184, 0.07); }
.pe-cap-icon {
  width: 32px; height: 32px; border-radius: 8px; display: grid; place-items: center; flex: none;
  color: var(--accent); background: var(--accent-soft); border: 1px solid rgba(76, 201, 240, 0.2);
}
.pe-cap-title { font-weight: 600; font-size: 14px; }
.pe-cap-q { color: var(--accent); font-size: 12.5px; margin-top: 1px; }
.pe-cap-body { color: var(--text-2); font-size: 13px; margin-top: 4px; max-width: 46ch; }

/* motion */
@keyframes pe-rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes pe-fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes pe-sheen { to { transform: translateX(100%); } }
@keyframes pe-pulse {
  0% { box-shadow: 0 0 0 0 rgba(76, 201, 240, 0.5); }
  100% { box-shadow: 0 0 0 8px rgba(76, 201, 240, 0); }
}
.pe-spin { animation: pe-spin 0.9s linear infinite; }
@keyframes pe-spin { to { transform: rotate(360deg); } }

@media (max-width: 920px) {
  .pe-columns { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .pe-main { padding-top: 36px; }
}
@media (max-width: 520px) {
  .pe-topbar, .pe-main { padding-left: 16px; padding-right: 16px; }
  .pe-steps { gap: 14px; }
  .pe-actions { flex-direction: column-reverse; }
  .pe-actions .pe-btn { width: 100%; }
}
@media (prefers-reduced-motion: reduce) {
  .pe-root *, .pe-root *::before, .pe-root *::after { animation: none !important; transition: none !important; }
}
`;
