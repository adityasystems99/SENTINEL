import React, { useState, useEffect, useCallback } from 'react';
import LoadingScreen from './components/LoadingScreen';
import ProjectEntry from './components/ProjectEntry';
import FiveFeatureDashboard from './components/FiveFeatureDashboard';
import LiveIncidentWorkspace from './components/workspaces/LiveIncidentWorkspace';
import CompatibilityWorkspace from './components/workspaces/CompatibilityWorkspace';
import PromiseAuditWorkspace from './components/workspaces/PromiseAuditWorkspace';
import DependencyRadarWorkspace from './components/workspaces/DependencyRadarWorkspace';
import FixValidationWorkspace from './components/workspaces/FixValidationWorkspace';
import ParticleVortex from './components/ParticleVortex';
import {
  fetchHealth,
  fetchIncidents,
  fetchIncidentDetail,
  triggerIncidentAnalysis,
  fetchProjects,
  fetchProjectMetadata,
} from './api/client';

export default function App() {
  const [currentView, setCurrentView] = useState('loading'); // loading | entry | dashboard | workspace-*
  const [health, setHealth] = useState(null);
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Initial load
  useEffect(() => {
    async function initApp() {
      try {
        const [hData, projList, incList] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchProjects().catch(() => []),
          fetchIncidents().catch(() => []),
        ]);
        setHealth(hData);
        setProjects(projList || []);
        setIncidents(incList || []);

        if (projList && projList.length > 0) {
          const firstProj = await fetchProjectMetadata(projList[0].project_id).catch(() => null);
          setActiveProject(firstProj);
          setCurrentView('dashboard');
        } else {
          setCurrentView('entry');
        }
      } catch (err) {
        console.error('App init error:', err);
        setCurrentView('entry');
      }
    }
    initApp();
  }, []);

  const refreshIncidentData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const incData = await fetchIncidents().catch(() => []);
      setIncidents(incData || []);

      if (incData && incData.length > 0) {
        const targetId = selectedIncidentId || incData[0].incident_id;
        setSelectedIncidentId(targetId);
        const detail = await fetchIncidentDetail(targetId).catch(() => null);
        setSelectedIncident(detail);
      } else {
        setSelectedIncident(null);
        setSelectedIncidentId(null);
      }
    } catch (err) {
      console.error('Failed to refresh incident data:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedIncidentId]);

  const handleSelectIncident = async (id) => {
    setSelectedIncidentId(id);
    try {
      const detail = await fetchIncidentDetail(id);
      setSelectedIncident(detail);
    } catch (err) {
      console.error('Error fetching incident detail:', err);
    }
  };

  const handleManualAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      const newReport = await triggerIncidentAnalysis(300);
      await refreshIncidentData();
      if (newReport) {
        setSelectedIncidentId(newReport.incident_id);
        setSelectedIncident(newReport);
      }
    } catch (err) {
      alert(`Analysis notice: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleProjectReady = (metadata, inspectionResult) => {
    setActiveProject(metadata);
    setProjects((prev) => [metadata, ...prev.filter((p) => p.project_id !== metadata.project_id)]);
    setCurrentView('dashboard');
  };

  const handleSelectExistingProject = async (projectId) => {
    try {
      const meta = await fetchProjectMetadata(projectId);
      setActiveProject(meta);
      setCurrentView('dashboard');
    } catch (err) {
      alert(`Failed to load project: ${err.message}`);
    }
  };

  // 1. Loading Page (features hero particle vortex)
  if (currentView === 'loading') {
    return <LoadingScreen message="Initializing SENTINEL Intelligence Engine & Workspaces..." />;
  }

  // 2. Project Entry Page (features hero particle vortex & START A PROJECT)
  if (currentView === 'entry') {
    return (
      <ProjectEntry
        existingProjects={projects}
        onProjectReady={handleProjectReady}
        onSelectExisting={handleSelectExistingProject}
      />
    );
  }

  // Operational experience wrapper with ambient background particle atmosphere
  return (
    <div style={{ position: 'relative', minHeight: '100vh', width: '100%' }}>
      {/* Subtle ambient 3D particle vortex backdrop */}
      <ParticleVortex mode="ambient" />

      {/* 3. Five-Feature Dashboard */}
      {currentView === 'dashboard' && (
        <FiveFeatureDashboard
          project={activeProject}
          onSelectFeature={(featureId) => setCurrentView(`workspace-${featureId}`)}
          onBackToEntry={() => setCurrentView('entry')}
        />
      )}

      {/* 4. Feature Workspaces */}
      {currentView === 'workspace-incidents' && (
        <LiveIncidentWorkspace
          project={activeProject}
          incidents={incidents}
          selectedIncident={selectedIncident}
          selectedIncidentId={selectedIncidentId}
          onSelectIncident={handleSelectIncident}
          onAnalyze={handleManualAnalyze}
          isAnalyzing={isAnalyzing}
          onRefresh={refreshIncidentData}
          isRefreshing={isRefreshing}
          onBackToDashboard={() => setCurrentView('dashboard')}
        />
      )}

      {currentView === 'workspace-compatibility' && (
        <CompatibilityWorkspace
          project={activeProject}
          onBackToDashboard={() => setCurrentView('dashboard')}
        />
      )}

      {currentView === 'workspace-promise_audit' && (
        <PromiseAuditWorkspace
          project={activeProject}
          onBackToDashboard={() => setCurrentView('dashboard')}
        />
      )}

      {currentView === 'workspace-dependency_radar' && (
        <DependencyRadarWorkspace
          project={activeProject}
          onBackToDashboard={() => setCurrentView('dashboard')}
        />
      )}

      {currentView === 'workspace-fix_validation' && (
        <FixValidationWorkspace
          project={activeProject}
          onBackToDashboard={() => setCurrentView('dashboard')}
        />
      )}
    </div>
  );
}
