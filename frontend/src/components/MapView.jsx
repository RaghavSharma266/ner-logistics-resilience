import { useState, useMemo, useEffect } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, Tooltip, useMap } from 'react-leaflet'
import { AlertTriangle } from 'lucide-react'
import 'leaflet/dist/leaflet.css'
import MapLegend from './MapLegend.jsx'
import IncidentLayer from './IncidentLayer.jsx'
import VehicleLayer from './VehicleLayer.jsx'
import { facilityIcon, warningIcon } from './mapIcons.js'

const NER_CENTER = [25.9, 92.9]
const NER_ZOOM = 6.4

const RISK_COLOR = {
  LOW: '#2fbf6f',
  MEDIUM: '#f0a825',
  HIGH: '#e5484d',
}

function RoadLine({ road, isSelected, isBlocked, isAlternative, onSelect }) {
  if (isBlocked) {
    return (
      <Polyline
        positions={road.path}
        pathOptions={{
          color: '#e5484d',
          weight: isSelected ? 7 : 6,
          opacity: 0.95,
          dashArray: '10 8',
          className: 'route-blocked-line',
        }}
        eventHandlers={{ click: () => onSelect(road) }}
      >
        <Tooltip permanent direction="center" className="road-label road-label-blocked" offset={[0, -4]}>
          {road.id} &middot; BLOCKED
        </Tooltip>
      </Polyline>
    )
  }

  if (isAlternative) {
    return (
      <>
        {/* soft glow underlay so the alternate route reads clearly against the base map */}
        <Polyline positions={road.path} pathOptions={{ color: '#2dd4ee', weight: 16, opacity: 0.16 }} />
        <Polyline
          positions={road.path}
          pathOptions={{
            color: '#2dd4ee',
            weight: 7,
            opacity: 1,
            dashArray: '2 14',
            lineCap: 'round',
            className: 'route-alt-line',
          }}
          eventHandlers={{ click: () => onSelect(road) }}
        >
          <Tooltip permanent direction="center" className="road-label road-label-alt" offset={[0, -4]}>
            {road.id} &middot; ALTERNATE ROUTE
          </Tooltip>
        </Polyline>
      </>
    )
  }

  return (
    <Polyline
      positions={road.path}
      pathOptions={{
        color: RISK_COLOR[road.riskLevel],
        weight: isSelected ? 6 : 4,
        opacity: isSelected ? 1 : 0.85,
      }}
      eventHandlers={{ click: () => onSelect(road) }}
    />
  )
}

// Programmatically pans/zooms the map so the blocked corridor and its
// alternate are both in view the moment they appear — otherwise a route on
// the far side of the map could change without the officer ever noticing.
function MapController({ roads, blockedRoadId, alternativeRoadId }) {
  const map = useMap()

  useEffect(() => {
    if (!blockedRoadId) return
    const blocked = roads.find((r) => r.id === blockedRoadId)
    const alternative = alternativeRoadId ? roads.find((r) => r.id === alternativeRoadId) : null
    const points = [...(blocked?.path ?? []), ...(alternative?.path ?? [])]
    if (points.length) {
      map.flyToBounds(points, { padding: [70, 70], maxZoom: 9.5, duration: 0.9 })
    }
  }, [map, roads, blockedRoadId, alternativeRoadId])

  return null
}

export default function MapView({
  roads,
  facilities,
  incidents,
  vehicles,
  selectedRoadId,
  onSelectRoad,
  simulationResult,
  showAlternative,
  showIncidents,
  showVehicles,
  onIncidentSelect,
}) {
  const [tileError, setTileError] = useState(false)

  const blockedRoadId = simulationResult ? simulationResult.roadId : null
  const alternativeRoadId = showAlternative && simulationResult ? simulationResult.alternativeRoute : null

  const affectedLocations = useMemo(() => {
    if (!showAlternative && !simulationResult) return []
    return simulationResult?.affectedLocations ?? []
  }, [simulationResult, showAlternative])

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border border-border">
      <MapContainer
        center={NER_CENTER}
        zoom={NER_ZOOM}
        minZoom={5.5}
        maxZoom={12}
        className="h-full w-full"
        preferCanvas
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
          eventHandlers={{ tileerror: () => setTileError(true), tileload: () => setTileError(false) }}
        />

        <MapController roads={roads} blockedRoadId={blockedRoadId} alternativeRoadId={alternativeRoadId} />

        {roads.map((road) => (
          <RoadLine
            key={road.id}
            road={road}
            isSelected={road.id === selectedRoadId}
            isBlocked={road.id === blockedRoadId}
            isAlternative={road.id === alternativeRoadId}
            onSelect={onSelectRoad}
          />
        ))}

        {facilities.map((facility) => (
          <Marker key={facility.id} position={facility.coords} icon={facilityIcon(facility.type, facility.critical)}>
            <Popup>
              <div className="p-3">
                <div className="font-mono text-[10px] tracking-wide text-text-tertiary">{facility.type}</div>
                <div className="mt-0.5 text-sm font-semibold text-text-primary">{facility.name}</div>
                {facility.critical && (
                  <div className="mt-1 text-[11px] font-medium text-risk-high">Critical facility</div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {showIncidents && <IncidentLayer incidents={incidents} onSelect={onIncidentSelect} />}
        {showVehicles && <VehicleLayer vehicles={vehicles} />}

        {affectedLocations.map((loc) => (
          <Marker key={loc.name} position={loc.coords} icon={warningIcon()}>
            <Popup>
              <div className="p-3">
                <div className="font-mono text-[10px] tracking-wide text-risk-high">ACCESSIBILITY AFFECTED</div>
                <div className="mt-0.5 text-sm font-semibold text-text-primary">{loc.name}</div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      <MapLegend />

      {tileError && (
        <div className="absolute inset-x-0 top-0 z-[500] flex items-center gap-2 border-b border-risk-medium/40 bg-risk-medium-dim/95 px-4 py-2 text-xs text-risk-medium">
          <AlertTriangle size={14} />
          Map tiles are taking longer than expected to load. The dashboard below continues to function normally.
        </div>
      )}
    </div>
  )
}
