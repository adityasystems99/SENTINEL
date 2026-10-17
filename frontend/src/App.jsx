import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import DemoControls from './components/DemoControls';
import IncidentList from './components/IncidentList';
import RootCauseCard from './components/RootCauseCard';
import IncidentGraph from './components/IncidentGraph';
import Timeline from './components/Timeline';
import { fetchHealth, fetchIncidents, fetchIncidentDetail, triggerIncidentAnalysis } from './api/client';

export default function App() {
  const [health, setHealth] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const [hData, incData] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchIncidents().catch(() => []),
      ]);
      setHealth(hData);
      setIncidents(incData || []);

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
