import React, { useState, useRef } from 'react';
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
  Github,
} from 'lucide-react';
import StartProjectButton from './StartProjectButton';
import ParticleVortex from './ParticleVortex';
import SentinelLogo from './SentinelLogo';
import { uploadProjectArchive, inspectProject } from '../api/client';

export default function ProjectEntry({
  existingProjects = [],
  onProjectReady,
  onSelectExisting,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | selected | uploading | ready | failed
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);
  const [projectMetadata, setProjectMetadata] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelection = (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.zip')) {
      setErrorMessage('Invalid file type: Please select a valid .zip project archive');
      setUploadStatus('failed');
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setErrorMessage('Archive file is empty (0 bytes)');
      setUploadStatus('failed');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setErrorMessage(null);
    setUploadStatus('selected');
    setUploadProgress(0);
    setProjectMetadata(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadStatus('uploading');
      setUploadProgress(0);
      setErrorMessage(null);

      const metadata = await uploadProjectArchive(
        selectedFile,
        selectedFile.name.replace(/\.zip$/i, ''),
        (percent) => {
          setUploadProgress(percent);
        }
      );

      setProjectMetadata(metadata);
      setUploadStatus('ready');
    } catch (err) {
      setErrorMessage(err.message || 'Failed to upload and validate project archive');
      setUploadStatus('failed');
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setErrorMessage(null);
    setUploadProgress(0);
    setProjectMetadata(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleStartProject = async () => {
    if (!projectMetadata || isStarting) return;

    try {
      setIsStarting(true);
      const inspectionResult = await inspectProject(projectMetadata.project_id);
      onProjectReady(projectMetadata, inspectionResult);
    } catch (err) {
      setErrorMessage(`Inspection failed: ${err.message}`);
      setUploadStatus('failed');
    } finally {
      setIsStarting(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        width: '100%',
        overflowX: 'hidden',
        padding: '40px 20px 80px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {/* Signature 3D Particle Vortex Background (Reference 1) */}
      <ParticleVortex mode="hero" />

      {/* Main Glassmorphic Container */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          width: '100%',
          maxWidth: '880px',
        }}
      >
        {/* Brand & Vision Header */}
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          {/* GitHub Repository Link */}
          <div style={{ marginBottom: '14px' }}>
            <a
              href="https://github.com/adityasystems99/SENTINEL"
              target="_blank"
              rel="noopener noreferrer"
              title="View SENTINEL Repository on GitHub"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 14px',
                borderRadius: '999px',
                background: 'rgba(0, 242, 254, 0.08)',
                border: '1px solid rgba(0, 242, 254, 0.25)',
                fontSize: '0.74rem',
                fontWeight: '700',
                color: 'var(--accent-cyan)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontFamily: 'var(--font-mono)',
                textDecoration: 'none',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-cyan)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(0, 242, 254, 0.25)')}
            >
              <Github size={13} />
              <span>github.com/adityasystems99/SENTINEL</span>
            </a>
          </div>

          {/* Geometric Intelligence Mark */}
          <div style={{ display: 'inline-flex', marginBottom: '18px' }}>
            <SentinelLogo size={60} glowing={true} animated={true} />
          </div>

          <h1
            style={{
              fontSize: 'clamp(2.4rem, 5vw, 3.4rem)',
              fontWeight: '900',
              letterSpacing: '-0.035em',
              lineHeight: '1.15',
              marginBottom: '12px',
              background: 'linear-gradient(135deg, #ffffff 0%, #73D9F5 45%, #c084fc 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textShadow: '0 0 40px rgba(0, 242, 254, 0.25)',
            }}
          >
            <span
              style={{
                display: 'block',
                fontSize: 'clamp(1.1rem, 2.5vw, 1.4rem)',
                fontWeight: '800',
                letterSpacing: '0.25em',
                textTransform: 'uppercase',
                color: 'var(--accent-cyan)',
                fontFamily: 'var(--font-mono)',
                marginBottom: '6px',
              }}
            >
              SENTINEL
            </span>
            See beyond the code.
          </h1>

          <p
            style={{
              fontSize: 'clamp(1rem, 2.2vw, 1.25rem)',
              color: 'var(--accent)',
              fontWeight: '500',
              marginBottom: '8px',
              letterSpacing: '-0.01em',
            }}
          >
            Understand the system. Expose the risk. Trace the impact.
          </p>

          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              maxWidth: '640px',
              margin: '0 auto 10px',
              fontStyle: 'italic',
            }}
          >
            Understand your code. Investigate failures. Validate improvements.
          </p>

          <p
            style={{
              fontSize: '0.9rem',
              color: 'var(--text-muted)',
              maxWidth: '640px',
              margin: '0 auto',
              lineHeight: '1.6',
            }}
          >
            Ingest your codebase into SENTINEL to extract AST topologies, analyze microservice
            blast radiuses, perform AST-level compliance audits, and rank incident root causes.
          </p>
        </div>

        {/* Upload ZIP Container */}
        <div
          className="glass-panel glass-panel-glow"
          style={{
            padding: '36px',
            marginBottom: '32px',
            border: '1px solid rgba(0, 242, 254, 0.2)',
          }}
        >
          {/* Dropzone Area */}
          {uploadStatus === 'idle' && (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${dragOver ? 'var(--accent-cyan)' : 'rgba(115, 217, 245, 0.25)'}`,
                borderRadius: 'var(--radius-lg)',
                padding: '52px 24px',
                textAlign: 'center',
                background: dragOver ? 'rgba(0, 242, 254, 0.08)' : 'rgba(6, 9, 19, 0.45)',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                boxShadow: dragOver ? '0 0 30px rgba(0, 242, 254, 0.15)' : 'none',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  background: 'rgba(0, 242, 254, 0.08)',
                  border: '1px solid rgba(0, 242, 254, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                }}
              >
                <Upload
                  size={32}
                  color={dragOver ? 'var(--accent-cyan)' : 'var(--accent)'}
                />
              </div>

              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', marginBottom: '8px' }}>
                Drag & Drop Project ZIP
              </h3>
              <p
                style={{
                  fontSize: '0.86rem',
                  color: 'var(--text-secondary)',
                  marginBottom: '20px',
                  maxWidth: '440px',
                  margin: '0 auto 20px',
                }}
              >
                Select or drop a project archive (.zip) to begin automated developer intelligence
              </p>
              <button
                type="button"
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(115, 217, 245, 0.3)',
                  color: 'var(--text-primary)',
                  padding: '9px 22px',
                  borderRadius: '10px',
                  fontSize: '0.86rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                Browse Files
              </button>
            </div>
          )}

          {/* Selected or Uploading or Ready State */}
          {uploadStatus !== 'idle' && (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'rgba(6, 9, 19, 0.6)',
                  border: '1px solid rgba(115, 217, 245, 0.2)',
                  borderRadius: '14px',
                  padding: '18px 22px',
                  marginBottom: '20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div
                    style={{
                      background:
                        uploadStatus === 'ready'
                          ? 'rgba(16, 185, 129, 0.15)'
                          : 'rgba(0, 242, 254, 0.12)',
                      padding: '12px',
                      borderRadius: '12px',
                      color: uploadStatus === 'ready' ? '#10b981' : 'var(--accent-cyan)',
                      border: `1px solid ${uploadStatus === 'ready' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(0, 242, 254, 0.25)'}`,
                    }}
                  >
                    <FileArchive size={26} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <strong style={{ fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                        {selectedFile?.name}
                      </strong>
                      <span
                        className={`badge ${
                          uploadStatus === 'ready'
                            ? 'badge-low'
                            : uploadStatus === 'failed'
                            ? 'badge-critical'
                            : 'badge-high'
                        }`}
                      >
                        {uploadStatus}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {selectedFile ? formatFileSize(selectedFile.size) : ''}
                    </span>
                  </div>
                </div>

                {/* Action buttons: Replace or Remove */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {uploadStatus === 'selected' && (
                    <button
                      type="button"
                      onClick={handleUpload}
                      style={{
                        background: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)',
                        color: '#060913',
                        border: 'none',
                        padding: '8px 18px',
                        borderRadius: '9px',
                        fontSize: '0.84rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                        boxShadow: '0 0 15px rgba(0, 242, 254, 0.3)',
                      }}
                    >
                      Upload & Validate
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    title="Replace file"
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border)',
                      color: 'var(--text-secondary)',
                      padding: '8px 14px',
                      borderRadius: '9px',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      cursor: 'pointer',
                    }}
                  >
                    <RefreshCw size={14} /> Replace
                  </button>

                  <button
                    type="button"
                    onClick={handleRemove}
                    title="Remove file"
                    style={{
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#f87171',
                      padding: '8px 14px',
                      borderRadius: '9px',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      cursor: 'pointer',
                    }}
                  >
                    <Trash2 size={14} /> Remove
                  </button>
                </div>
              </div>

              {/* Real Progress Bar */}
              {uploadStatus === 'uploading' && (
                <div style={{ marginBottom: '22px' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      marginBottom: '8px',
                    }}
                  >
                    <span>Uploading archive to isolated workspace...</span>
                    <strong>{uploadProgress}%</strong>
                  </div>
                  <div
                    style={{
                      width: '100%',
                      height: '6px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '999px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${uploadProgress}%`,
                        height: '100%',
                        background: 'linear-gradient(90deg, #8b5cf6, #00f2fe)',
                        boxShadow: '0 0 10px rgba(0, 242, 254, 0.5)',
                        transition: 'width 0.2s ease',
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Ready State Info */}
              {uploadStatus === 'ready' && projectMetadata && (
                <div
                  style={{
                    background: 'rgba(16, 185, 129, 0.08)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    borderRadius: '12px',
                    padding: '16px 20px',
                    marginBottom: '22px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#34d399' }}>
                    <CheckCircle2 size={20} />
                    <span style={{ fontSize: '0.9rem', fontWeight: '600' }}>
                      Project archive successfully validated and isolated in workspace
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                    <span>
                      Files: <strong style={{ color: '#fff' }}>{projectMetadata.file_count}</strong>
                    </span>
                    <span>
                      Stack:{' '}
                      <strong style={{ color: 'var(--accent-cyan)' }}>
                        {projectMetadata.detected_frameworks?.join(', ') || 'Generic'}
                      </strong>
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileSelection(e.target.files[0])}
          />

          {/* Error Banner */}
          {errorMessage && (
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '10px',
                padding: '12px 16px',
                color: '#f87171',
                fontSize: '0.86rem',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginBottom: '20px',
              }}
            >
              <AlertCircle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Primary Action: START A PROJECT */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '28px' }}>
            <StartProjectButton
              onClick={handleStartProject}
              disabled={uploadStatus !== 'ready' || !projectMetadata}
              loading={isStarting}
              label="START A PROJECT"
            />
          </div>
        </div>

        {/* Or Select Existing Project */}
        {existingProjects.length > 0 && (
          <div className="glass-panel" style={{ padding: '24px 28px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
                flexWrap: 'wrap',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FolderOpen size={19} color="var(--accent-cyan)" />
                <h4 style={{ fontSize: '0.98rem', fontWeight: '700' }}>
                  Previously Ingested Projects ({existingProjects.length})
                </h4>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Select a project to reopen its workspaces
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '14px',
              }}
            >
              {existingProjects.map((p) => (
                <div
                  key={p.project_id}
                  onClick={() => onSelectExisting(p.project_id)}
                  style={{
                    background: 'rgba(6, 9, 19, 0.5)',
                    border: '1px solid rgba(115, 217, 245, 0.15)',
                    borderRadius: '12px',
                    padding: '14px 16px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-cyan)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(115, 217, 245, 0.15)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '6px',
                    }}
                  >
                    <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      {p.name}
                    </strong>
                    <span className="badge badge-low">{p.status}</span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {p.file_count} files · {p.detected_frameworks?.join(', ') || 'Generic'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Operational Status Pill Footer */}
        <div
          style={{
            marginTop: '32px',
            textAlign: 'center',
            fontSize: '0.76rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <span className="pulse-dot" style={{ color: '#10b981', background: '#10b981' }} />
            SENTINEL ENGINE: OPERATIONAL
          </span>
          <span>·</span>
          <span>AST TOPOLOGY SCANNER READY</span>
          <span>·</span>
          <span>NETWORKX CAUSAL GRAPH V1.0</span>
          <span>·</span>
          <a
            href="https://github.com/adityasystems99/SENTINEL"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--accent-cyan)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: '600',
            }}
          >
            <Github size={12} />
            <span>GITHUB</span>
          </a>
        </div>
      </div>
    </div>
  );
}
