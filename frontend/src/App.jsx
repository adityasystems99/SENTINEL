import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ProjectWorkspaceBar from './components/ProjectWorkspaceBar';
import DemoControls from './components/DemoControls';
import IncidentList from './components/IncidentList';
import RootCauseCard from './components/RootCauseCard';
import IncidentGraph from './components/IncidentGraph';
import Timeline from './components/Timeline';
import {
  fetchHealth,
  fetchIncidents,
  fetchIncidentDetail,
  triggerIncidentAnalysis,
  fetchProjects,
  fetchProjectMetadata,
} from './api/client';

export default function App() {
  const [health, setHealth] = useState(null);
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeProject, setActiveProject] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const [hData, incData, projList] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchIncidents().catch(() => []),
        fetchProjects().catch(() => []),
      ]);
      setHealth(hData);
      setIncidents(incData || []);
      setProjects(projList || []);

      // If active project is selected, refresh its metadata
      if (projList && projList.length > 0) {
        const currentId = activeProjectId || projList[0].project_id;
        setActiveProjectId(currentId);
        const meta = await fetchProjectMetadata(currentId).catch(() => null);
        setActiveProject(meta);
      } else {
        setActiveProject(null);
        setActiveProjectId(null);
      }

      // If no incident selected or selected not in list, auto-select latest
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
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedIncidentId, activeProjectId]);

  const handleSelectProject = async (id) => {
    setActiveProjectId(id);
    try {
      const meta = await fetchProjectMetadata(id);
      setActiveProject(meta);
    } catch (err) {
      console.error('Error fetching project detail:', err);
    }
  };

  const handleProjectUploaded = async (newProjectId) => {
    setActiveProjectId(newProjectId);
    await loadData();
  };

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
      await loadData();
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

  useEffect(() => {
    loadData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      <Header
        health={health}
        onRefresh={loadData}
        isRefreshing={isRefreshing}
        activeIncidentCount={incidents.length}
      />

      {/* Project Ingestion & Workspaces Bar */}
      <ProjectWorkspaceBar
        projects={projects}
        activeProject={activeProject}
        onSelectProject={handleSelectProject}
        onProjectUploaded={handleProjectUploaded}
      />

      {/* Telemetry & Chaos Harness */}
      <DemoControls onActionComplete={loadData} />

      <main style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Left Column: Incidents List */}
        <div>
          <IncidentList
            incidents={incidents}
            selectedId={selectedIncidentId}
            onSelect={handleSelectIncident}
            onAnalyze={handleManualAnalyze}
            isAnalyzing={isAnalyzing}
          />
        </div>

        {/* Right Column: Deep Incident Investigation */}
        <div>
          <RootCauseCard incident={selectedIncident} />
          {selectedIncident && (
            <>
              <IncidentGraph
                nodes={selectedIncident.nodes}
                edges={selectedIncident.edges}
              />
              <Timeline nodes={selectedIncident.nodes} />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
