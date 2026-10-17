import React, { useState, useRef } from 'react';
import {
  FolderArchive,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ShieldCheck,
  Compass,
  FileCheck2,
  Radio,
  Share2,
  RotateCcw,
} from 'lucide-react';
import { uploadProjectArchive, inspectProject } from '../api/client';

export default function ProjectWorkspaceBar({
  projects = [],
  activeProject,
  onSelectProject,
  onProjectUploaded,
}) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;
    try {
      setIsUploading(true);
      setUploadError(null);
      const metadata = await uploadProjectArchive(file, file.name.replace(/\.zip$/i, ''));
      // Automatically inspect project upon upload
      try {
        await inspectProject(metadata.project_id);
      } catch (e) {
        console.warn('Auto inspect notice:', e);
      }
      setShowUploadModal(false);
      onProjectUploaded(metadata.project_id);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const capabilityIcons = {
    compatibility: <Compass size={14} />,
    promise_audit: <FileCheck2 size={14} />,
    live_incident: <Radio size={14} />,
    dependency_radar: <Share2 size={14} />,
    fix_validation: <RotateCcw size={14} />,
  };

  return (
    <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        {/* Project Selector & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'rgba(59, 130, 246, 0.15)',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            color: '#60a5fa'
          }}>
            <FolderArchive size={20} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: '700' }}>
                Active Project Workspace
              </span>
              {activeProject && (
                <span className={`badge ${activeProject.status === 'ready' ? 'badge-low' : activeProject.status === 'failed' ? 'badge-critical' : 'badge-high'}`}>
                  {activeProject.status}
                </span>
              )}
            </div>

            {projects.length > 0 ? (
              <select
                value={activeProject?.project_id || ''}
                onChange={(e) => onSelectProject(e.target.value)}
                style={{
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  marginTop: '4px',
                  cursor: 'pointer',
                }}
              >
                {projects.map((p) => (
                  <option key={p.project_id} value={p.project_id}>
                    {p.name} ({p.project_id}) — {p.detected_frameworks?.join(', ') || 'Generic'}
                  </option>
                ))}
              </select>
            ) : (
              <div style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
                No project uploaded yet (Demo Service Active)
              </div>
            )}
          </div>
        </div>

        {/* Action Button: Ingest Project Archive */}
        <button
          onClick={() => setShowUploadModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            border: 'none',
            color: '#ffffff',
            padding: '8px 16px',
            borderRadius: '8px',
            fontSize: '0.82rem',
            fontWeight: '600',
            boxShadow: '0 2px 10px rgba(37, 99, 235, 0.35)',
          }}
        >
          <Upload size={15} />
          Ingest Project ZIP
        </button>
      </div>

      {/* Active Project Details & 5 Capability Workspaces Preview */}
      {activeProject && (
        <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <FileCode size={14} color="#60a5fa" />
              <span>Files: <strong>{activeProject.file_count || 0}</strong></span>
            </div>
            <span>•</span>
            <div>
              Size: <strong>{((activeProject.extracted_size_bytes || 0) / 1024).toFixed(1)} KB</strong>
            </div>
            <span>•</span>
            <div>
              Stack: <strong>{activeProject.detected_frameworks?.join(', ') || 'Generic'}</strong>
            </div>
            {activeProject.excluded_items_count > 0 && (
              <>
                <span>•</span>
                <div style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={14} />
                  <span><strong>{activeProject.excluded_items_count}</strong> secrets/deps safely excluded</span>
                </div>
              </>
            )}
          </div>

          {/* 5 Workspaces Readiness Pills */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <span className="badge badge-low" title="Feature 1: Integration Readiness">
              {capabilityIcons.compatibility} Can I use it?
            </span>
            <span className="badge badge-low" title="Feature 2: Promise vs Reality Audit">
              {capabilityIcons.promise_audit} Promised?
            </span>
            <span className="badge badge-low" title="Feature 3: Live Incident RCA">
              {capabilityIcons.live_incident} Why failing?
            </span>
            <span className="badge badge-low" title="Feature 4: Dependency Radar">
              {capabilityIcons.dependency_radar} What breaks?
            </span>
            <span className="badge badge-low" title="Feature 5: Fix Validation">
              {capabilityIcons.fix_validation} Fix works?
            </span>
          </div>
        </div>
      )}

      {/* Upload ZIP Modal */}
      {showUploadModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
          onClick={() => !isUploading && setShowUploadModal(false)}
        >
          <div
            className="glass-panel"
            style={{
              width: '100%',
              maxWidth: '520px',
              padding: '28px',
              background: '#0d131f',
              border: '1px solid rgba(255, 255, 255, 0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FolderArchive size={22} color="#3b82f6" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Ingest Project Archive</h3>
              </div>
              <button
                onClick={() => !isUploading && setShowUploadModal(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1rem' }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Upload your application codebase as a standard <code>.zip</code> file. SENTINEL validates and isolates the project in a sandboxed workspace.
            </p>

            {/* Drag & Drop Target */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: `2px dashed ${dragOver ? '#3b82f6' : 'rgba(255, 255, 255, 0.15)'}`,
                borderRadius: '12px',
                padding: '36px 20px',
                textAlign: 'center',
                background: dragOver ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0, 0, 0, 0.3)',
                cursor: 'pointer',
                marginBottom: '16px',
                transition: 'all 0.2s ease',
              }}
            >
              <Upload size={36} color={dragOver ? '#60a5fa' : 'var(--text-muted)'} style={{ margin: '0 auto 12px' }} />
              <p style={{ fontSize: '0.88rem', fontWeight: '600', marginBottom: '4px' }}>
                {isUploading ? 'Validating & Extracting Archive...' : 'Drop project .zip here, or click to browse'}
              </p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Max upload: 50 MB · Max uncompressed: 150 MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              />
            </div>

            {/* Security Guarantee Box */}
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '8px', padding: '10px 12px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontSize: '0.78rem', fontWeight: '600', marginBottom: '2px' }}>
                <ShieldCheck size={14} />
                <span>Automated Zero-Trust Security Policy</span>
              </div>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                Secrets (<code>.env</code>, private keys), virtual environments, and <code>node_modules</code> are automatically filtered and never extracted into workspace storage.
              </p>
            </div>

            {uploadError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', padding: '10px 12px', color: '#f87171', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span>{uploadError}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
