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
  FileCode,
} from 'lucide-react';
import StartProjectButton from './StartProjectButton';
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

    // Validate .zip extension
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
      // Call inspection API to transition project to inspected state
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
    <div style={{ maxWidth: '840px', margin: '40px auto', padding: '0 20px' }}>
      {/* Title & Vision Statement */}
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h1
          style={{
            fontSize: '2.6rem',
            fontWeight: '900',
            letterSpacing: '-0.03em',
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #F3F0E8 0%, #73D9F5 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          SENTINEL
        </h1>
        <p
          style={{
            fontSize: '1.15rem',
            fontStyle: 'italic',
            color: 'var(--accent)',
            marginBottom: '14px',
            fontWeight: '500',
          }}
        >
          Understand your code. Investigate failures. Validate improvements.
        </p>
        <p
          style={{
            fontSize: '0.95rem',
            color: 'var(--text-secondary)',
            maxWidth: '620px',
            margin: '0 auto',
            lineHeight: '1.6',
          }}
        >
          Bring your project into SENTINEL to inspect its implementation, investigate application
          behavior, identify potential risks, and validate fixes.
        </p>
      </div>

      {/* Upload ZIP Container */}
      <div className="glass-panel" style={{ padding: '32px', marginBottom: '32px' }}>
        {/* Dropzone Area */}
        {uploadStatus === 'idle' && (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${dragOver ? 'var(--accent)' : 'rgba(255, 255, 255, 0.15)'}`,
              borderRadius: 'var(--radius-lg)',
              padding: '48px 24px',
              textAlign: 'center',
              background: dragOver ? 'rgba(115, 217, 245, 0.08)' : 'rgba(0, 0, 0, 0.25)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <Upload size={44} color={dragOver ? 'var(--accent)' : 'var(--text-muted)'} style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700', marginBottom: '6px' }}>
              Drag & Drop Project ZIP
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Select a project archive (.zip) to begin automated developer intelligence
            </p>
            <button
              type="button"
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
                padding: '8px 18px',
                borderRadius: '8px',
                fontSize: '0.84rem',
                fontWeight: '600',
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
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '16px 20px',
                marginBottom: '20px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div
                  style={{
                    background: uploadStatus === 'ready' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(115, 217, 245, 0.15)',
                    padding: '10px',
                    borderRadius: '10px',
                    color: uploadStatus === 'ready' ? '#10b981' : 'var(--accent)',
                  }}
                >
                  <FileArchive size={24} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                      {selectedFile?.name}
                    </strong>
                    <span className={`badge ${uploadStatus === 'ready' ? 'badge-low' : uploadStatus === 'failed' ? 'badge-critical' : 'badge-high'}`}>
                      {uploadStatus}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
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
                      background: 'var(--accent)',
                      color: '#080D18',
                      border: 'none',
                      padding: '7px 16px',
                      borderRadius: '8px',
                      fontSize: '0.82rem',
                      fontWeight: '700',
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
                    padding: '7px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <RefreshCw size={13} /> Replace
                </button>

                <button
                  type="button"
                  onClick={handleRemove}
                  title="Remove file"
                  style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    color: '#f87171',
                    padding: '7px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <Trash2 size={13} /> Remove
                </button>
              </div>
            </div>

            {/* Real Progress Bar */}
            {uploadStatus === 'uploading' && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  <span>Uploading archive to isolated workspace...</span>
                  <strong>{uploadProgress}%</strong>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '999px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${uploadProgress}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #ff6ea9, #ffd36e, #6ef0ff)',
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
                  borderRadius: '10px',
                  padding: '14px 18px',
                  marginBottom: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#34d399' }}>
                  <CheckCircle2 size={18} />
                  <span style={{ fontSize: '0.88rem', fontWeight: '600' }}>
                    Project archive successfully validated and isolated in workspace
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '14px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  <span>Files: <strong>{projectMetadata.file_count}</strong></span>
                  <span>Stack: <strong>{projectMetadata.detected_frameworks?.join(', ') || 'Generic'}</strong></span>
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
              fontSize: '0.85rem',
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

        {/* Start Project CTA Button */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px' }}>
          <StartProjectButton
            onClick={handleStartProject}
            disabled={uploadStatus !== 'ready' || !projectMetadata}
            loading={isStarting}
          />
        </div>
      </div>

      {/* Or Select Existing Project */}
      {existingProjects.length > 0 && (
        <div className="glass-panel" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <FolderOpen size={18} color="var(--accent)" />
            <h4 style={{ fontSize: '0.95rem', fontWeight: '700' }}>
              Or Open Previously Ingested Project ({existingProjects.length})
            </h4>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
            {existingProjects.map((p) => (
              <div
                key={p.project_id}
                onClick={() => onSelectExisting(p.project_id)}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <strong style={{ fontSize: '0.86rem', color: 'var(--text-primary)' }}>{p.name}</strong>
                  <span className="badge badge-low">{p.status}</span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {p.file_count} files · {p.detected_frameworks?.join(', ') || 'Generic'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
