import { useEffect, useMemo, useState, useCallback } from 'react'
import { RotateCcw } from 'lucide-react'
import Header from './Header.jsx'
import RiskSummary from './RiskSummary.jsx'
import MapView from './MapView.jsx'
import CorridorPanel from './CorridorPanel.jsx'
import SimulationPanel from './SimulationPanel.jsx'
import RecommendationPanel from './RecommendationPanel.jsx'
import AlertsPanel from './AlertsPanel.jsx'
import IncidentModal from './IncidentModal.jsx'
import {
  fetchRoads,
  fetchNetworkOverview,
  fetchIncidents,
  fetchFacilities,
  fetchVehicles,
  fetchDistricts,
  simulateFailure,
  fetchRecommendation,
} from '../services/api.js'

export default function Dashboard() {
  const [roads, setRoads] = useState([])
  const [overview, setOverview] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [facilities, setFacilities] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [districts, setDistricts] = useState([])

  const [activeNav, setActiveNav] = useState('overview')
  const [selectedRoadId, setSelectedRoadId] = useState(null)
  const [simulationStatus, setSimulationStatus] = useState('idle') // idle | loading | done
  const [simulationResult, setSimulationResult] = useState(null)
  const [showAlternative, setShowAlternative] = useState(false)
  const [recommendation, setRecommendation] = useState(null)
  const [selectedIncident, setSelectedIncident] = useState(null)

  useEffect(() => {
    fetchRoads().then(setRoads)
    fetchNetworkOverview().then(setOverview)
    fetchIncidents().then(setIncidents)
    fetchFacilities().then(setFacilities)
    fetchVehicles().then(setVehicles)
    fetchDistricts().then(setDistricts)
  }, [])

  const selectedRoad = useMemo(() => roads.find((r) => r.id === selectedRoadId) ?? null, [roads, selectedRoadId])

  const showIncidents = activeNav !== 'vehicles'
  const showVehicles = activeNav === 'vehicles' || activeNav === 'overview'

  const handleSelectRoad = useCallback((road) => {
    setSelectedRoadId(road.id)
    setSimulationStatus('idle')
    setSimulationResult(null)
    setShowAlternative(false)
    setRecommendation(null)
  }, [])

  const handleSimulate = useCallback(async (road) => {
    setSimulationStatus('loading')
    setShowAlternative(false)
    setRecommendation(null)
    const result = await simulateFailure(road)
    setSimulationResult(result)
    setSimulationStatus('done')
  }, [])

  const handleViewAlternative = useCallback(async () => {
    if (!simulationResult) return
    setShowAlternative(true)
    const rec = await fetchRecommendation(simulationResult)
    setRecommendation(rec)
  }, [simulationResult])

  const handleReset = useCallback(() => {
    setSelectedRoadId(null)
    setSimulationStatus('idle')
    setSimulationResult(null)
    setShowAlternative(false)
    setRecommendation(null)
    setSelectedIncident(null)
    setActiveNav('overview')
  }, [])

  const handleIncidentSelect = useCallback((incident) => setSelectedIncident(incident), [])

  const handleViewImpact = useCallback(
    (incident) => {
      setSelectedIncident(null)
      const road = roads.find((r) => r.id === incident.relatedRoad)
      if (road) {
        handleSelectRoad(road)
        handleSimulate(road)
      }
    },
    [roads, handleSelectRoad, handleSimulate]
  )

  if (!overview) {
    return (
      <div className="flex h-screen items-center justify-center bg-void">
        <span className="font-mono text-sm text-text-secondary">Loading dashboard&hellip;</span>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col bg-void">
      <Header alertCount={incidents.length} />

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[240px_1fr_320px]">
        <div className="hidden lg:block lg:min-h-0">
          <RiskSummary overview={overview} districts={districts} activeNav={activeNav} onNavChange={setActiveNav} />
        </div>

        <main className="relative flex min-h-0 min-w-0 flex-col gap-3 p-3">
          <div className="flex items-center justify-between">
            <div className="text-[11px] text-text-secondary">
              Showing <span className="font-medium text-text-primary">{roads.length}</span> tracked corridors across the
              North Eastern Region
            </div>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 rounded-md border border-border-strong bg-panel px-2.5 py-1.5 text-[11px] font-medium text-text-secondary hover:border-accent/40 hover:text-accent-strong"
            >
              <RotateCcw size={12} />
              RESET SIMULATION
            </button>
          </div>

          <div className="min-h-[360px] flex-1">
            <MapView
              roads={roads}
              facilities={facilities}
              incidents={incidents}
              vehicles={vehicles}
              selectedRoadId={selectedRoadId}
              onSelectRoad={handleSelectRoad}
              simulationResult={simulationStatus === 'done' ? simulationResult : null}
              showAlternative={showAlternative}
              showIncidents={showIncidents}
              showVehicles={showVehicles}
              onIncidentSelect={handleIncidentSelect}
            />
          </div>

          <AlertsPanel incidents={incidents} overview={overview} activeRecommendation={recommendation} />
        </main>

        <div className="flex min-h-0 flex-col gap-3 overflow-y-auto border-t border-border bg-void p-3 lg:border-l lg:border-t-0">
          <CorridorPanel road={selectedRoad} onSimulate={handleSimulate} simulationStatus={simulationStatus} />
          <SimulationPanel
            status={simulationStatus}
            result={simulationResult}
            onViewAlternative={handleViewAlternative}
            alternativeShown={showAlternative}
          />
          <RecommendationPanel recommendation={recommendation} />
        </div>
      </div>

      <IncidentModal incident={selectedIncident} onClose={() => setSelectedIncident(null)} onViewImpact={handleViewImpact} />
    </div>
  )
}
