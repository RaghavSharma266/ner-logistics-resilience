import { mockIncidents } from '../data/mockIncidents.js'
import { mockVehicles } from '../data/mockVehicles.js'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

async function getJson(url) {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// -------------------- DISTRICTS --------------------
// Backend: GET /districts -> [{ id, name, state, terrainClass, coords,
// connectivityStatus, dataStatus }, ...]
// Frontend (DistrictStatusPanel.jsx) only reads id, name, state,
// connectivityStatus, so the backend shape is used as-is with no mapping.

export async function fetchDistricts() {
  const data = await getJson(`${API_BASE_URL}/districts`)
  return Array.isArray(data) ? data : data.districts ?? []
}

// -------------------- ROADS --------------------
// Backend: GET /roads -> [{ id, name, originDistrict, destinationDistrict,
// distanceKm, roadType, officialRef, riskScore, riskLevel, status, path,
// dataStatus, geometryQuality }, ...]
//
// Frontend needs (CorridorPanel.jsx / MapView.jsx / mockRoads.js shape):
// id, name, originDistrict, destinationDistrict, riskLevel, riskScore,
// status, path, criticality, cargo, destination, lengthKm.
//
// distanceKm -> lengthKm is a straight rename (same real value).
// criticality, cargo, and destination (the named drop-off point/facility)
// have NO equivalent field anywhere in the backend response, so they are
// NOT invented here — they come through as undefined. CorridorPanel will
// render those two rows blank for now; nothing crashes, but be aware this
// is a genuine backend data gap, not a bug in this file.

function mapRoad(road) {
  return {
    ...road,
    lengthKm: road.distanceKm,
  }
}

export async function fetchRoads() {
  const data = await getJson(`${API_BASE_URL}/roads`)
  const roads = Array.isArray(data) ? data : data.roads ?? []
  return roads.map(mapRoad)
}

// -------------------- FACILITIES --------------------
// Backend: GET /facilities -> [{ id, name, type, district, coords,
// critical, dataStatus }, ...]
// Frontend (MapView.jsx) only reads id, type, name, coords, critical, all
// present as-is. The extra `district` field is simply ignored.

export async function fetchFacilities() {
  const data = await getJson(`${API_BASE_URL}/facilities`)
  return Array.isArray(data) ? data : data.facilities ?? []
}

// -------------------- SIMULATION --------------------
// Backend: POST /simulate-failure
// Request body field is `road_id` (snake_case) — confirmed directly from
// backend/models/schemas.py (SimulationRequest.road_id, no camelCase alias
// configured anywhere) and from backend/tests/test_backend.py, which posts
// {"road_id": "R102"} / {"road_id": "R101"} / {"road_id": "R108"} in every
// passing test. The originally-specified `{ "roadId": "R101" }` body does
// NOT match the real backend contract and would be rejected by FastAPI's
// request validation (422) — this file follows the actual code instead,
// per "the actual backend response is the source of truth."
//
// road.id is used to build the request, matching the same `id` field the
// frontend already keys roads by everywhere else (selection, map lines,
// CorridorPanel).
//
// Backend response (SimulationResponse) has NO `roadId`, `status`,
// `supplyRoutesDisrupted`, `priority`, `reason`, `reachableConfirmed`,
// `affectedLocations`, or `affectedDistrict` fields — despite those being
// listed in the integration brief. The REAL fields, per
// backend/models/schemas.py and backend/services/orchestrator.py, are:
// failedRoad, roadName, originDistrict, destinationDistrict, source,
// destination, riskScore, riskLevel, destinationReachable, originalRoute,
// alternateRoute, originalDistanceKm, alternateDistanceKm,
// alternativeRoute, alternativeRouteName, additionalDistanceKm,
// accessibilityBefore, accessibilityAfter, travelDelayMin,
// locationsAffected, criticalFacilitiesAffected, recommendation.
//
// The mapping below translates every field it honestly can, and leaves the
// rest as safe, clearly-flagged defaults rather than inventing data:
//   - roadId            <- failedRoad (same concept, backend's real name)
//   - status             = 'UNAVAILABLE' (constant, not per-instance data —
//                          this endpoint only ever describes the failed
//                          road's own now-unavailable state)
//   - reachableConfirmed <- destinationReachable (same concept, renamed)
//   - priority           <- riskLevel (backend has no dedicated priority
//                          field; riskLevel — HIGH/MEDIUM/LOW — is the
//                          closest real signal, so it's reused rather than
//                          fabricating a separate value)
//   - reason             <- recommendation text (backend has no separate
//                          "reason" field; recommendation is the backend's
//                          own real explanatory sentence)
//   - supplyRoutesDisrupted -> left undefined; no backend field exists for
//                          this at all. Renders blank in the Stat card
//                          rather than showing a made-up number.
//   - affectedLocations  = [] (backend has no named-locations data;
//                          SimulationPanel.jsx calls
//                          result.affectedLocations.map(...) with no
//                          guard, so this MUST be an array or the UI
//                          crashes — an empty array is honest, not
//                          fabricated, and keeps the UI usable.)
//   - affectedDistrict   = null (backend's District model has no
//                          `population` field, but SimulationPanel.jsx
//                          unconditionally calls
//                          result.affectedDistrict.population.toLocaleString(...)
//                          whenever affectedDistrict is truthy. Since that
//                          would either crash or require fabricating a
//                          population number, this stays null — the panel
//                          already has an `{result.affectedDistrict && ...}`
//                          guard, so it just skips that block cleanly.)
// Everything else below (accessibilityBefore/After, travelDelayMin,
// locationsAffected, criticalFacilitiesAffected, alternativeRoute,
// alternativeRouteName, recommendation) is a direct, same-name passthrough
// of real backend values.

export async function simulateFailure(road) {
  const roadId = road.id

  const response = await fetch(`${API_BASE_URL}/simulate-failure`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ road_id: roadId }),
  })

  if (!response.ok) {
    let detail = ''
    try {
      const errorBody = await response.json()
      detail = errorBody.detail ?? JSON.stringify(errorBody)
    } catch {
      detail = await response.text()
    }
    throw new Error(`Simulation failed: ${response.status} ${detail}`)
  }

  const data = await response.json()

  return {
    roadId: data.failedRoad,
    status: 'UNAVAILABLE',

    supplyRoutesDisrupted: undefined,
    accessibilityBefore: data.accessibilityBefore,
    accessibilityAfter: data.accessibilityAfter,
    travelDelayMin: data.travelDelayMin,
    locationsAffected: data.locationsAffected,
    criticalFacilitiesAffected: data.criticalFacilitiesAffected,

    alternativeRoute: data.alternativeRoute,
    alternativeRouteName: data.alternativeRouteName,

    recommendation: data.recommendation,
    priority: data.riskLevel,
    reason: data.recommendation,
    reachableConfirmed: data.destinationReachable,

    affectedLocations: [],
    affectedDistrict: null,
  }
}

// -------------------- MOCK FEATURES --------------------
// No backend endpoint exists for incidents or vehicles. Left exactly as
// before, on mock data.

export async function fetchIncidents() {
  return mockIncidents
}

export async function fetchVehicles() {
  return mockVehicles
}

// -------------------- NETWORK OVERVIEW --------------------
// No dedicated backend endpoint. Risk/corridor counts are derived from the
// real GET /roads data (same as before). activeIncidents/activeVehicles
// now reflect the actual mock arrays' real lengths — the same numbers
// already shown elsewhere in the dashboard (e.g. the Header alert badge
// uses incidents.length from this same mock data) — instead of being
// hardcoded to 0, which was inconsistent with the rest of the UI.
// affectedCorridors stays derived from live road status: at baseline
// (before any simulation), GET /roads always reports every road as
// OPERATIONAL, so this is honestly 0 until a real per-corridor "affected"
// signal exists on the backend.

export async function fetchNetworkOverview() {
  const roads = await fetchRoads()

  const highRisk = roads.filter(
    (road) => String(road.riskLevel ?? '').toUpperCase() === 'HIGH'
  ).length

  const mediumRisk = roads.filter(
    (road) => String(road.riskLevel ?? '').toUpperCase() === 'MEDIUM'
  ).length

  const lowRisk = roads.filter(
    (road) => String(road.riskLevel ?? '').toUpperCase() === 'LOW'
  ).length

  const operationalCorridors = roads.filter(
    (road) => String(road.status ?? '').toUpperCase() !== 'UNAVAILABLE'
  ).length

  return {
    highRisk,
    mediumRisk,
    lowRisk,
    monitoredCorridors: roads.length,
    operationalCorridors,
    activeIncidents: mockIncidents.length,
    activeVehicles: mockVehicles.length,
    affectedCorridors: roads.length - operationalCorridors,
  }
}

// -------------------- RECOMMENDATION --------------------
// Pure repackaging of fields already produced by simulateFailure() above;
// unchanged.

export async function fetchRecommendation(simulationResult) {
  return {
    action: simulationResult.recommendation,
    priority: simulationResult.priority,
    reason: simulationResult.reason,
    delayMin: simulationResult.travelDelayMin,
    reachableConfirmed: simulationResult.reachableConfirmed,
  }
}
